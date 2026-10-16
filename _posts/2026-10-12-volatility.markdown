---
title:  "Volatility"
date:  2026-10-12 09:00:00 +0800
categories:
  - economy
tags: economy
classes: wide
layout: single
use_math: true
excerpt: >
  notes, with a five-minute bitcoin round as the running example.
---


The example throughout is a five-minute market on bitcoin: at some instant the round opens, five minutes later it closes, and it settles on whether the price finished above where it started.

### Probability space

A probability space is a triple,

$$
(\Omega,\, \mathcal{F},\, \mathbb{P}) ,
$$

and each piece answers a different question.

$$\Omega$$ is the set of outcomes — every way the five minutes could possibly go. A single $$\omega \in \Omega$$ is not "up" or "down" but an entire price path, every movement from open to close. The answer the round settles on is something you *compute* from $$\omega$$; it is not $$\omega$$ itself.

$$\mathcal{F}$$ is the collection of events to which a probability can be attached. An event is a subset of $$\Omega$$: "finished above the open" is the set of all paths ending higher, "the price never dipped fifty dollars below the open" is another. $$\mathcal{F}$$ is required to be closed under complement and countable union, which is the formal way of insisting that if $$A$$ and $$B$$ are events then so are "not $$A$$", "$$A$$ or $$B$$" and "$$A$$ and $$B$$" — the operations you would perform on them anyway.

$$\mathbb{P}$$ assigns a probability to each event in $$\mathcal{F}$$, with $$\mathbb{P}(\Omega) = 1$$ and countable additivity. It is worth saying plainly that $$\mathbb{P}$$ is a modelling choice rather than something observed directly from the world: the market quotes one measure, your model implies another, and trading is the business of betting that the difference is real.

### Filtered probability space

The triple is enough to ask what the chance of finishing up is. It is not enough to ask anything interesting, because it has no notion of *when* something becomes known. Every event in $$\mathcal{F}$$ sits there on equal footing, the ones settled in the first second alongside the ones settled only at the close.

A filtration repairs that. It is a family $$(\mathcal{F}_t)_{t \ge 0}$$ in which each $$\mathcal{F}_t$$ is itself a collection of events, read as *what is knowable by time* $$t$$, and which grows:

$$
\mathcal{F}_s \subseteq \mathcal{F}_t \qquad \text{whenever } s \le t ,
$$

because information accumulates and is never lost. At the open you know only the opening price. At ninety seconds you have seen ninety seconds of path, so "the price was above the open at $$t = 60$$" belongs to $$\mathcal{F}_{90}$$ — it has been settled. But "the round finishes up" does *not*, however strongly the first half of the path hints at it; no amount of staring at what has happened decides it. At the close, $$\mathcal{F}_{300}$$ contains everything about this round.

Attaching that to the triple gives the filtered probability space,

$$
(\Omega,\, (\mathcal{F}_t)_{t \ge 0},\, \mathcal{F},\, \mathbb{P}) ,
$$

and the inclusion is what makes the whole construction worth the trouble. A trading rule is a decision made at time $$t$$, and for it to be a rule rather than a fantasy it must be measurable with respect to $$\mathcal{F}_t$$ — it may depend on the path so far and on nothing else.

### Jump diffusion

The two sections above set up a stage and put nothing on it. A *model* is a claim about how $$P_t$$ actually moves, and the standard one writes the price in logs,

$$
\log(P_t) = \log(P_0) + \int_0^t \mu_s\, \mathrm{d}s + \int_0^t \sigma_s\, \mathrm{d}W_s + \sum_{k=1}^{N_t} J_k , \qquad t \ge 0 .
$$

Logs first, because returns compound: two consecutive $$+1\%$$ moves multiply, and multiplying is awkward to decompose. In logs they add, so the whole history becomes a sum of increments and each source of movement gets its own term. There are four.

$$\log(P_0)$$ is the opening price, and it is $$\mathcal{F}_0$$-measurable — known the instant the round starts. It is still a random variable, because which round you are in was not decided in advance, but once the round opens it is a number you can read.

$$\int_0^t \mu_s\, \mathrm{d}s$$ is the **drift**, where $$\mu = (\mu_t)_{t \ge 0}$$ is a continuous process: the slow, trend-like part. It has no noise of its own — given the path of $$\mu$$ this integral is an ordinary smooth function of $$t$$. For a five-minute round it is almost nothing. Drift accumulates like $$t$$, and five minutes is $$10^{-5}$$ of a year: even at an extreme $$100\%$$ per year, bitcoin at a hundred thousand dollars drifts about **one dollar** over the round.

