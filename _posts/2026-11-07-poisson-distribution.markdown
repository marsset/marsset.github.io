---
title:  "Poisson Distribution"
date:   2026-11-07 14:00:00 +0800
categories:
  - math
tags: [math, probability, stochastic-processes]
excerpt: >
  A first-principles derivation of the Poisson distribution from the binomial limit, defining signatures, and its asymptotic convergence to the Gaussian distribution.
---

Most fundamental probability distributions are answers to questions about geometry or games of chance: tossing coins, rolling dice, or measuring lengths. 

The **Poisson distribution** is different. It is an answer to a question about continuous time:

> *If unpredictable events happen completely independently from one another at a steady average rate, how many will occur during a fixed window of time?*

It governs radioactive decay, cosmic ray strikes on microchips, the arrival of network packets at a router, customer requests hitting a web server, and incoming market orders at an exchange matching engine.

---

### 1. Derivation: The Law of Rare Events

The cleanest way to understand why the Poisson formula has its specific structure is to derive it as the natural limiting case of the Binomial distribution.

Suppose events occur at an average intensity of $$\lambda$$ events per unit of time. We want to observe a fixed time interval of length $$T$$, so the expected total number of events is:

$$
\mu = \lambda T
$$

Now, slice this continuous interval $$[0, T]$$ into $$n$$ tiny, disjoint sub-intervals of width $$\Delta t = \frac{T}{n}$$.

```
[--- Δt ---][--- Δt ---][--- Δt ---] ... [--- Δt ---]
     1           2           3                 n
```

We make two physical assumptions:
1. **Rareness:** As $$n \to \infty$$, the sub-interval $$\Delta t$$ becomes so infinitesimally narrow that the probability of *two or more* events occurring in the exact same slice is negligible: $$o(\Delta t)$$.
2. **Independence:** What happens inside slice $$i$$ has zero influence on slice $$j$$.

Under these assumptions, each slice is an independent Bernoulli trial:
* Success (an event occurs) with probability $$p \approx \lambda \Delta t = \lambda \left(\frac{T}{n}\right) = \frac{\mu}{n}$$.
* Failure (no event occurs) with probability $$1 - p = 1 - \frac{\mu}{n}$$.

The total number of events $$K$$ across the whole interval $$[0, T]$$ is the sum of these $$n$$ Bernoulli trials, which follows the Binomial distribution:

$$
\mathbb{P}(K = k) = \binom{n}{k} p^k (1 - p)^{n - k} = \frac{n!}{k!(n - k)!} \left( \frac{\mu}{n} \right)^k \left( 1 - \frac{\mu}{n} \right)^{n - k}
$$

Now, let the discretization vanish by taking the limit as $$n \to \infty$$ with $$\mu$$ held constant.

Rearrange the terms:

$$
\mathbb{P}(K = k) = \frac{\mu^k}{k!} \cdot \underbrace{\left[ \frac{n(n - 1)(n - 2)\cdots(n - k + 1)}{n^k} \right]}_{\text{Factor 1}} \cdot \underbrace{\left( 1 - \frac{\mu}{n} \right)^n}_{\text{Factor 2}} \cdot \underbrace{\left( 1 - \frac{\mu}{n} \right)^{-k}}_{\text{Factor 3}}
$$

Examine the behavior of each factor as $$n \to \infty$$:

1. **Factor 1:** A product of $$k$$ linear terms, each divided by $$n$$:

   $$
   \lim_{n \to \infty} \frac{n}{n} \cdot \frac{n - 1}{n} \cdots \frac{n - k + 1}{n} = 1 \cdot 1 \cdots 1 = 1
   $$

2. **Factor 2:** The standard exponential limit:

   $$
   \lim_{n \to \infty} \left( 1 - \frac{\mu}{n} \right)^n = e^{-\mu}
   $$

3. **Factor 3:** Since $$k$$ and $$\mu$$ are fixed, $$\frac{\mu}{n} \to 0$$:

   $$
   \lim_{n \to \infty} \left( 1 - \frac{\mu}{n} \right)^{-k} = (1 - 0)^{-k} = 1
   $$

Multiplying them together yields the **Poisson probability mass function**:

$$
\mathbb{P}(K = k) = \frac{\mu^k e^{-\mu}}{k!} \qquad (k = 0, 1, 2, \dots)
$$

For a unit time interval where $$\mu = \lambda$$:

$$
\mathbb{P}(K = k) = \frac{\lambda^k e^{-\lambda}}{k!}
$$

---

### 2. Properties: The Defining Signature

#### Total Probability Sums to One
A quick sanity check using the Taylor series of $$e^\lambda$$:

$$
\sum_{k=0}^{\infty} \mathbb{P}(K = k) = \sum_{k=0}^{\infty} \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=0}^{\infty} \frac{\lambda^k}{k!} = e^{-\lambda} \cdot e^\lambda = 1
$$

#### The Mean ($$\mathbb{E}[K] = \lambda$$)
Using the property that the $$k=0$$ term vanishes:

