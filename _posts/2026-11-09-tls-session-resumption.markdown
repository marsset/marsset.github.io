---
title: "TLS Session Resumption"
date: 2026-11-09 10:00:00 +0800
categories:
  - system
tags: system networking tls crypto hft low-latency security
excerpt: >
  A deep dive into persistent TLS session management for crypto exchange gateways: the catastrophic cost of cold handshakes during disconnects, TLS 1.3 PSK resumption, 0-RTT Early Data replay risks in trading, AES-NI acceleration, and pre-warmed shadow connections.
---

In quantitative market making and high-frequency trading (HFT) across centralized exchanges (Binance, OKX, Bybit, Gate) and decentralized perps (such as Hyperliquid), firms maintain hundreds of persistent, bidirectional **WebSocket/TLS** connections. 

These streams handle two missions:
1. Ingesting high-throughput public market data (L2 order book deltas, BBO quotes, trade ticks).
2. Transmitting ultra-critical private trading messages (order placement, mass cancels, fill reports).

In production, these connections do not stay alive forever. Exchange load balancers, Cloudflare edge proxies, AWS NLB idle timers, and volatile market bursts trigger frequent TCP connection resets (`RST` or abrupt `FIN`).

When a connection drops while your market-making engine has resting limit orders on the book, **you enter the most dangerous state in electronic trading: toxic exposure**.

If your gateway takes $50$ to $200\,\text{ms}$ to execute a cold TLS renegotiation, latency arbitrageurs will pick off your stale quotes before you can send a cancel command.

This post explores the mechanics of **sub-millisecond TLS session resumption**, TLS 1.3 Pre-Shared Keys ($0\text{-RTT}$), replay attack hazards in financial protocols, and pre-warmed shadow connection pools.

---

## 1. The Cost of a Cold TLS 1.3 Handshake

Why is a standard cold TLS reconnection catastrophic for high-frequency execution?

A full, cold connection requires two sequential network barriers and substantial asymmetric cryptographic computation:

```text
CLIENT (HFT Gateway)                          SERVER (Exchange Cloudflare / AWS NLB)
       │                                                      │
       │ ─── 1. TCP SYN ────────────────────────────────────► │
       │ ◄── 2. TCP SYN-ACK ───────────────────────────────── │  [ 1 RTT: TCP Handshake ]
       │ ─── 3. TCP ACK ────────────────────────────────────► │
       │                                                      │
       │ ─── 4. TLS ClientHello (Key Share: X25519) ────────► │
       │ ◄── 5. TLS ServerHello + EncryptedExtensions ─────── │  [ 2 RTTs: TLS Handshake ]
       │        + Certificate + CertVerify + Finished         │
       │                                                      │
       │ ─── 6. TLS Finished + HTTP WebSocket Upgrade ──────► │
       │ ◄── 7. HTTP 101 Switching Protocols ──────────────── │  [ 3 RTTs: WebSocket Ready ]
```

### The Three Latency Taxations
1. **Network RTT Amplification ($3\times$ Round-Trips):**
   * Even when co-located in Tokyo (`ap-northeast-1`), round-trip times to exchange endpoints range from $1.5$ to $4\,\text{ms}$. Three round-trips require **$4.5$ to $12\,\text{ms}$** of pure wire travel.
   * On cross-region routes (e.g., Tokyo to Dublin or Singapore to US-East), a single RTT is $70$ to $120\,\text{ms}$. A 3-RTT cold reconnect takes **$210$ to $360\,\text{ms}$**—a virtual eternity during which market prices can move tens of basis points.
2. **Asymmetric Cryptographic CPU Penalty:**
   * During a cold handshake, the server must sign the handshake transcript using its private key (ECDSA or RSA), and the client must verify the certificate chain and validate the digital signature.
   * Certificate parsing and signature verification require **$1$ to $3\,\text{ms}$ of pure CPU compute**, burning precious CPU cycles on your network thread.
3. **The Toxic Exposure Window:**
   * While your gateway negotiates the cold handshake, your previously placed bid/ask orders remain live in the exchange order matching engine.
   * If the market moves against you, fast competitors snipe your resting liquidity before your new connection can authenticate and transmit a `cancel_all` command.

---

## 2. TLS Session Resumption: From Tickets to PSK

To bypass the multi-RTT and asymmetric crypto penalties, TLS provides **Session Resumption**.

Instead of performing expensive public-key cryptography and certificate exchange every time, the client and server negotiate a shared secret once, store it, and reuse it for future reconnections.

### Evolution of Session Resumption

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ Legacy TLS 1.2: Session ID (RFC 5246)                                          │
│ • Server caches session state in RAM; client sends 32-byte Session ID.         │
│ • Fatal Flaw: Fails behind multi-server load balancers unless distributed      │
│   Redis/memcached cache is deployed across the exchange edge.                  │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ TLS 1.2 / 1.3: Session Tickets (RFC 5077)                                      │
│ • Server encrypts state into an opaque ticket with a secret key (STEK).        │
│ • Client stores ticket and echoes it back; server decrypts it locally.         │
│ • Eliminates server-side memory caching!                                       │
└──────────────────────────────────────┬─────────────────────────────────────────┘
                                       ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│ Modern TLS 1.3: Pre-Shared Key (PSK) Resumption (RFC 8446)                     │