$$\int_0^t \sigma_s\, \mathrm{d}W_s$$ is the **diffusion**, the continuous random part, with $$(W_t)_{t \ge 0}$$ a standard Brownian motion and $$\sigma = (\sigma_t)_{t \ge 0}$$ the volatility process. Two things deserve emphasis. First, it accumulates like $$\sqrt{t}$$, not $$t$$ — so over the same five minutes, at a typical $$50\%$$ annualised vol, one standard deviation is about **150 dollars** — more than a hundred times the drift. Over a short horizon the drift is noise and the volatility is the whole story. Second, $$\sigma_s$$ sits *inside* the integral as a process, not a constant: volatility is not a number you estimate once, it is itself a path that moves, and it is only assumed càdlàg — right-continuous with left limits — so it is allowed to jump.

$$\sum_{k=1}^{N_t} J_k$$ is the **jump** part. $$(J_k)_{k \ge 1}$$ are the jump sizes and $$N = (N_t)_{t \ge 0}$$ is a counting process recording how many jumps the log-price has taken by time $$t$$. This term exists because the diffusion cannot produce one: a Brownian path is continuous, so it never covers a finite distance in zero time. Real prices do — a liquidation cascade, an exchange outage, a Fed headline landing mid-round.

Why bother splitting the randomness in two when both terms are random? Because they scale differently, and the scaling is what matters most in a five-minute market. Halve the horizon and the diffusion's contribution falls by $$\sqrt{2}$$ while the drift's falls by $$2$$ — but the jump term does not shrink at all. A jump is either inside your window or it is not. As the window gets short the continuous part becomes negligible and the entire question becomes *will something land in the next few minutes*, which is a question about $$N$$ and the $$J_k$$, not about $$\sigma$$.

Everything on the right is adapted, so $$\log(P_t)$$ is $$\mathcal{F}_t$$-measurable and the model respects the constraint of the previous section. What is *not* available at time $$t$$ is the decomposition itself: you observe the sum, never the four terms separately. Recovering how much of a realised move was diffusion and how much was a jump is an estimation problem, and it is where realized volatility begins.

### Realized volatility

Realized volatility is built from nothing but the observed path, and the construction runs through the variance. Cut $$[0, T]$$ into $$n$$ pieces, write the log return over each,

$$
r_i = \log P_{t_i} - \log P_{t_{i-1}} , \qquad i = 1, \dots, n ,
$$

and add the squares:

$$
RV_n = \sum_{i=1}^{n} r_i^2 .
$$

Realized volatility is the square root of that, annualised by the $$\sqrt{t}$$ rule.

By itself that is just a number computed from the data. What makes it useful is that it has a limit: as the sampling interval shrinks, $$RV_n$$ converges in probability to the quadratic variation of the log price,

$$
RV_n \;\xrightarrow{\;p\;}\; [\log P]_T = \int_0^T \sigma_t^2\,\mathrm{d}t \;+\; \sum_{k=1}^{N_T} J_k^2 .
$$

The first piece is the **integrated variance** — the diffusion's entire contribution over the window. The second is the jumps', each entering as its square. The drift is gone.

The first half of that is true by definition. Quadratic variation is *defined* as the limit of summed squared increments,

$$
[X]_T = \lim_{n \to \infty} \sum_{i=1}^{n} \big( X_{t_i} - X_{t_{i-1}} \big)^2 ,
$$

and with $$X = \log P$$ those increments are precisely the log returns $$r_i$$. So $$\sum r_i^2 \to [\log P]_T$$ is the definition being applied, not a result. What needs an argument is the right-hand side — why the limit resolves into integrated variance plus squared jumps, with no drift anywhere in it.

Take the continuous part first. Over one short interval the coefficients barely move, so hold them constant at the left endpoint:

$$
r_i \approx \mu\,\Delta t + \sigma\,\Delta W_i , \qquad \Delta W_i \sim N(0, \Delta t) .
$$

Squaring produces three terms,

$$
r_i^2 \approx \mu^2 (\Delta t)^2 + 2\mu\sigma\,\Delta t\,\Delta W_i + \sigma^2 (\Delta W_i)^2 ,
$$

and everything depends on how each behaves once $$n$$ of them are summed with $$\Delta t = T/n$$. The one fact needed is that $$\Delta W_i$$ has standard deviation $$\sqrt{\Delta t}$$, which dwarfs $$\Delta t$$ itself:

| term | one of them | summed over $$n$$ | as $$n \to \infty$$ |
|---|---|---|---|
| drift squared | $$(\Delta t)^2$$ | $$T\,\Delta t$$ | $$\to 0$$ |
| cross term | $$\Delta t\,\sqrt{\Delta t}$$ | $$\sim T\sqrt{\Delta t}$$ | $$\to 0$$ |
| diffusion squared | $$\Delta t$$ | $$\sim \sigma^2 T$$ | survives |

Only the last one lives. That is why $$\mu$$ never reaches the answer, and why subtracting the mean would be wasted effort — the drift's whole contribution is a higher-order term that the refinement destroys.

Jumps behave differently, and in the way the previous section described: a jump does not shrink with the partition. However fine the grid, the interval containing it still takes the entire $$J_k^2$$. So the jumps survive the limit intact, as the second sum: realized variance measures diffusion and jumps *together*.

### DVOL

Nothing in the model says $$\sigma_t$$ is observable. There are two ways to get at it: look backwards and estimate it from the path that already happened, or ask someone who is being paid to have an opinion about the future. DVOL is the second.

It is Deribit's bitcoin implied volatility index — one number, in annualised percent, for the volatility the options market is pricing over the next thirty days.

What DVOL computes is the fair strike of a variance swap,

$$
K_{\text{var}} = \frac{2 e^{rT}}{T} \left( \int_0^F \frac{P(K)}{K^2}\,\mathrm{d}K + \int_F^\infty \frac{C(K)}{K^2}\,\mathrm{d}K \right) ,
$$

where $$C(K)$$ and $$P(K)$$ are today's call and put prices at strike $$K$$, $$F$$ is the forward price, $$r$$ the interest rate and $$T$$ the maturity. The underlying is written $$S_t$$ for the rest of this section, to keep it apart from the $$P(K)$$ of a put. Deriving it takes four steps.

**One: the fair strike is an expected variance.** A variance swap costs nothing to enter, so its value at inception is zero,

$$
e^{-rT}\,\mathbb{E}^{\mathbb{Q}}\big[\sigma_R^2 - K_{\text{var}}\big] = 0 ,
$$

and under continuous monitoring the annualised realised variance is the integrated variance of the previous section divided by the horizon,

$$
\sigma_R^2 = \frac{1}{T}\int_0^T \sigma_t^2\,\mathrm{d}t ,
$$

so that

$$
K_{\text{var}} = \frac{1}{T}\,\mathbb{E}^{\mathbb{Q}}\Big[\int_0^T \sigma_t^2\,\mathrm{d}t\Big] .
$$

The problem is now to compute that expectation without knowing what process $$\sigma_t$$ follows.

**Two: Itô's lemma converts variance into a log contract.** With $$\mathrm{d}S_t = \mu_t S_t\,\mathrm{d}t + \sigma_t S_t\,\mathrm{d}W_t$$, applying [Itô's lemma]({{ site.baseurl }}/math/2026/10/13/itos-lemma.html) to $$\ln S_t$$ produces the familiar extra term,

$$
\mathrm{d}\ln S_t = \frac{\mathrm{d}S_t}{S_t} - \frac12\,\sigma_t^2\,\mathrm{d}t ,
$$

and integrating and rearranging isolates the quantity we want:

$$
\int_0^T \sigma_t^2\,\mathrm{d}t = 2\int_0^T \frac{\mathrm{d}S_t}{S_t} - 2\ln\frac{S_T}{S_0} .
$$

Take expectations under $$\mathbb{Q}$$, where $$\mathrm{d}S_t/S_t = r\,\mathrm{d}t + \sigma_t\,\mathrm{d}W^{\mathbb{Q}}_t$$ if the underlying pays no dividend. The stochastic integral is a martingale and contributes nothing, so the first term leaves only its drift, $$rT$$. Splitting the second at the forward price $$F = S_0 e^{rT}$$ gives $$\ln(S_T/S_0) = \ln(S_T/F) + rT$$, and the two $$rT$$ cancel:

$$
K_{\text{var}} = -\frac{2}{T}\,\mathbb{E}^{\mathbb{Q}}\Big[\ln\frac{S_T}{F}\Big] .
$$

Pricing variance has become pricing a single payoff that depends only on the final price.

**Three: options replicate that payoff.** For any twice-differentiable $$f$$ and any expansion point $$F$$,