$$
\mathbb{E}[K] = \sum_{k=0}^{\infty} k \frac{\lambda^k e^{-\lambda}}{k!} = \sum_{k=1}^{\infty} \frac{\lambda^k e^{-\lambda}}{(k - 1)!} = \lambda e^{-\lambda} \sum_{k=1}^{\infty} \frac{\lambda^{k-1}}{(k - 1)!}
$$

Substitute $$j = k - 1$$:

$$
\mathbb{E}[K] = \lambda e^{-\lambda} \sum_{j=0}^{\infty} \frac{\lambda^j}{j!} = \lambda e^{-\lambda} e^\lambda = \lambda
$$

#### The Variance ($$\operatorname{Var}(K) = \lambda$$)
To compute variance, evaluate the factorial moment $$\mathbb{E}[K(K - 1)]$$:

$$
\mathbb{E}[K(K - 1)] = \sum_{k=2}^{\infty} k(k - 1) \frac{\lambda^k e^{-\lambda}}{k!} = \lambda^2 e^{-\lambda} \sum_{k=2}^{\infty} \frac{\lambda^{k-2}}{(k - 2)!} = \lambda^2
$$

Since $$\mathbb{E}[K^2] = \mathbb{E}[K(K - 1)] + \mathbb{E}[K] = \lambda^2 + \lambda$$:

$$
\operatorname{Var}(K) = \mathbb{E}[K^2] - (\mathbb{E}[K])^2 = (\lambda^2 + \lambda) - \lambda^2 = \lambda
$$

> **The Poisson Signature:** The mean equals the variance:
> 
> $$
> \mathbb{E}[K] = \operatorname{Var}(K) = \lambda
> $$

The ratio of variance to mean is called the **Fano factor**:

$$
F = \frac{\operatorname{Var}(K)}{\mathbb{E}[K]}
$$

- For a true Poisson process, $$F = 1$$ exactly.
- **Over-dispersion ($$F > 1$$):** Events cluster or trigger one another (contagion, self-excitation, or bursty traffic).
- **Under-dispersion ($$F < 1$$):** Events repel or pace each other (periodic schedules, queues with refractoriness).

---

### 3. Relation to the Normal Distribution

As arrival intensity $$\lambda$$ increases, the Poisson distribution undergoes a fundamental qualitative transformation: its right-skewed asymmetry vanishes and converges into a symmetric Gaussian bell curve.