│ • Unifies session tickets and pre-shared keys into a single PSK mechanism.     │
│ • Handshake dropped to 1-RTT (or 0-RTT with Early Data).                       │
│ • Zero asymmetric certificate verification!                                    │
└────────────────────────────────────────────────────────────────────────────────┘
```

### The 1-RTT PSK Handshake
In standard TLS 1.3 session resumption (1-RTT):
1. During the previous session, the exchange sent a `NewSessionTicket` message containing an encrypted ticket and a ticket nonce.
2. The client derives a **Resumption Pre-Shared Key (PSK)** from the previous session's master secret.
3. Upon reconnection, the client sends `ClientHello` with a `pre_shared_key` extension containing the ticket and a cryptographic binder.
4. The server validates the ticket using its internal key, and both sides immediately derive symmetric traffic keys.
5. **Result:** Asymmetric RSA/ECDSA verification is completely skipped, saving $1$ to $2\,\text{ms}$ of CPU time and cutting handshake time to **$1$ RTT**.

---

## 3. The 0-RTT Holy Grail: Pre-Shared Key Early Data

Can we do better than 1 RTT? **Yes, with TLS 1.3 0-RTT Early Data.**

Under TLS 1.3 $0\text{-RTT}$, the client does not wait for the server to respond to `ClientHello`. Instead, the client encrypts application data immediately using the resumed PSK and transmits it **inside the very first TCP packet**:

```text
CLIENT (HFT Gateway)                          SERVER (Exchange Edge)
       │                                                      │
       │ ─── TCP SYN ───────────────────────────────────────► │
       │ ◄── TCP SYN-ACK ──────────────────────────────────── │  [ 1 RTT: TCP Handshake ]
       │ ─── TCP ACK                                          │
       │     + TLS ClientHello (PSK)                          │
       │     + 0-RTT Early Data (WebSocket Upgrade + Auth) ─► │  [ 0-RTT APPLICATION DATA! ]
       │                                                      │
       │ ◄── TLS ServerHello + EncryptedExtensions            │
       │ ◄── HTTP 101 Switching Protocols ─────────────────── │
```

Using TLS 1.3 $0\text{-RTT}$, your application data (the HTTP WebSocket upgrade and exchange API authentication headers) arrives at the exchange **in the exact same packet as the TLS handshake**.

### The Replay Attack Hazard in Financial Trading
While $0\text{-RTT}$ sounds ideal, it introduces a severe security and financial liability: **Network Replay Attacks**.

Because $0\text{-RTT}$ data is transmitted before the server and client establish fresh ephemeral keys, an attacker or network glitch that captures the packet can **replay the exact same packet to the exchange**:

```text
Attacker intercepts 0-RTT Packet:
[ ClientHello + Encrypted: "POST /api/v3/order { symbol: BTCUSDT, side: BUY, qty: 5 }" ]
       │
Attacker replays packet 10 times:
       └──► Exchange receives and executes 10 separate 5-BTC BUY orders!
```

### How Trading Gateways Safely Use 0-RTT
In high-frequency trading architectures, you must enforce a strict separation between **idempotent** and **non-idempotent** commands:

1. **SAFE for 0-RTT:**
   * **WebSocket Handshake:** `GET /ws/v3 HTTP/1.1` (Upgrading protocol state).
   * **Public Market Data Subscriptions:** `{"method": "SUBSCRIBE", "params": ["btcusdt@depth@100ms"]}`.
   * **Cancel Orders by Client Order ID (Idempotent):** Canceling an already-canceled order simply returns an error without altering exchange account state.
2. **FORBIDDEN for 0-RTT:**
   * **Order Entry (New Orders):** Never transmit new order placements (`POST /order`) inside $0\text{-RTT}$ early data unless the exchange strictly supports cryptographic replay prevention via single-use monotonic nonces.

---

## 4. Hardware Cryptography: AES-NI vs. ChaCha20

Once the TLS session is established, every single packet payload passing through the WebSocket must be symmetrically encrypted and decrypted.

In high-throughput environments processing 500,000 market quotes per second, software-based cryptography introduces massive CPU overhead.

### AES-GCM with AES-NI
Modern x86-64 processors feature dedicated silicon instructions:
* **AES-NI (`aesenc`, `aesdec`):** Hardware instructions for AES block encryption/decryption.
* **PCLMULQDQ (`pclmulqdq`):** Carry-less multiplication instructions accelerating GHASH (Galois Counter Mode authentication).

```c
// Verify CPU supports hardware crypto acceleration
#include <cpuid.h>