$$
f(S_T) = f(F) + f'(F)(S_T - F) + \int_0^F f''(K)\,(K - S_T)^+\,\mathrm{d}K + \int_F^\infty f''(K)\,(S_T - K)^+\,\mathrm{d}K .
$$

This is Taylor's theorem with an integral remainder. If $$S_T < F$$ the remainder is $$\int_{S_T}^{F} f''(K)(K - S_T)\,\mathrm{d}K$$; since $$(K - S_T)^+$$ is zero below $$S_T$$ and equals $$K - S_T$$ between $$S_T$$ and $$F$$, that is exactly the third term, while the fourth is zero. The case $$S_T > F$$ is symmetric.

Taking $$f(S) = \ln(S/F)$$, so that $$f(F) = 0$$, $$f'(F) = 1/F$$ and $$f''(K) = -1/K^2$$,

$$
\ln\frac{S_T}{F} = \frac{S_T - F}{F} - \int_0^F \frac{(K - S_T)^+}{K^2}\,\mathrm{d}K - \int_F^\infty \frac{(S_T - K)^+}{K^2}\,\mathrm{d}K .
$$

A log contract is a forward position minus a strip of out-of-the-money options, each weighted by $$1/K^2$$: puts below the forward, calls above it.

**Four: take expectations term by term.** $$F$$ is the risk-neutral expectation of $$S_T$$, so the forward term vanishes. An option price today is the discounted expected payoff, which inverted gives $$\mathbb{E}^{\mathbb{Q}}[(K - S_T)^+] = e^{rT}P(K)$$ and $$\mathbb{E}^{\mathbb{Q}}[(S_T - K)^+] = e^{rT}C(K)$$. Hence

$$
\mathbb{E}^{\mathbb{Q}}\Big[\ln\frac{S_T}{F}\Big] = -e^{rT}\left( \int_0^F \frac{P(K)}{K^2}\,\mathrm{d}K + \int_F^\infty \frac{C(K)}{K^2}\,\mathrm{d}K \right) ,
$$

and substituting into step two returns the formula above.

Because it is annualised, getting to a horizon you care about is the $$\sqrt{t}$$ rule again — and for a market that never closes, with $$365$$ rather than the $$252$$ trading days an equity index would use:

$$
\text{daily move} \;\approx\; \frac{\text{DVOL}}{\sqrt{365}} \;\approx\; \frac{\text{DVOL}}{19} .
$$

Deribit's own rule of thumb is to divide by $$20$$. Here is the index live, with that arithmetic already carried down to one of our rounds.

<div id="dvol-live">
<style>
#dvol-live{border:1px solid rgba(128,128,128,.4);border-radius:8px;padding:.8em 1em .6em;margin:1.5em 0}
#dvol-live .hd{font-size:.82em;opacity:.7;margin-bottom:.1em}
#dvol-live .row{display:flex;flex-wrap:wrap;gap:.3em 1.4em;align-items:baseline}
#dvol-live .val{font-size:2.2em;font-weight:600;font-variant-numeric:tabular-nums;line-height:1.15}
#dvol-live .pct{font-size:1em;opacity:.55;margin-left:-.3em}
#dvol-live .chg{font-size:.9em;font-variant-numeric:tabular-nums;opacity:0;transition:opacity .35s}
#dvol-live.ready .chg{opacity:1}
#dvol-live .chg.up{color:#16a34a}
#dvol-live .chg.dn{color:#dc2626}
#dvol-live svg{display:block;width:100%;height:auto;margin:.3em 0 .15em;overflow:hidden}
#dvol-live .ax{display:flex;justify-content:space-between;font-size:.76em;opacity:.6;margin-bottom:.55em}
#dvol-live .dv{font-size:.9em;border-top:1px solid rgba(128,128,128,.25);padding-top:.55em}
#dvol-live b{font-variant-numeric:tabular-nums;font-weight:600}
#dvol-live .stamp{font-size:.74em;opacity:.5;margin-top:.45em}
</style>
<div class="hd">BTC DVOL &middot; 30-day implied volatility, annualised</div>
<div class="row"><span class="val">&mdash;</span><span class="pct">%</span><span class="chg">&mdash;</span></div>
<svg viewBox="0 0 640 88" role="img" aria-label="BTC DVOL over the last 30 days">
<path class="area" fill="#3b82f6" fill-opacity=".09"></path>
<path class="line" fill="none" stroke="#3b82f6" stroke-width="1.6" stroke-linejoin="round"></path>
<circle class="dot" cx="-10" cy="-10" r="2.6" fill="#3b82f6"></circle>
</svg>
<div class="ax"><span>30 days ago</span><span>low <b class="lo">&mdash;</b> &middot; high <b class="hi">&mdash;</b></span><span>now</span></div>
<div class="row dv"><span>&asymp; <b class="day">&mdash;</b> per day</span><span>&asymp; <b class="five">&mdash;</b> over a five-minute round, at BTC <b class="btc">&mdash;</b></span></div>
<div class="stamp">loading&hellip;</div>
</div>