<figure style="margin: 2.2em auto; text-align: center;">
<svg viewBox="0 0 840 500" width="100%" style="max-width:840px;display:block;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;" role="img" aria-label="Poisson distribution probability mass functions for lambda equals 1, 4, 10, and 20">
  <defs>
    <style>
      .p-axis { stroke: currentColor; stroke-opacity: 0.5; stroke-width: 1.2; }
      .p-grid { stroke: currentColor; stroke-opacity: 0.08; stroke-dasharray: 3,3; stroke-width: 1; }
      .p-tick { fill: currentColor; font-size:12.0px; fill-opacity: 0.65; }
      .p-axis-title { fill: currentColor; font-size: 13px; font-weight: 500; fill-opacity: 0.85; }
      .p-legend-title { fill: currentColor; font-size: 12px; font-weight: 600; fill-opacity: 0.9; }
      .p-legend-text { fill: currentColor; font-size:12.0px; fill-opacity: 0.8; }
      .p-annot { font-size:12.0px; font-weight: 500; }
    </style>
  </defs>
  <line x1="70" y1="373.75" x2="805" y2="373.75" class="p-grid" />
  <text x="60" y="377.75" text-anchor="end" class="p-tick">0.05</text>
  <line x1="70" y1="327.50" x2="805" y2="327.50" class="p-grid" />
  <text x="60" y="331.50" text-anchor="end" class="p-tick">0.10</text>
  <line x1="70" y1="281.25" x2="805" y2="281.25" class="p-grid" />
  <text x="60" y="285.25" text-anchor="end" class="p-tick">0.15</text>
  <line x1="70" y1="235.00" x2="805" y2="235.00" class="p-grid" />
  <text x="60" y="239.00" text-anchor="end" class="p-tick">0.20</text>
  <line x1="70" y1="188.75" x2="805" y2="188.75" class="p-grid" />
  <text x="60" y="192.75" text-anchor="end" class="p-tick">0.25</text>
  <line x1="70" y1="142.50" x2="805" y2="142.50" class="p-grid" />
  <text x="60" y="146.50" text-anchor="end" class="p-tick">0.30</text>
  <line x1="70" y1="96.25" x2="805" y2="96.25" class="p-grid" />
  <text x="60" y="100.25" text-anchor="end" class="p-tick">0.35</text>
  <line x1="70" y1="50.00" x2="805" y2="50.00" class="p-grid" />
  <text x="60" y="54.00" text-anchor="end" class="p-tick">0.40</text>
  <line x1="70.00" y1="50" x2="70.00" y2="420" class="p-grid" />
  <text x="70.00" y="440.00" text-anchor="middle" class="p-tick">0</text>
  <line x1="115.94" y1="50" x2="115.94" y2="420" class="p-grid" />
  <text x="115.94" y="440.00" text-anchor="middle" class="p-tick">2</text>
  <line x1="161.88" y1="50" x2="161.88" y2="420" class="p-grid" />
  <text x="161.88" y="440.00" text-anchor="middle" class="p-tick">4</text>
  <line x1="207.81" y1="50" x2="207.81" y2="420" class="p-grid" />
  <text x="207.81" y="440.00" text-anchor="middle" class="p-tick">6</text>
  <line x1="253.75" y1="50" x2="253.75" y2="420" class="p-grid" />
  <text x="253.75" y="440.00" text-anchor="middle" class="p-tick">8</text>
  <line x1="299.69" y1="50" x2="299.69" y2="420" class="p-grid" />
  <text x="299.69" y="440.00" text-anchor="middle" class="p-tick">10</text>
  <line x1="345.62" y1="50" x2="345.62" y2="420" class="p-grid" />
  <text x="345.62" y="440.00" text-anchor="middle" class="p-tick">12</text>
  <line x1="391.56" y1="50" x2="391.56" y2="420" class="p-grid" />
  <text x="391.56" y="440.00" text-anchor="middle" class="p-tick">14</text>
  <line x1="437.50" y1="50" x2="437.50" y2="420" class="p-grid" />
  <text x="437.50" y="440.00" text-anchor="middle" class="p-tick">16</text>
  <line x1="483.44" y1="50" x2="483.44" y2="420" class="p-grid" />
  <text x="483.44" y="440.00" text-anchor="middle" class="p-tick">18</text>
  <line x1="529.38" y1="50" x2="529.38" y2="420" class="p-grid" />
  <text x="529.38" y="440.00" text-anchor="middle" class="p-tick">20</text>
  <line x1="575.31" y1="50" x2="575.31" y2="420" class="p-grid" />
  <text x="575.31" y="440.00" text-anchor="middle" class="p-tick">22</text>
  <line x1="621.25" y1="50" x2="621.25" y2="420" class="p-grid" />
  <text x="621.25" y="440.00" text-anchor="middle" class="p-tick">24</text>
  <line x1="667.19" y1="50" x2="667.19" y2="420" class="p-grid" />
  <text x="667.19" y="440.00" text-anchor="middle" class="p-tick">26</text>
  <line x1="713.12" y1="50" x2="713.12" y2="420" class="p-grid" />
  <text x="713.12" y="440.00" text-anchor="middle" class="p-tick">28</text>
  <line x1="759.06" y1="50" x2="759.06" y2="420" class="p-grid" />
  <text x="759.06" y="440.00" text-anchor="middle" class="p-tick">30</text>
  <line x1="805.00" y1="50" x2="805.00" y2="420" class="p-grid" />
  <text x="805.00" y="440.00" text-anchor="middle" class="p-tick">32</text>
  <line x1="92.97" y1="420" x2="92.97" y2="424" class="p-axis" />
  <line x1="138.91" y1="420" x2="138.91" y2="424" class="p-axis" />
  <line x1="184.84" y1="420" x2="184.84" y2="424" class="p-axis" />
  <line x1="230.78" y1="420" x2="230.78" y2="424" class="p-axis" />
  <line x1="276.72" y1="420" x2="276.72" y2="424" class="p-axis" />
  <line x1="322.66" y1="420" x2="322.66" y2="424" class="p-axis" />
  <line x1="368.59" y1="420" x2="368.59" y2="424" class="p-axis" />
  <line x1="414.53" y1="420" x2="414.53" y2="424" class="p-axis" />
  <line x1="460.47" y1="420" x2="460.47" y2="424" class="p-axis" />
  <line x1="506.41" y1="420" x2="506.41" y2="424" class="p-axis" />
  <line x1="552.34" y1="420" x2="552.34" y2="424" class="p-axis" />
  <line x1="598.28" y1="420" x2="598.28" y2="424" class="p-axis" />
  <line x1="644.22" y1="420" x2="644.22" y2="424" class="p-axis" />
  <line x1="690.16" y1="420" x2="690.16" y2="424" class="p-axis" />
  <line x1="736.09" y1="420" x2="736.09" y2="424" class="p-axis" />
  <line x1="782.03" y1="420" x2="782.03" y2="424" class="p-axis" />
  <line x1="70" y1="420" x2="805" y2="420" class="p-axis" />
  <line x1="70" y1="50" x2="70" y2="420" class="p-axis" />
  <text x="437.5" y="468" text-anchor="middle" class="p-axis-title">Number of Occurrences (k)</text>
  <text x="24.0" y="235.0" text-anchor="middle" transform="rotate(-90, 24.0, 235.0)" class="p-axis-title">Probability P(K = k)</text>
  <g transform="translate(610, 55)">
    <rect x="0" y="0" width="190" height="118" rx="6" fill="currentColor" fill-opacity="0.04" stroke="currentColor" stroke-opacity="0.14" />
    <text x="16" y="20" class="p-legend-title">Mean Arrival Rate (λ)</text>
    <circle cx="24" cy="40" r="4" fill="#3b82f6" />
    <line x1="12" y1="40" x2="36" y2="40" stroke="#3b82f6" stroke-width="2" />
    <text x="46" y="43.5" class="p-legend-text">λ = 1 (σ = 1.00)</text>
    <circle cx="24" cy="60" r="4" fill="#10b981" />
    <line x1="12" y1="60" x2="36" y2="60" stroke="#10b981" stroke-width="2" />
    <text x="46" y="63.5" class="p-legend-text">λ = 4 (σ = 2.00)</text>
    <circle cx="24" cy="80" r="4" fill="#f59e0b" />
    <line x1="12" y1="80" x2="36" y2="80" stroke="#f59e0b" stroke-width="2" />
    <text x="46" y="83.5" class="p-legend-text">λ = 10 (σ = 3.16)</text>
    <circle cx="24" cy="100" r="4" fill="#8b5cf6" />
    <line x1="12" y1="100" x2="36" y2="100" stroke="#8b5cf6" stroke-width="2" />
    <text x="46" y="103.5" class="p-legend-text">λ = 20 (σ = 4.47)</text>
  </g>
  <line x1="70.00" y1="420" x2="70.00" y2="79.71" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="92.97" y1="420" x2="92.97" y2="79.71" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="115.94" y1="420" x2="115.94" y2="249.86" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="138.91" y1="420" x2="138.91" y2="363.29" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="161.88" y1="420" x2="161.88" y2="405.82" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="184.84" y1="420" x2="184.84" y2="417.16" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="207.81" y1="420" x2="207.81" y2="419.53" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="230.78" y1="420" x2="230.78" y2="419.93" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="253.75" y1="420" x2="253.75" y2="419.99" stroke="#3b82f6" stroke-width="1.2" stroke-opacity="0.35" />
  <path d="M 70.00 79.71 C 73.83 79.71, 85.31 51.35, 92.97 79.71 C 100.62 108.07, 108.28 202.59, 115.94 249.86 C 123.59 297.12, 131.25 337.29, 138.91 363.29 C 146.56 389.28, 154.22 396.84, 161.88 405.82 C 169.53 414.80, 177.19 414.88, 184.84 417.16 C 192.50 419.45, 200.16 419.07, 207.81 419.53 C 215.47 419.99, 223.12 419.86, 230.78 419.93 C 238.44 420.01, 249.92 419.98, 253.75 419.99 L 253.75 420 L 70.00 420 Z" fill="#3b82f6" fill-opacity="0.07" />
  <path d="M 70.00 79.71 C 73.83 79.71, 85.31 51.35, 92.97 79.71 C 100.62 108.07, 108.28 202.59, 115.94 249.86 C 123.59 297.12, 131.25 337.29, 138.91 363.29 C 146.56 389.28, 154.22 396.84, 161.88 405.82 C 169.53 414.80, 177.19 414.88, 184.84 417.16 C 192.50 419.45, 200.16 419.07, 207.81 419.53 C 215.47 419.99, 223.12 419.86, 230.78 419.93 C 238.44 420.01, 249.92 419.98, 253.75 419.99" fill="none" stroke="#3b82f6" stroke-width="2.2" />
  <circle cx="70.00" cy="79.71" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="92.97" cy="79.71" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="115.94" cy="249.86" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="138.91" cy="363.29" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="161.88" cy="405.82" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="184.84" cy="417.16" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="207.81" cy="419.53" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="230.78" cy="419.93" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="253.75" cy="419.99" r="3.8" fill="#3b82f6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <line x1="70.00" y1="420" x2="70.00" y2="403.06" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="92.97" y1="420" x2="92.97" y2="352.23" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="115.94" y1="420" x2="115.94" y2="284.46" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="138.91" y1="420" x2="138.91" y2="239.29" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="161.88" y1="420" x2="161.88" y2="239.29" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="184.84" y1="420" x2="184.84" y2="275.43" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="207.81" y1="420" x2="207.81" y2="323.62" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="230.78" y1="420" x2="230.78" y2="364.93" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="253.75" y1="420" x2="253.75" y2="392.46" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="276.72" y1="420" x2="276.72" y2="407.76" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="299.69" y1="420" x2="299.69" y2="415.10" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="322.66" y1="420" x2="322.66" y2="418.22" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="345.62" y1="420" x2="345.62" y2="419.41" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="368.59" y1="420" x2="368.59" y2="419.82" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="391.56" y1="420" x2="391.56" y2="419.95" stroke="#10b981" stroke-width="1.2" stroke-opacity="0.35" />
  <path d="M 70.00 403.06 C 73.83 394.59, 85.31 372.00, 92.97 352.23 C 100.62 332.47, 108.28 303.29, 115.94 284.46 C 123.59 265.64, 131.25 246.82, 138.91 239.29 C 146.56 231.76, 154.22 233.26, 161.88 239.29 C 169.53 245.31, 177.19 261.37, 184.84 275.43 C 192.50 289.48, 200.16 308.70, 207.81 323.62 C 215.47 338.54, 223.12 353.45, 230.78 364.93 C 238.44 376.40, 246.09 385.32, 253.75 392.46 C 261.41 399.60, 269.06 403.99, 276.72 407.76 C 284.38 411.53, 292.03 413.36, 299.69 415.10 C 307.34 416.85, 315.00 417.50, 322.66 418.22 C 330.31 418.94, 337.97 419.14, 345.62 419.41 C 353.28 419.67, 360.94 419.73, 368.59 419.82 C 376.25 419.91, 387.73 419.93, 391.56 419.95 L 391.56 420 L 70.00 420 Z" fill="#10b981" fill-opacity="0.07" />
  <path d="M 70.00 403.06 C 73.83 394.59, 85.31 372.00, 92.97 352.23 C 100.62 332.47, 108.28 303.29, 115.94 284.46 C 123.59 265.64, 131.25 246.82, 138.91 239.29 C 146.56 231.76, 154.22 233.26, 161.88 239.29 C 169.53 245.31, 177.19 261.37, 184.84 275.43 C 192.50 289.48, 200.16 308.70, 207.81 323.62 C 215.47 338.54, 223.12 353.45, 230.78 364.93 C 238.44 376.40, 246.09 385.32, 253.75 392.46 C 261.41 399.60, 269.06 403.99, 276.72 407.76 C 284.38 411.53, 292.03 413.36, 299.69 415.10 C 307.34 416.85, 315.00 417.50, 322.66 418.22 C 330.31 418.94, 337.97 419.14, 345.62 419.41 C 353.28 419.67, 360.94 419.73, 368.59 419.82 C 376.25 419.91, 387.73 419.93, 391.56 419.95" fill="none" stroke="#10b981" stroke-width="2.2" />
  <circle cx="70.00" cy="403.06" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="92.97" cy="352.23" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="115.94" cy="284.46" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="138.91" cy="239.29" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="161.88" cy="239.29" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="184.84" cy="275.43" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="207.81" cy="323.62" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="230.78" cy="364.93" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="253.75" cy="392.46" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="276.72" cy="407.76" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="299.69" cy="415.10" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="322.66" cy="418.22" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="345.62" cy="419.41" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="368.59" cy="419.82" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="391.56" cy="419.95" r="3.8" fill="#10b981" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <line x1="92.97" y1="420" x2="92.97" y2="419.58" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="115.94" y1="420" x2="115.94" y2="417.90" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="138.91" y1="420" x2="138.91" y2="413.00" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="161.88" y1="420" x2="161.88" y2="402.50" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="184.84" y1="420" x2="184.84" y2="385.00" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="207.81" y1="420" x2="207.81" y2="361.67" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="230.78" y1="420" x2="230.78" y2="336.68" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="253.75" y1="420" x2="253.75" y2="315.85" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="276.72" y1="420" x2="276.72" y2="304.27" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="299.69" y1="420" x2="299.69" y2="304.27" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="322.66" y1="420" x2="322.66" y2="314.79" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="345.62" y1="420" x2="345.62" y2="332.33" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="368.59" y1="420" x2="368.59" y2="352.56" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="391.56" y1="420" x2="391.56" y2="371.83" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="414.53" y1="420" x2="414.53" y2="387.89" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="437.50" y1="420" x2="437.50" y2="399.93" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="460.47" y1="420" x2="460.47" y2="408.19" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="483.44" y1="420" x2="483.44" y2="413.44" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="506.41" y1="420" x2="506.41" y2="416.55" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="529.38" y1="420" x2="529.38" y2="418.27" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="552.34" y1="420" x2="552.34" y2="419.18" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="575.31" y1="420" x2="575.31" y2="419.63" stroke="#f59e0b" stroke-width="1.2" stroke-opacity="0.35" />
  <path d="M 92.97 419.58 C 96.80 419.30, 108.28 419.00, 115.94 417.90 C 123.59 416.80, 131.25 415.57, 138.91 413.00 C 146.56 410.43, 154.22 407.17, 161.88 402.50 C 169.53 397.84, 177.19 391.81, 184.84 385.00 C 192.50 378.20, 200.16 369.73, 207.81 361.67 C 215.47 353.62, 223.12 344.31, 230.78 336.68 C 238.44 329.04, 246.09 321.25, 253.75 315.85 C 261.41 310.45, 269.06 306.20, 276.72 304.27 C 284.38 302.34, 292.03 302.52, 299.69 304.27 C 307.34 306.03, 315.00 310.12, 322.66 314.79 C 330.31 319.47, 337.97 326.03, 345.62 332.33 C 353.28 338.62, 360.94 345.98, 368.59 352.56 C 376.25 359.14, 383.91 365.94, 391.56 371.83 C 399.22 377.72, 406.88 383.20, 414.53 387.89 C 422.19 392.57, 429.84 396.54, 437.50 399.93 C 445.16 403.31, 452.81 405.94, 460.47 408.19 C 468.12 410.45, 475.78 412.05, 483.44 413.44 C 491.09 414.83, 498.75 415.74, 506.41 416.55 C 514.06 417.35, 521.72 417.84, 529.38 418.27 C 537.03 418.71, 544.69 418.95, 552.34 419.18 C 560.00 419.40, 571.48 419.55, 575.31 419.63 L 575.31 420 L 92.97 420 Z" fill="#f59e0b" fill-opacity="0.07" />
  <path d="M 92.97 419.58 C 96.80 419.30, 108.28 419.00, 115.94 417.90 C 123.59 416.80, 131.25 415.57, 138.91 413.00 C 146.56 410.43, 154.22 407.17, 161.88 402.50 C 169.53 397.84, 177.19 391.81, 184.84 385.00 C 192.50 378.20, 200.16 369.73, 207.81 361.67 C 215.47 353.62, 223.12 344.31, 230.78 336.68 C 238.44 329.04, 246.09 321.25, 253.75 315.85 C 261.41 310.45, 269.06 306.20, 276.72 304.27 C 284.38 302.34, 292.03 302.52, 299.69 304.27 C 307.34 306.03, 315.00 310.12, 322.66 314.79 C 330.31 319.47, 337.97 326.03, 345.62 332.33 C 353.28 338.62, 360.94 345.98, 368.59 352.56 C 376.25 359.14, 383.91 365.94, 391.56 371.83 C 399.22 377.72, 406.88 383.20, 414.53 387.89 C 422.19 392.57, 429.84 396.54, 437.50 399.93 C 445.16 403.31, 452.81 405.94, 460.47 408.19 C 468.12 410.45, 475.78 412.05, 483.44 413.44 C 491.09 414.83, 498.75 415.74, 506.41 416.55 C 514.06 417.35, 521.72 417.84, 529.38 418.27 C 537.03 418.71, 544.69 418.95, 552.34 419.18 C 560.00 419.40, 571.48 419.55, 575.31 419.63" fill="none" stroke="#f59e0b" stroke-width="2.2" />
  <circle cx="92.97" cy="419.58" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="115.94" cy="417.90" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="138.91" cy="413.00" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="161.88" cy="402.50" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="184.84" cy="385.00" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="207.81" cy="361.67" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="230.78" cy="336.68" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="253.75" cy="315.85" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="276.72" cy="304.27" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="299.69" cy="304.27" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="322.66" cy="314.79" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="345.62" cy="332.33" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="368.59" cy="352.56" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="391.56" cy="371.83" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="414.53" cy="387.89" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="437.50" cy="399.93" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="460.47" cy="408.19" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="483.44" cy="413.44" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="506.41" cy="416.55" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="529.38" cy="418.27" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="552.34" cy="419.18" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="575.31" cy="419.63" r="3.8" fill="#f59e0b" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <line x1="230.78" y1="420" x2="230.78" y2="419.52" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="253.75" y1="420" x2="253.75" y2="418.79" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="276.72" y1="420" x2="276.72" y2="417.31" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="299.69" y1="420" x2="299.69" y2="414.62" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="322.66" y1="420" x2="322.66" y2="410.22" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="345.62" y1="420" x2="345.62" y2="403.70" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="368.59" y1="420" x2="368.59" y2="394.92" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="391.56" y1="420" x2="391.56" y2="384.17" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="414.53" y1="420" x2="414.53" y2="372.22" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="437.50" y1="420" x2="437.50" y2="360.28" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="460.47" y1="420" x2="460.47" y2="349.74" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="483.44" y1="420" x2="483.44" y2="341.94" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="506.41" y1="420" x2="506.41" y2="337.83" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="529.38" y1="420" x2="529.38" y2="337.83" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="552.34" y1="420" x2="552.34" y2="341.74" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="575.31" y1="420" x2="575.31" y2="348.85" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="598.28" y1="420" x2="598.28" y2="358.13" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="621.25" y1="420" x2="621.25" y2="368.45" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="644.22" y1="420" x2="644.22" y2="378.76" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="667.19" y1="420" x2="667.19" y2="388.27" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="690.16" y1="420" x2="690.16" y2="396.50" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="713.12" y1="420" x2="713.12" y2="403.21" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="736.09" y1="420" x2="736.09" y2="408.42" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="759.06" y1="420" x2="759.06" y2="412.28" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="782.03" y1="420" x2="782.03" y2="415.02" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <line x1="805.00" y1="420" x2="805.00" y2="416.89" stroke="#8b5cf6" stroke-width="1.2" stroke-opacity="0.35" />
  <path d="M 230.78 419.52 C 234.61 419.39, 246.09 419.16, 253.75 418.79 C 261.41 418.42, 269.06 418.00, 276.72 417.31 C 284.38 416.62, 292.03 415.80, 299.69 414.62 C 307.34 413.44, 315.00 412.04, 322.66 410.22 C 330.31 408.40, 337.97 406.25, 345.62 403.70 C 353.28 401.15, 360.94 398.17, 368.59 394.92 C 376.25 391.66, 383.91 387.95, 391.56 384.17 C 399.22 380.39, 406.88 376.21, 414.53 372.22 C 422.19 368.24, 429.84 364.03, 437.50 360.28 C 445.16 356.53, 452.81 352.80, 460.47 349.74 C 468.12 346.68, 475.78 343.92, 483.44 341.94 C 491.09 339.95, 498.75 338.51, 506.41 337.83 C 514.06 337.14, 521.72 337.18, 529.38 337.83 C 537.03 338.48, 544.69 339.90, 552.34 341.74 C 560.00 343.58, 567.66 346.12, 575.31 348.85 C 582.97 351.59, 590.62 354.87, 598.28 358.13 C 605.94 361.40, 613.59 365.01, 621.25 368.45 C 628.91 371.88, 636.56 375.45, 644.22 378.76 C 651.88 382.06, 659.53 385.32, 667.19 388.27 C 674.84 391.23, 682.50 394.01, 690.16 396.50 C 697.81 398.99, 705.47 401.23, 713.12 403.21 C 720.78 405.20, 728.44 406.91, 736.09 408.42 C 743.75 409.93, 751.41 411.18, 759.06 412.28 C 766.72 413.38, 774.38 414.25, 782.03 415.02 C 789.69 415.79, 801.17 416.58, 805.00 416.89 L 805.00 420 L 230.78 420 Z" fill="#8b5cf6" fill-opacity="0.07" />
  <path d="M 230.78 419.52 C 234.61 419.39, 246.09 419.16, 253.75 418.79 C 261.41 418.42, 269.06 418.00, 276.72 417.31 C 284.38 416.62, 292.03 415.80, 299.69 414.62 C 307.34 413.44, 315.00 412.04, 322.66 410.22 C 330.31 408.40, 337.97 406.25, 345.62 403.70 C 353.28 401.15, 360.94 398.17, 368.59 394.92 C 376.25 391.66, 383.91 387.95, 391.56 384.17 C 399.22 380.39, 406.88 376.21, 414.53 372.22 C 422.19 368.24, 429.84 364.03, 437.50 360.28 C 445.16 356.53, 452.81 352.80, 460.47 349.74 C 468.12 346.68, 475.78 343.92, 483.44 341.94 C 491.09 339.95, 498.75 338.51, 506.41 337.83 C 514.06 337.14, 521.72 337.18, 529.38 337.83 C 537.03 338.48, 544.69 339.90, 552.34 341.74 C 560.00 343.58, 567.66 346.12, 575.31 348.85 C 582.97 351.59, 590.62 354.87, 598.28 358.13 C 605.94 361.40, 613.59 365.01, 621.25 368.45 C 628.91 371.88, 636.56 375.45, 644.22 378.76 C 651.88 382.06, 659.53 385.32, 667.19 388.27 C 674.84 391.23, 682.50 394.01, 690.16 396.50 C 697.81 398.99, 705.47 401.23, 713.12 403.21 C 720.78 405.20, 728.44 406.91, 736.09 408.42 C 743.75 409.93, 751.41 411.18, 759.06 412.28 C 766.72 413.38, 774.38 414.25, 782.03 415.02 C 789.69 415.79, 801.17 416.58, 805.00 416.89" fill="none" stroke="#8b5cf6" stroke-width="2.2" />
  <circle cx="230.78" cy="419.52" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="253.75" cy="418.79" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="276.72" cy="417.31" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="299.69" cy="414.62" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="322.66" cy="410.22" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="345.62" cy="403.70" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="368.59" cy="394.92" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="391.56" cy="384.17" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="414.53" cy="372.22" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="437.50" cy="360.28" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="460.47" cy="349.74" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="483.44" cy="341.94" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="506.41" cy="337.83" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="529.38" cy="337.83" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="552.34" cy="341.74" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="575.31" cy="348.85" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="598.28" cy="358.13" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="621.25" cy="368.45" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="644.22" cy="378.76" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="667.19" cy="388.27" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="690.16" cy="396.50" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="713.12" cy="403.21" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="736.09" cy="408.42" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="759.06" cy="412.28" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="782.03" cy="415.02" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <circle cx="805.00" cy="416.89" r="3.8" fill="#8b5cf6" stroke="currentColor" stroke-opacity="0.1" stroke-width="1" />
  <line x1="92.97" y1="79.71151691641586" x2="92.97" y2="420" stroke="#3b82f6" stroke-width="1.4" stroke-dasharray="4,3" stroke-opacity="0.7" />
  <text x="92.97" y="71.71" text-anchor="middle" fill="#3b82f6" class="p-annot">μ=1</text>
  <line x1="161.88" y1="239.2856962978228" x2="161.88" y2="420" stroke="#10b981" stroke-width="1.4" stroke-dasharray="4,3" stroke-opacity="0.7" />
  <text x="161.88" y="231.29" text-anchor="middle" fill="#10b981" class="p-annot">μ=4</text>
  <line x1="299.69" y1="304.2732169579517" x2="299.69" y2="420" stroke="#f59e0b" stroke-width="1.4" stroke-dasharray="4,3" stroke-opacity="0.7" />
  <text x="299.69" y="296.27" text-anchor="middle" fill="#f59e0b" class="p-annot">μ=10</text>
  <line x1="529.38" y1="337.8273314123212" x2="529.38" y2="420" stroke="#8b5cf6" stroke-width="1.4" stroke-dasharray="4,3" stroke-opacity="0.7" />
  <text x="529.38" y="329.83" text-anchor="middle" fill="#8b5cf6" class="p-annot">μ=20</text>