void check_crypto_hardware() {
    unsigned int eax, ebx, ecx, edx;
    __cpuid(1, eax, ebx, ecx, edx);
    if (ecx & (1 << 25)) {
        // AES-NI is supported! Hardware encryption enabled.
    }
    if (ecx & (1 << 1)) {
        // PCLMULQDQ supported! Hardware GHASH enabled.
    }
}
```

With hardware AES-NI enabled, symmetric throughput exceeds **$4$ to $8\,\text{GB/s}$ per core**, reducing the latency cost of symmetric encryption to **sub-microsecond scale ($< 300\,\text{ns}$ per frame)**.

### Cipher Selection: AES-128-GCM vs. ChaCha20-Poly1305
* **On Dedicated Hardware Servers:** Always prioritize `TLS_AES_128_GCM_SHA256`. With AES-NI, AES-128 is approximately **$3\times$ faster** than ChaCha20.
* **On Low-End Edge Devices / ARM without Crypto Extensions:** Use `TLS_CHACHA20_POLY1305_SHA256`. ChaCha20 was designed by Daniel J. Bernstein to run efficiently purely on standard CPU arithmetic registers.

---

## 5. Gateway Architecture: Pre-Warmed Shadow Connections

Even with TLS 1.3 $0\text{-RTT}$, reconnecting after an unexpected drop still costs at least **1 RTT of network latency**.

In top-tier quantitative firms, the ultimate solution to reconnection latency is **never having to wait for a reconnection at all**.

### The Hot Standby Connection Pool

Instead of maintaining a single WebSocket connection to Binance or OKX, the trading gateway maintains **$N+1$ active connections** per stream:

```text
                          [ HFT Execution Gateway ]
                                     │
           ┌─────────────────────────┴─────────────────────────┐
           ▼                                                   ▼
[ Primary Active Session ]                          [ Pre-Warmed Shadow Session ]
• Actively streaming quotes                         • TLS Handshake ALREADY complete!
• Ready for immediate send                          • WebSocket handshake ALREADY upgraded!
• In-flight order routing                           • Heartbeat ping/pong idling in RAM
           │                                                   │
           │ (Connection Reset: TCP RST!)                      │
           ▼                                                   ▼
      DROPPED! ──────────────────────────────────► INSTANT SWAP (< 1 microsecond!)
                                                   Shadow promoted to Primary!
                                                   New background thread spawns
                                                   replacement shadow in parallel.
```

### How Pre-Warmed Shadow Pools Work
1. **The Primary Channel:** Sits on an isolated CPU core running `SO_BUSY_POLL`, streaming real-time order fills and market data.
2. **The Shadow Channel:** A secondary, fully authenticated WebSocket session established in advance. It exchanges standard WebSocket ping/pong frames to keep cloud firewalls and stateful NAT tables alive.
3. **Microsecond Failover:**
   * The instant the primary socket receives `POLLHUP`, `POLLERR`, or a TCP `RST`, the gateway's event loop immediately swaps the active socket file descriptor pointer in user space to the shadow connection.
   * **Failover latency is reduced from $50\,\text{ms}$ down to sub-microsecond memory pointer swapping.**
4. **Background Re-arming:** A background worker thread asynchronously establishes a new shadow connection and warms up its TLS session tickets, restoring the $N+1$ redundancy without interrupting trading logic.

---

## 6. Implementation Recipe: OpenSSL Session Caching

In low-latency C/C++ gateways built on OpenSSL or BoringSSL, you must explicitly enable and store session tickets:

```cpp
// 1. Configure SSL_CTX for TLS 1.3 and session tickets
SSL_CTX *ctx = SSL_CTX_new(TLS_client_method());

// Require TLS 1.3 minimum
SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION);

// Enable session caching on the client side
SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_CLIENT);

// 2. Register callback to store NewSessionTicket when sent by exchange
SSL_CTX_sess_set_new_cb(ctx, [](SSL *ssl, SSL_SESSION *sess) -> int {
    // Save sess pointer to internal memory cache indexed by exchange IP / hostname
    save_session_ticket_to_cache(sess);
    return 1; // Retain reference
});

// 3. On Reconnect: Attach stored session ticket BEFORE connecting
SSL *ssl = SSL_new(ctx);
SSL_SESSION *cached_sess = get_session_ticket_from_cache(exchange_host);

if (cached_sess) {
    SSL_set_session(ssl, cached_sess); // Triggers 1-RTT PSK resumption!
}

// 4. Perform non-blocking connect
SSL_connect(ssl);
```

---

## Summary Architecture Checklist

| Mechanism | Cold Handshake | 1-RTT PSK Resumption | 0-RTT Early Data | Pre-Warmed Shadow Pool |
| :--- | :--- | :--- | :--- | :--- |
| **Network Latency** | $3$ RTTs ($6$–$300\,\text{ms}$) | $2$ RTTs ($4$–$200\,\text{ms}$) | $1$ RTT ($2$–$100\,\text{ms}$) | **$< 1\,\mu\text{s}$ (Zero RTT)** |
| **Crypto CPU Overhead** | High (Asymmetric RSA/ECDSA) | Zero (Symmetric PSK derivation) | Zero (Symmetric PSK derivation) | Zero during failover |
| **Replay Attack Risk** | None | None | **High** (orders vulnerable) | None |
| **Production Use Case** | Initial system boot only | Cold fallback reconnects | WebSocket upgrades / subscriptions | Mission-critical order routing |
