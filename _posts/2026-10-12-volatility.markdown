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

$$\Omega$$ is the set of outcomes — every way the five minutes could possibly go. A single $$\omega \in \Omega$$ is not "up" or "down" but an entire price path, the whole wiggle from open to close. The answer the round settles on is something you *compute* from $$\omega$$; it is not $$\omega$$ itself.

$$\mathcal{F}$$ is the collection of events to which a probability can be attached. An event is a subset of $$\Omega$$: "finished above the open" is the set of all paths ending higher, "the price never dipped fifty dollars below the open" is another. $$\mathcal{F}$$ is required to be closed under complement and countable union, which is the formal way of insisting that if $$A$$ and $$B$$ are events then so are "not $$A$$", "$$A$$ or $$B$$" and "$$A$$ and $$B$$" — the operations you would perform on them anyway.

$$\mathbb{P}$$ assigns a probability to each event in $$\mathcal{F}$$, with $$\mathbb{P}(\Omega) = 1$$ and countable additivity. It is worth saying plainly that $$\mathbb{P}$$ is a modelling choice rather than something read off the world: the market quotes one measure, your model implies another, and trading is the business of betting that the difference is real.

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

$$\int_0^t \mu_s\, \mathrm{d}s$$ is the **drift**, where $$\mu = (\mu_t)_{t \ge 0}$$ is a continuous process: the slow, trend-like part. It has no noise of its own — given the path of $$\mu$$ this integral is an ordinary smooth function of $$t$$. For a five-minute round it is almost nothing. Drift accumulates like $$t$$, and five minutes is $$10^{-5}$$ of a year: even at a ferocious $$100\%$$ per year, bitcoin at a hundred thousand dollars drifts about **one dollar** over the round.

$$\int_0^t \sigma_s\, \mathrm{d}W_s$$ is the **diffusion**, the continuous random part, with $$(W_t)_{t \ge 0}$$ a standard Brownian motion and $$\sigma = (\sigma_t)_{t \ge 0}$$ the volatility process. Two things deserve emphasis. First, it accumulates like $$\sqrt{t}$$, not $$t$$ — so over the same five minutes, at a typical $$50\%$$ annualised vol, one standard deviation is about **150 dollars** — more than a hundred times the drift. Over a short horizon the drift is noise and the volatility is the whole story. Second, $$\sigma_s$$ sits *inside* the integral as a process, not a constant: volatility is not a number you estimate once, it is itself a path that moves, and it is only assumed càdlàg — right-continuous with left limits — so it is allowed to jump.

$$\sum_{k=1}^{N_t} J_k$$ is the **jump** part. $$(J_k)_{k \ge 1}$$ are the jump sizes and $$N = (N_t)_{t \ge 0}$$ is a counting process recording how many jumps the log-price has taken by time $$t$$. This term exists because the diffusion cannot produce one: a Brownian path is continuous, so it never covers a finite distance in zero time. Real prices do — a liquidation cascade, an exchange outage, a Fed headline landing mid-round.

Why bother splitting the randomness in two when both terms are random? Because they scale differently, and the scaling is what a five-minute market lives on. Halve the horizon and the diffusion's contribution falls by $$\sqrt{2}$$ while the drift's falls by $$2$$ — but the jump term does not shrink at all. A jump is either inside your window or it is not. As the window gets short the continuous part quietly dies away and the entire question becomes *will something land in the next few minutes*, which is a question about $$N$$ and the $$J_k$$, not about $$\sigma$$.

Everything on the right is adapted, so $$\log(P_t)$$ is $$\mathcal{F}_t$$-measurable and the model respects the constraint of the previous section. What is *not* available at time $$t$$ is the decomposition itself: you observe the sum, never the four terms separately. Recovering how much of a realised move was diffusion and how much was a jump is an estimation problem, and it is where realized volatility begins.

### DVOL

Nothing in the model says $$\sigma_t$$ is observable. There are two ways to get at it: look backwards and estimate it from the path that already happened, or ask someone who is being paid to have an opinion about the future. DVOL is the second.

It is Deribit's bitcoin implied volatility index — one number, in annualised percent, for the volatility the options market is pricing over the next thirty days. Bitcoin's VIX, and built the same way. Deribit is the venue that matters here because close to nine out of ten bitcoin options traded anywhere are traded on it, so its book is not one opinion among many.

The construction is worth knowing, because it is not what people assume. DVOL does not take some option's Black–Scholes implied vol and call it the answer. It takes the two expiries that bracket thirty days, prices every option on each from the depth of the book, throws away the in-the-money strikes and the far wings below five delta, applies the **variance swap** formula to what is left, interpolates the two variances to exactly thirty days, and takes the square root. Integrating the whole smile rather than reading one point off it is what makes the number model-free — and it means DVOL is an estimate of precisely the object in our equation: the expected $$\int \sigma_s^2\, \mathrm{d}s$$ over the next thirty days, annualised.

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


Two things stop this from being the answer to the five-minute question.

The first is the horizon. Thirty days is not five minutes, and the gap is not a detail: realised volatility over any given five minutes swings by multiples around the thirty-day level, driven by time of day and by whatever is on the calendar. DVOL tells you which regime you are in. It does not tell you what the next round will do.

The second is subtler, and it is the one the first section warned about. Option prices are risk-neutral prices, so DVOL is an expectation under $$\mathbb{Q}$$, not under $$\mathbb{P}$$ — it is what volatility costs, not what volatility will be. Those differ systematically and in a known direction: implied sits above subsequently realised, because the seller is being paid to carry the risk. Treating DVOL as a forecast of realised volatility gives a forecast that is biased high on purpose. That gap has a name, the variance risk premium, and it is traded in its own right.

Which makes DVOL a useful thing to look at twice. The first section said $$\mathbb{P}$$ is a modelling choice, and that the market quotes one measure while your model implies another. DVOL is that sentence with a public API in front of it.

### References

1. A. Goel, P. Pasricha, M. Magris, J. Kanniainen, "Foundation Time-Series AI Model for Realized Volatility Forecasting," 2025. [arXiv:2505.11163](https://arxiv.org/abs/2505.11163).
2. S. Fernando, "DVOL &mdash; Deribit Implied Volatility Index," *Deribit Insights*, 2021. [Article](https://insights.deribit.com/exchange-updates/dvol-deribit-implied-volatility-index/).