</svg>
</figure>

#### Why They Converge (The Central Limit Theorem)

1. **Poisson Additivity:** An arrival process of rate $$\lambda$$ over time $$T$$ is mathematically identical to the sum of $$m$$ independent sub-windows, each with arrival rate $$\frac{\lambda}{m}$$:

   $$
   X = \sum_{i=1}^{m} X_i, \quad X_i \sim \operatorname{Pois}\left(\frac{\lambda}{m}\right)
   $$

2. **Central Limit Theorem:** Because $$X$$ is the sum of independent and identically distributed increments, the Central Limit Theorem guarantees convergence to a Gaussian distribution as $$\lambda \to \infty$$:

   $$
   \frac{X - \lambda}{\sqrt{\lambda}} \xrightarrow{d} \mathcal{N}(0, 1) \implies \operatorname{Pois}(\lambda) \xrightarrow{d} \mathcal{N}(\mu = \lambda, \, \sigma^2 = \lambda)
   $$

3. **Vanishing Skewness:** The third standardized moment (skewness) of the Poisson distribution is:

   $$
   \gamma_1 = \frac{1}{\sqrt{\lambda}}
   $$

   At $$\lambda = 1$$, skewness is $$1.0$$ (heavily lopsided). By $$\lambda = 20$$, skewness drops to $$\frac{1}{\sqrt{20}} \approx 0.22$$, rendering the distribution virtually indistinguishable from a symmetric bell curve.