<script>
(function(){
  var root = document.getElementById('dvol-live');
  if (!root) return;
  var API  = 'https://www.deribit.com/api/v2/public/',
      YEAR = 365 * 24 * 3600,
      DAYS = 30,
      q    = function(s){ return root.querySelector(s); };

  function get(url){
    return fetch(url, {cache:'no-store'}).then(function(r){
      if (!r.ok) throw new Error('HTTP ' + r.status);
      return r.json();
    }).then(function(j){ return j.result; });
  }

  function spark(closes){
    var W = 640, H = 88, p = 3,
        lo = Math.min.apply(null, closes),
        hi = Math.max.apply(null, closes),
        span = (hi - lo) || 1,
        n = closes.length,
        X = function(i){ return p + i * (W - 2*p) / (n - 1); },
        Y = function(v){ return p + (hi - v) * (H - 2*p) / span; },
        d = '', i;
    for (i = 0; i < n; i++) d += (i ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(closes[i]).toFixed(1);
    q('.line').setAttribute('d', d);
    q('.area').setAttribute('d', d + 'L' + X(n-1).toFixed(1) + ' ' + H + 'L' + X(0).toFixed(1) + ' ' + H + 'Z');
    q('.dot').setAttribute('cx', X(n-1).toFixed(1));
    q('.dot').setAttribute('cy', Y(closes[n-1]).toFixed(1));
    q('.hi').textContent = hi.toFixed(1);
    q('.lo').textContent = lo.toFixed(1);
  }

  function render(rows, btc){
    var closes = rows.map(function(r){ return r[4]; }),
        now    = closes[closes.length - 1],
        back   = closes.length > 24 ? closes[closes.length - 25] : closes[0],
        chg    = now - back;

    q('.val').textContent  = now.toFixed(2);
    q('.day').textContent  = (now / Math.sqrt(365)).toFixed(2) + '%';
    q('.five').textContent = '$' + Math.round(now / 100 * Math.sqrt(300 / YEAR) * btc).toLocaleString();
    q('.btc').textContent  = '$' + Math.round(btc).toLocaleString();

    var c = q('.chg');
    c.textContent = (chg >= 0 ? '▲ +' : '▼ −') + Math.abs(chg).toFixed(2) + ' (24h)';
    c.className = 'chg ' + (chg >= 0 ? 'up' : 'dn');

    spark(closes);
    q('.stamp').textContent = 'Deribit, ' + new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
    root.classList.add('ready');
  }

  function load(){
    var end = Date.now(), start = end - DAYS * 86400 * 1000;
    Promise.all([
      get(API + 'get_volatility_index_data?currency=BTC&resolution=3600' +
          '&start_timestamp=' + start + '&end_timestamp=' + end),
      get(API + 'get_index_price?index_name=btc_usd')
    ]).then(function(r){
      var rows = r[0] && r[0].data;
      if (!rows || rows.length < 2) throw new Error('no data');
      render(rows, r[1].index_price);
    }).catch(function(e){
      q('.stamp').textContent = 'live value unavailable (' + e.message + ')';
    });
  }

  load();
  setInterval(load, 60000);
})();
</script>

### References

1. A. Goel, P. Pasricha, M. Magris, J. Kanniainen, "Foundation Time-Series AI Model for Realized Volatility Forecasting," 2025. [arXiv:2505.11163](https://arxiv.org/abs/2505.11163).
2. S. Fernando, "DVOL &mdash; Deribit Implied Volatility Index," *Deribit Insights*, 2021. [Article](https://insights.deribit.com/exchange-updates/dvol-deribit-implied-volatility-index/).
3. P. Carr, D. Madan, "Towards a Theory of Volatility Trading," in *Volatility: New Estimation Techniques for Pricing Derivatives*, R. Jarrow (ed.), RISK Publications, 1998. [Reprint](https://doi.org/10.1017/cbo9780511569708.013).