4. **Variance Diffusion:** Because $$\operatorname{Var}(X) = \lambda$$, the standard deviation expands as $$\sigma = \sqrt{\lambda}$$. Since the total discrete probability mass must sum to $$1$$, this lateral spreading forces the peak probability downward ($$0.37$$ at $$\lambda=1$$ down to $$0.09$$ at $$\lambda=20$$).

---

#### Key Differences: Poisson vs. Normal

| Dimension | Poisson Distribution | Normal (Gaussian) Distribution |
| :--- | :--- | :--- |
| **Domain** | **Discrete counts:** $$k \in \{0, 1, 2, \dots\}$$ | **Continuous measurements:** $$x \in (-\infty, +\infty)$$ |
| **Physical Meaning** | Counts indivisible events (packets, orders, clicks). You cannot have $$2.4$$ arrivals. | Continuous physical quantities (time, price returns, voltage, temperature). |
| **Left Boundary** | **Hard zero floor:** Negative occurrences are impossible ($$\mathbb{P}(k < 0) = 0$$). | **Infinite negative tail:** Extends to $$-\infty$$. |
| **Degrees of Freedom** | **1 parameter ($$\lambda$$):** Variance is strictly locked to the mean ($$\sigma^2 = \mu = \lambda$$). | **2 independent parameters ($$\mu, \sigma^2$$):** Spread can vary independently of center. |

> **Practical Rule of Thumb:** When $$\lambda < 10$$, never approximate with a Normal distribution; the zero floor causes severe distortions. When $$\lambda \ge 20$$, the Gaussian approximation is extremely accurate because the mean sits more than $$4.4\sigma$$ away from zero, making negative probabilities negligible ($$< 0.0004\%$$).

---

### 4. Summary

| Property | Value | Interpretation |
| :--- | :--- | :--- |
| **Support** | $$k \in \{0, 1, 2, \dots\}$$ | Discrete count of occurrences. |
| **Expected Count** | $$\mu = \lambda T$$ | Expected events in observation window $$T$$. |
| **PMF** | $$\frac{\mu^k e^{-\mu}}{k!}$$ | Law of rare events in the limit of infinitesimal slices. |
| **Mean & Variance** | $$\mathbb{E}[K] = \operatorname{Var}(K) = \mu$$ | Hallmark of purely uncorrelated random arrivals ($$F = 1$$). |
