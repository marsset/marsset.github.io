---
title:  "Murphy Decomposition"
date:  2026-11-04 06:30:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
excerpt: >
  how the Brier score splits into uncertainty, resolution, and calibration—and why Bernoulli variance p(1-p) plays the role of Shannon entropy under squared error.
---

When evaluating a probabilistic forecast $$q \in [0, 1]$$ for a binary outcome $$Y \in \{0, 1\}$$, log loss leads to Shannon entropy and KL divergence:

$$
H(p \parallel q) = \underbrace{H(p)}_{\text{uncertainty}} + \underbrace{D_{\mathrm{KL}}(p \parallel q)}_{\text{divergence}} .
$$

If we replace logarithmic loss with **squared error**—the **Brier score** $$(Y - q)^2$$—the exact same geometry reappears in quadratic form. The role of Shannon entropy $$H(p)$$ is taken by $$p(1 - p)$$, the **variance of the Bernoulli distribution**, and across a set of forecasts the score splits into three pieces via the **Murphy decomposition** (1973): **uncertainty**, **resolution**, and **calibration**.

---

### 1. Bernoulli Variance $$p(1 - p)$$ and Single-Probability Brier Score

Let $$Y \sim \mathrm{Bernoulli}(p)$$ be a binary random variable with $$\mathbb{P}(Y = 1) = p$$ and $$\mathbb{P}(Y = 0) = 1 - p$$. Its expectation is $$\mathbb{E}[Y] = p$$, and since $$Y^2 = Y$$ for $$Y \in \{0, 1\}$$, its variance is

$$
\begin{align*}
\operatorname{Var}(Y) &= \mathbb{E}\big[(Y - p)^2\big] = \mathbb{E}[Y^2] - (\mathbb{E}[Y])^2 \\[4pt]
&= p - p^2 \;=\; p(1 - p) . \tag{1}
\end{align*}
$$

Now suppose a forecaster quotes probability $$q \in [0, 1]$$ while nature draws $$Y \sim \mathrm{Bernoulli}(p)$$. Add and subtract the true probability $$p$$ inside the Brier score $$(Y - q)^2$$:

$$
\begin{align*}
\mathbb{E}_p\big[(Y - q)^2\big] &= \mathbb{E}_p\big[\big((Y - p) + (p - q)\big)^2\big] \\[4pt]
&= \mathbb{E}_p\big[(Y - p)^2\big] + 2(p - q)\underbrace{\mathbb{E}_p[Y - p]}_{=\,0} + (p - q)^2 \\[4pt]
&= \underbrace{p(1 - p)}_{\text{Bernoulli variance}} + \underbrace{(p - q)^2}_{\text{squared error}} . \tag{2}
\end{align*}
$$

Equation (2) is the quadratic twin of $$H(p \parallel q) = H(p) + D_{\mathrm{KL}}(p \parallel q)$$:

- **$$(p - q)^2 \ge 0$$** is the penalty for quoting the wrong probability $$q \neq p$$. It vanishes if and only if $$q = p$$ (showing that the Brier score is a **strictly proper scoring rule**).
- **$$p(1 - p)$$** is the **irreducible uncertainty** of the outcome itself—the variance of $$\mathrm{Bernoulli}(p)$$. Even an oracle that knows the exact probability $$q = p$$ still suffers an expected Brier score of $$p(1 - p)$$, because the realization $$Y$$ must land on $$0$$ or $$1$$.

---

### 2. Comparing $$p(1 - p)$$ and Binary Shannon Entropy

Both the Bernoulli variance $$\operatorname{Var}(Y) = p(1 - p)$$ and the binary Shannon entropy

$$
H(p) = -p \log_2 p - (1 - p) \log_2 (1 - p)
$$

measure the intrinsic unpredictability of a $$\mathrm{Bernoulli}(p)$$ trial:

- **Zero at certainty ($$p = 0$$ and $$p = 1$$):** When the coin is two-headed or two-tailed, there is no randomness left: $$p(1 - p) = 0$$ and $$H(p) = 0$$.
- **Symmetric and strictly concave on $$[0, 1]$$:** Flipping labels $$p \mapsto 1 - p$$ leaves both unchanged, and mixing two probabilities always increases uncertainty.
- **Peak at a fair coin ($$p = 1/2$$):** At $$p = 1/2$$, Shannon entropy reaches its maximum $$H(1/2) = 1\text{ bit}$$, while Bernoulli variance reaches $$\operatorname{Var}(Y) = \frac{1}{2}\big(1 - \frac{1}{2}\big) = 0.25$$ (and its normalized form $$4p(1 - p)$$ reaches $$1$$).

In fact, expanding $$H(p)$$ in a Taylor series around $$p = 1/2$$ (setting $$p = \frac{1}{2} + \delta$$) gives

$$
H\!\left(\tfrac{1}{2} + \delta\right) = 1 - \frac{2}{\ln 2}\,\delta^2 - O(\delta^4) , \qquad 4p(1 - p) = 1 - 4\delta^2 ,
$$

so $$p(1 - p)$$ is the leading quadratic polynomial approximation to Shannon entropy (which is why CART decision trees use Gini impurity $$2p(1 - p)$$ as a fast, logarithm-free substitute for entropy).

<svg viewBox="0 0 680 296" width="100%" style="max-width:680px;display:block;margin:1.5em auto;" role="img" aria-label="Comparison of binary Shannon entropy H(p), normalized Bernoulli variance 4p(1-p), and Bernoulli variance Var(Y) = p(1-p) for p in [0, 1]">
  <!-- Grid lines -->
  <line x1="68" y1="28" x2="508" y2="28" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="83" x2="508" y2="83" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="138" x2="508" y2="138" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="193" x2="508" y2="193" stroke="currentColor" stroke-opacity="0.18" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="288" y1="28" x2="288" y2="248" stroke="currentColor" stroke-opacity="0.18" stroke-width="1" stroke-dasharray="3,3"/>

  <!-- Axes -->
  <line x1="68" y1="248" x2="518" y2="248" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <line x1="68" y1="248" x2="68" y2="18" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>

  <!-- Y-axis ticks & labels -->
  <text x="58" y="252" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0</text>
  <text x="58" y="197" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.25</text>
  <text x="58" y="142" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.50</text>
  <text x="58" y="87" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.75</text>
  <text x="58" y="32" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">1.00</text>

  <!-- X-axis ticks & labels -->
  <line x1="68" y1="248" x2="68" y2="253" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="68" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">0</text>

  <line x1="178" y1="248" x2="178" y2="253" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="178" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.25</text>

  <line x1="288" y1="248" x2="288" y2="253" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="288" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.50</text>

  <line x1="398" y1="248" x2="398" y2="253" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="398" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.75</text>

  <line x1="508" y1="248" x2="508" y2="253" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <text x="508" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">1</text>

  <text x="288" y="288" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.8">Bernoulli parameter p = P(Y = 1)</text>

  <!-- 1. Shannon Entropy H(p) = -p log2(p) - (1-p) log2(1-p) -->
  <path d="M68.0,248.0 L72.4,230.2 L76.8,216.9 L81.2,205.2 L85.6,194.7 L90.0,185.0 L94.4,176.0 L98.8,167.5 L103.2,159.5 L107.6,152.0 L112.0,144.8 L116.4,138.0 L120.8,131.5 L125.2,125.4 L129.6,119.5 L134.0,113.8 L138.4,108.5 L142.8,103.3 L147.2,98.4 L151.6,93.7 L156.0,89.2 L160.4,84.9 L164.8,80.8 L169.2,76.8 L173.6,73.1 L178.0,69.5 L182.4,66.1 L186.8,62.9 L191.2,59.8 L195.6,56.9 L200.0,54.1 L204.4,51.5 L208.8,49.0 L213.2,46.7 L217.6,44.5 L222.0,42.5 L226.4,40.6 L230.8,38.9 L235.2,37.2 L239.6,35.7 L244.0,34.4 L248.4,33.2 L252.8,32.1 L257.2,31.1 L261.6,30.3 L266.0,29.6 L270.4,29.0 L274.8,28.6 L279.2,28.3 L283.6,28.1 L288.0,28.0 L292.4,28.1 L296.8,28.3 L301.2,28.6 L305.6,29.0 L310.0,29.6 L314.4,30.3 L318.8,31.1 L323.2,32.1 L327.6,33.2 L332.0,34.4 L336.4,35.7 L340.8,37.2 L345.2,38.9 L349.6,40.6 L354.0,42.5 L358.4,44.5 L362.8,46.7 L367.2,49.0 L371.6,51.5 L376.0,54.1 L380.4,56.9 L384.8,59.8 L389.2,62.9 L393.6,66.1 L398.0,69.5 L402.4,73.1 L406.8,76.8 L411.2,80.8 L415.6,84.9 L420.0,89.2 L424.4,93.7 L428.8,98.4 L433.2,103.3 L437.6,108.5 L442.0,113.8 L446.4,119.5 L450.8,125.4 L455.2,131.5 L459.6,138.0 L464.0,144.8 L468.4,152.0 L472.8,159.5 L477.2,167.5 L481.6,176.0 L486.0,185.0 L490.4,194.7 L494.8,205.2 L499.2,216.9 L503.6,230.2 L508.0,248.0" fill="none" stroke="currentColor" stroke-opacity="0.9" stroke-width="2"/>

  <!-- 2. Normalized Bernoulli variance 4p(1-p) -->
  <path d="M68,248 Q288,-192 508,248" fill="none" stroke="currentColor" stroke-opacity="0.65" stroke-width="1.8" stroke-dasharray="6,4"/>

  <!-- 3. Bernoulli variance Var(Y) = p(1-p) -->
  <path d="M68,248 Q288,138 508,248" fill="none" stroke="#2563eb" stroke-opacity="0.85" stroke-width="2"/>

  <!-- Peak markers at p = 0.5 -->
  <circle cx="288" cy="28" r="3" fill="currentColor" fill-opacity="0.9"/>
  <circle cx="288" cy="193" r="3" fill="#2563eb" fill-opacity="0.9"/>

  <!-- Direct curve annotations on the right -->
  <line x1="524" y1="62" x2="552" y2="62" stroke="currentColor" stroke-opacity="0.9" stroke-width="2"/>
  <text x="560" y="66" text-anchor="start" font-size="12" fill="currentColor" fill-opacity="0.9">H(p) (Shannon)</text>

  <line x1="524" y1="102" x2="552" y2="102" stroke="currentColor" stroke-opacity="0.65" stroke-width="1.8" stroke-dasharray="6,4"/>
  <text x="560" y="106" text-anchor="start" font-size="12" fill="currentColor" fill-opacity="0.75">4p(1 − p) (scaled)</text>

  <line x1="524" y1="193" x2="552" y2="193" stroke="#2563eb" stroke-opacity="0.85" stroke-width="2"/>
  <text x="560" y="190" text-anchor="start" font-size="12" fill="#2563eb" fill-opacity="0.95">p(1 − p) = Var(Y)</text>
  <text x="560" y="206" text-anchor="start" font-size="10.5" fill="currentColor" fill-opacity="0.55">peak = 0.25 at p = 0.5</text>
</svg>

---

### 3. The Murphy Decomposition

Equation (2) evaluated a single forecast $$q$$ against a single fixed probability $$p$$. In practice, a model issues varying forecasts $$Q \in [0, 1]$$ across different instances (weather days, credit applicants, market ticks), and on each instance nature reveals a binary outcome $$Y \in \{0, 1\}$$.

Two conditional probabilities govern the system:

- **The overall base rate (climatology):** $$p = \mathbb{P}(Y = 1) = \mathbb{E}[Y]$$.
- **The true calibrated rate given the forecast:** $$\pi_Q = \mathbb{P}(Y = 1 \mid Q) = \mathbb{E}[Y \mid Q]$$, the actual fraction of times $$Y = 1$$ among all instances where the model predicted $$Q$$.

#### Intuition: What $$\pi_Q$$ Means by Grouping into "Forecast Buckets"

Suppose a weather model predicts rain ($$Y = 1$$) vs. no rain ($$Y = 0$$) over $$100$$ days, and only ever outputs two numbers: either $$Q = 0.80$$ ("80% chance of rain") or $$Q = 0.20$$ ("20% chance of rain"). If we group all $$100$$ days into two buckets based on the number $$Q$$ the model announced and count how often it actually rained in each bucket:

| Forecast Bucket ($$Q$$) | Days Predicted ($$n_k$$) | Days It Actually Rained ($$Y = 1$$) | True Conditional Rate $$\pi_Q = \mathbb{P}(Y = 1 \mid Q)$$ |
| :--- | :--- | :--- | :--- |
| **Bucket 1:** $$Q = 0.80$$ | $$40$$ days | $$24$$ days | $$\pi_{0.80} = \frac{24}{40} = \mathbf{0.60}$$ (60%) |
| **Bucket 2:** $$Q = 0.20$$ | $$60$$ days | $$12$$ days | $$\pi_{0.20} = \frac{12}{60} = \mathbf{0.20}$$ (20%) |
| **Total (All Days)** | $$100$$ days | $$36$$ days | Base rate $$p = \frac{36}{100} = \mathbf{0.36}$$ (36%) |

- **$$Q$$ vs. $$\pi_Q$$:** $$Q$$ is what the model *claims* the probability is, whereas $$\pi_Q$$ is what *actually happens* when the model makes that claim.
  - On the $$40$$ days the model announced $$Q = 0.80$$, it only rained $$24$$ times, so $$\pi_{0.80} = 0.60$$. Because $$Q = 0.80 \neq \pi_{0.80} = 0.60$$, this bucket is **overconfident (miscalibrated)**—if you simply relabeled the model's `"0.80"` output to `"0.60"`, that bucket would become perfectly calibrated.
  - On the $$60$$ days the model announced $$Q = 0.20$$, it rained $$12$$ times, so $$\pi_{0.20} = 0.20$$. Here $$Q = \pi_Q$$, so this bucket is **perfectly calibrated**.
- **Why $$\mathbb{P}(Y = 1 \mid Q) = \mathbb{E}[Y \mid Q]$$:** Because $$Y$$ only takes values $$0$$ or $$1$$, the average value of $$Y$$ inside a bucket is identical to the fraction of $$1$$s in that bucket:

  $$
  \mathbb{E}[Y \mid Q = 0.80] = \frac{24 \times 1 + 16 \times 0}{40} = \frac{24}{40} = 0.60 = \mathbb{P}(Y = 1 \mid Q = 0.80) .
  $$

#### Deriving the Decomposition

Condition on the forecast $$Q$$ and apply Equation (2) with $$\pi_Q$$ as the true conditional probability:

$$
\mathbb{E}\big[(Y - Q)^2 \;\big|\; Q\big] = \pi_Q(1 - \pi_Q) + (Q - \pi_Q)^2 .
$$

Taking the expectation over $$Q$$ yields

$$
\mathbb{E}\big[(Y - Q)^2\big] = \mathbb{E}\big[\pi_Q(1 - \pi_Q)\big] + \mathbb{E}\big[(Q - \pi_Q)^2\big] . \tag{3}
$$

Meanwhile, by the law of total variance applied to $$Y \in \{0, 1\}$$,

$$
\underbrace{\operatorname{Var}(Y)}_{p(1 - p)} = \mathbb{E}\big[\operatorname{Var}(Y \mid Q)\big] + \operatorname{Var}\big(\mathbb{E}[Y \mid Q]\big) = \mathbb{E}\big[\pi_Q(1 - \pi_Q)\big] + \operatorname{Var}(\pi_Q) ,
$$

so $$\mathbb{E}\big[\pi_Q(1 - \pi_Q)\big] = p(1 - p) - \operatorname{Var}(\pi_Q)$$. Substituting this into (3) gives the **Murphy decomposition**:

$$
\operatorname{BS} = \mathbb{E}\big[(Y - Q)^2\big] = \underbrace{p(1 - p)}_{\text{Uncertainty (UNC)}} - \underbrace{\operatorname{Var}(\pi_Q)}_{\text{Resolution (RES)}} + \underbrace{\mathbb{E}\big[(Q - \pi_Q)^2\big]}_{\text{Calibration / Reliability (REL)}} . \tag{4}
$$

When the forecaster chooses from $$K$$ discrete probability bins $$f_1, \dots, f_K$$, where bin $$k$$ is predicted $$n_k$$ times out of $$N$$ with empirical event rate $$\bar{y}_k$$ and overall base rate $$\bar{y} = \frac{1}{N}\sum_{i=1}^N y_i$$, Equation (4) takes Allan Murphy's classic 1973 sample form:

$$
\frac{1}{N} \sum_{i=1}^{N} (q_i - y_i)^2 = \underbrace{\bar{y}(1 - \bar{y})}_{\text{Uncertainty}} - \underbrace{\frac{1}{N} \sum_{k=1}^{K} n_k (\bar{y}_k - \bar{y})^2}_{\text{Resolution}} + \underbrace{\frac{1}{N} \sum_{k=1}^{K} n_k (f_k - \bar{y}_k)^2}_{\text{Calibration (Reliability)}} . \tag{5}
$$

---

### 4. What Each Term Means

1. **Uncertainty ($$\mathrm{UNC} = p(1 - p)$$) — The Environment:**
   The marginal variance of $$Y \sim \mathrm{Bernoulli}(p)$$, which depends **only on the outcomes $$Y$$ and not on the model**. It is the Brier score achieved by a trivial forecaster that always predicts the base rate $$Q = p$$.
2. **Resolution ($$\mathrm{RES} = \operatorname{Var}(\pi_Q)$$) — Information Gain (Subtracted):**
   How strongly the true event rate $$\pi_Q$$ moves away from the base rate $$p$$ across different forecast buckets. A constant forecast $$Q = p$$ has $$\pi_Q = p$$ everywhere, so $$\mathrm{RES} = 0$$. A sharp model that sorts instances into bins where $$\pi_Q$$ is near $$0$$ or near $$1$$ achieves $$\operatorname{Var}(\pi_Q) \to p(1 - p)$$, canceling out the environment's uncertainty. Notice that $$\mathrm{UNC} - \mathrm{RES} = \mathbb{E}[\pi_Q(1 - \pi_Q)]$$ is the quadratic analogue of conditional entropy $$H(Y \mid Q) = H(Y) - I(Y; Q)$$, with **Resolution playing the exact role of Mutual Information $$I(Y; Q)$$**.
3. **Calibration / Reliability ($$\mathrm{REL} = \mathbb{E}[(Q - \pi_Q)^2]$$) — Honesty (Added):**
   The squared gap between the number $$Q$$ the model quotes and the true empirical frequency $$\pi_Q$$ when $$Q$$ is quoted. Even a model with high resolution is penalized if its labels are miscalibrated (for example, predicting $$0.80$$ on a bucket that actually occurs $$60\%$$ of the time).

| Log Loss / Information Theory | Brier Score / Murphy Decomposition | Meaning |
| :--- | :--- | :--- |
| **Loss operator** $$-\log(\cdot)$$ | **Loss operator** $$(\cdot)^2$$ | Single-trial loss: $$-Y\log Q - (1-Y)\log(1-Q)$$ vs. $$(Y - Q)^2$$ |
| **Expected Log Loss (Cross-Entropy)** $$\mathbb{E}_Q[H(\pi_Q \parallel Q)]$$ | **Brier Score** $$\mathrm{BS} = \mathbb{E}[(Y - Q)^2]$$ | Total loss $$= \mathrm{UNC} - \mathrm{RES} + \mathrm{REL}$$ |
| Marginal entropy $$H(Y)$$ | **Uncertainty** $$\mathrm{UNC} = p(1 - p)$$ | Irreducible randomness of $$\mathrm{Bernoulli}(p)$$ |
| Mutual information $$I(Y; Q)$$ | **Resolution** $$\mathrm{RES} = \operatorname{Var}(\pi_Q)$$ | Uncertainty removed by conditioning on $$Q$$ |
| Conditional entropy $$H(Y \mid Q)$$ | $$\mathrm{UNC} - \mathrm{RES} = \mathbb{E}[\pi_Q(1 - \pi_Q)]$$ | Remaining uncertainty after knowing $$Q$$ |
| Expected KL $$\mathbb{E}_Q[D_{\mathrm{KL}}(\pi_Q \parallel Q)]$$ | **Calibration** $$\mathrm{REL} = \mathbb{E}[(Q - \pi_Q)^2]$$ | Penalty for miscalibrated probability labels |

#### Numerical Walk-Through on the 100-Day Weather Example

Applying Equation (5) to the two forecast buckets from Section 3 ($$p = 0.36$$, with $$40\%$$ of days in Bucket 1 where $$Q = 0.80, \pi_{0.80} = 0.60$$ and $$60\%$$ of days in Bucket 2 where $$Q = 0.20, \pi_{0.20} = 0.20$$):

- **Uncertainty ($$p(1 - p)$$):**

  $$
  \mathrm{UNC} = 0.36 \times (1 - 0.36) = 0.2304 .
  $$

- **Resolution ($$\operatorname{Var}(\pi_Q) = \mathbb{E}[(\pi_Q - p)^2]$$):** How far the bucket actual rates ($$0.60$$ and $$0.20$$) separate from the overall base rate ($$0.36$$):

  $$
  \mathrm{RES} = \frac{40}{100}(0.60 - 0.36)^2 + \frac{60}{100}(0.20 - 0.36)^2 = 0.40(0.0576) + 0.60(0.0256) = 0.0384 .
  $$

- **Calibration ($$\mathbb{E}[(Q - \pi_Q)^2]$$):** How far the quoted forecast $$Q$$ is from its bucket's actual rate $$\pi_Q$$:

  $$
  \mathrm{REL} = \frac{40}{100}(0.80 - 0.60)^2 + \frac{60}{100}(0.20 - 0.20)^2 = 0.40(0.04) + 0 = 0.0160 .
  $$

- **Total Brier Score:**

  $$
  \mathrm{BS} = \mathrm{UNC} - \mathrm{RES} + \mathrm{REL} = 0.2304 - 0.0384 + 0.0160 = 0.2080 .
  $$

---

### 5. How to Choose Between Brier Score and Log Loss

Both Brier Score and Log Loss are **strictly proper scoring rules** (both are uniquely minimized when $$Q = \pi_Q$$), so they agree on what the ideal forecast is. However, they behave very differently in the tails ($$Q \to 0$$ or $$1$$), in finite samples, and during gradient-based training.

#### When to Prefer Brier Score / Murphy Decomposition

1. **Boundedness and Robustness to Outliers ($$[0, 1]$$ vs. $$\infty$$):**
   On a single instance, Brier Score is bounded in $$[0, 1]$$: even if a model predicts $$Q = 1.00$$ and a "black swan" or mislabeled data point produces $$Y = 0$$, the penalty is at most $$(0 - 1)^2 = 1$$. Under Log Loss, a single $$Q = 1, Y = 0$$ event incurs $$-\log(0) = +\infty$$, blowing up the dataset average unless probabilities are arbitrarily clipped to $$[\epsilon, 1 - \epsilon]$$.
2. **Direct Percentage-Point Calibration & $$R^2$$ Interpretation:**
   In Murphy's decomposition, $$\sqrt{\mathrm{REL}} = \sqrt{\mathbb{E}[(Q - \pi_Q)^2]}$$ measures calibration error directly in probability percentage points, and normalizing by $$\mathrm{UNC} = p(1 - p)$$ yields the **Brier Skill Score ($$\mathrm{BSS}$$)**—the binary classification analogue of $$R^2$$ (fraction of variance explained):

   $$
   \mathrm{BSS} = 1 - \frac{\mathrm{BS}}{\mathrm{UNC}} = \frac{\mathrm{RES} - \mathrm{REL}}{p(1 - p)} .
   $$

3. **Zero-Count Finite-Sample Bins:**
   In empirical bucket tables (Equation 5), bins where $$f_k = 0$$ or $$\bar{y}_k = 0$$ require no smoothing or $$0 \log 0$$ conventions.
4. **Linear Dollar Payoffs:**
   When forecasts price linear payoffs (such as $$\$1$$ binary contracts), quadratic error matches the variance of dollar PnL.

#### When to Prefer Log Loss (Cross-Entropy)

1. **Rare Events and Tail Sensitivity ($$p \ll 1$$):**
   Suppose an event occurs $$0.1\%$$ of the time ($$p = 0.001$$), and Model A predicts $$Q = 0.001$$ while Model B predicts $$Q = 0.01$$ (off by $$10\times$$). When $$Y = 1$$, Brier Score barely distinguishes them: $$(1 - 0.001)^2 = 0.9980$$ vs. $$(1 - 0.01)^2 = 0.9801$$. Log Loss penalizes orders of magnitude in the tails ($$-\ln(0.001) = 6.91$$ vs. $$-\ln(0.01) = 4.61$$), making it essential for rare-event tasks (click-through rates, fraud detection, rare disease screening).
2. **Gradient-Based Model Training (Logits & Sigmoids):**
   For a model outputting logit $$z$$ with $$Q = \sigma(z) = (1 + e^{-z})^{-1}$$, the gradients with respect to $$z$$ are:

   $$
   \frac{\partial \, \ell_{\log}}{\partial z} = Q - Y , \qquad
   \frac{\partial \, \ell_{\mathrm{BS}}}{\partial z} = 2(Q - Y)\,Q(1 - Q) .
   $$

   Under Brier Score, a saturated wrong prediction ($$Q \approx 0.99$$ when $$Y = 0$$) is multiplied by $$Q(1 - Q) \approx 0.01$$, causing **vanishing gradients**. Log Loss cancels the sigmoid derivative $$Q(1 - Q)$$ so the gradient scales linearly with $$Q - Y$$.
3. **Maximum Likelihood & Kelly Utility:**
   Minimizing Log Loss is equivalent to **Maximum Likelihood Estimation (MLE)** and maximizes expected log-wealth growth.

| Dimension | Brier Score / Murphy Decomposition | Log Loss / Cross-Entropy |
| :--- | :--- | :--- |
| **Core operator (single trial)** | **Square** $$(\cdot)^2 \;\longrightarrow\; (Y - Q)^2$$ | **Negative log** $$-\log(\cdot) \;\longrightarrow\; -\log P_Y(Q)$$ |
| **Range on a single trial** | Bounded $$\in [0, 1]$$ | Unbounded $$\in [0, \infty]$$ |
| **Single $$Q = 1, Y = 0$$ error** | Penalty $$= 1$$ (robust to outliers) | Penalty $$= \infty$$ (requires clipping) |
| **Sensitivity to rare events ($$10^{-4}$$ vs. $$10^{-2}$$)** | **Weak** (dominated by midrange $$p \in [0.1, 0.9]$$) | **Strong** (separates orders of magnitude) |
| **Logit gradient $$\partial L / \partial z$$** | $$2(Q - Y)\,Q(1 - Q)$$ (saturates near $$0, 1$$) | $$Q - Y$$ (non-vanishing) |
| **Natural geometry** | **Variance / $$R^2$$** & percentage-point error | **Information (bits/nats)** & MLE |
| **Best used for** | **Post-hoc evaluation**, calibration diagnostics, weather/macro/market verification | **Model training** (neural nets, logistic regression) & **rare-event** ranking |

---

### 6. Why Polymarket's Taker Fee Rate Is Also $$p(1 - p)$$

In Polymarket's order book, the taker fee for trading $$C$$ shares of a binary contract at price $$p \in (0, 1)$$ is not a flat percentage of dollar notional $$C \cdot p$$. Instead, it is proportional to the Bernoulli variance $$p(1 - p)$$:

$$
\mathrm{Fee}(C, p) = C \cdot \gamma \cdot p(1 - p) , \tag{6}
$$

where $$\gamma$$ is the base fee rate (for example, $$\gamma = 0.072$$ in crypto markets). Why must a binary prediction market scale its fee by $$p(1 - p)$$?

1. **Complement Symmetry (YES at $$p$$ $$\equiv$$ NO at $$1 - p$$):**
   In a binary market, a YES share and a NO share sum to $$\$1.00$$ of collateral ($$\text{YES} + \text{NO} = 1$$). Buying 1 share of YES at $$p = 0.99$$ (risking $$\$0.99$$ to make $$\$0.01$$) is the exact same economic trade as selling 1 share of NO at $$1 - p = 0.01$$.
   - If the exchange charged a standard notional fee $$\gamma \cdot p$$, buying YES at $$0.99$$ would cost $$99\times$$ more than buying NO at $$0.01$$, and for $$\gamma = 0.072$$ the fee ($$\$0.071$$) would be **seven times larger than the maximum possible $$\$0.01$$ profit**, making high-probability contracts untradable.
   - To treat YES and NO identically, the per-share fee $$f(p)$$ must be symmetric under $$p \mapsto 1 - p$$ and vanish at both endpoints $$p \in \{0, 1\}$$. The unique lowest-degree polynomial with $$f(p) = f(1 - p)$$ and $$f(0) = f(1) = 0$$ is $$f(p) = \gamma \, p(1 - p)$$.

2. **A Constant Fraction of Potential Profit (and Deducted Shares):**
   Dividing Equation (6) by the dollar cost $$C \cdot p$$ of a buy order reveals what the fee actually taxes:

   $$
   \frac{\mathrm{Fee}(C, p)}{C \cdot p} = \gamma(1 - p) , \qquad \mathrm{Fee}_{\text{shares}} = \frac{\mathrm{Fee}(C, p)}{p} = C \cdot \gamma(1 - p) .
   $$

   On a buy at price $$p$$, each share costs $$p$$ and has a potential net profit of $$1 - p$$ if the event resolves to $$1$$. Charging $$\gamma \, p(1 - p)$$ in dollars per share is equivalent to taxing a **fixed fraction $$\gamma$$ of the buyer's potential upside $$1 - p$$** (or deducting $$\gamma(1 - p)$$ shares per share bought). At $$p = 0.99$$, where only $$\$0.01$$ of upside remains, the fee automatically shrinks to $$\gamma \times 0.99 \times 0.01 \approx 0.01\gamma$$, so it never exceeds the remaining edge.

3. **Scaling with Outcome Variance $$\operatorname{Var}(Y) = p(1 - p)$$:**
   From a market-making perspective, a binary contract is a claim on $$Y \sim \mathrm{Bernoulli}(p)$$. At $$p = 0.50$$, outcome variance $$\operatorname{Var}(Y) = p(1 - p) = 0.25$$ and adverse selection risk are at their peak, and the per-share fee reaches its maximum $$0.25\gamma$$ ($$1.8\text{¢}$$ per share at $$\gamma = 0.072$$). As $$p \to 0$$ or $$p \to 1$$, the contract approaches certainty, the variance $$p(1 - p)$$ collapses toward zero, and the taker fee decays at the exact same quadratic rate.

---

### 7. Empirical Case Study: Polymarket 5-Minute BTC Up-Down Contracts

To see the Murphy decomposition at work on real market data, we analyze **$$7,030$$ resolved 5-minute BTC Up-Down rounds** on Polymarket (30 trading days, $$N = 69,746$$ orderbook snapshots sampled across $$t \in \{15\text{s}, 30\text{s}, 60\text{s}, 90\text{s}, 120\text{s}, 150\text{s}, 180\text{s}, 210\text{s}, 240\text{s}, 270\text{s}\}$$ within each $$300\text{s}$$ window; see <a href="{{ '/assets/code/murphy_btc_5m/' | relative_url }}" target="_blank" rel="noopener">murphy_btc_5m.py</a> for the analysis script).

For each snapshot, the market's implied forecast is the UP token mid-price

$$
Q_{\text{poly}}(t) = \frac{\text{upBid}(t) + \text{upAsk}(t)}{2} \in [0, 1] ,
$$

and the binary outcome is $$Y = 1$$ if BTC closes the 5-minute window Up and $$Y = 0$$ if Down.

#### 1. Base Rate $$p$$ and Maximum Environmental Uncertainty $$\mathrm{UNC}$$

Out of $$7,030$$ rounds, BTC resolved Up $$3,471$$ times and Down $$3,559$$ times:

$$
p = \mathbb{P}(Y = 1) = \frac{3,471}{7,030} = \mathbf{0.4937} , \qquad
\mathrm{UNC} = p(1 - p) = 0.4937 \times 0.5063 = \mathbf{0.24996} \approx \mathbf{0.2500} .
$$

Because 5-minute BTC direction over a month is almost a fair coin flip ($$p \approx 0.50$$), the environment sits right at the **peak of the Bernoulli variance parabola** ($$\mathrm{UNC} = 0.25$$).

#### 2. Pooled 10-Bucket Calibration Table ($$Q_{\text{poly}}$$ vs. $$\pi_Q$$)

Pooling all $$N = 69,746$$ snapshots into $$K = 10$$ decile buckets of $$Q_{\text{poly}}$$ gives:

- **Uncertainty ($$\mathrm{UNC}$$):** $$0.2500$$
- **Resolution ($$\mathrm{RES} = \operatorname{Var}(\pi_Q)$$):** $$0.1053$$ (removes $$42.1\%$$ of total outcome variance on average across the round)
- **Calibration ($$\mathrm{REL} = \mathbb{E}[(Q - \pi_Q)^2]$$):** $$\mathbf{0.00011}$$ (root-mean-square calibration error $$\sqrt{\mathrm{REL}} \approx 1.05\text{¢}$$, or **$$1$$ percentage point**)
- **Total Brier Score ($$\mathrm{BS} = \mathrm{UNC} - \mathrm{RES} + \mathrm{REL}$$):** $$0.2500 - 0.1053 + 0.00011 = \mathbf{0.1448}$$ (Brier Skill Score $$\mathrm{BSS} = 42.1\%$$)

| Price Bucket $$Q_{\text{poly}}$$ | Snapshots $$n_k$$ (Share) | Mean Quoted $$Q$$ ($$f_k$$) | Actual Win Rate $$\pi_Q$$ ($$\bar{y}_k$$) | Calibration Gap $$Q - \pi_Q$$ |
| :--- | :--- | :--- | :--- | :--- |
| $$[0.0, 0.1)$$ | $$11,290$$ ($$16.2\%$$) | $$0.0277$$ | $$0.0223$$ | $$+0.0054$$ *(overpriced)* |
| $$[0.1, 0.2)$$ | $$4,687$$ ($$6.7\%$$) | $$0.1498$$ | $$0.1237$$ | $$+0.0261$$ *(overpriced)* |
| $$[0.2, 0.3)$$ | $$5,190$$ ($$7.4\%$$) | $$0.2522$$ | $$0.2443$$ | $$+0.0079$$ *(overpriced)* |
| $$[0.3, 0.4)$$ | $$6,112$$ ($$8.8\%$$) | $$0.3508$$ | $$0.3411$$ | $$+0.0096$$ *(overpriced)* |
| $$[0.4, 0.5)$$ | $$6,903$$ ($$9.9\%$$) | $$0.4516$$ | $$0.4321$$ | $$+0.0195$$ *(overpriced)* |
| $$[0.5, 0.6)$$ | $$8,542$$ ($$12.2\%$$) | $$0.5403$$ | $$0.5416$$ | $$-0.0013$$ |
| $$[0.6, 0.7)$$ | $$6,162$$ ($$8.8\%$$) | $$0.6480$$ | $$0.6480$$ | $$+0.0000$$ *(exact)* |
| $$[0.7, 0.8)$$ | $$5,193$$ ($$7.4\%$$) | $$0.7494$$ | $$0.7483$$ | $$+0.0011$$ |
| $$[0.8, 0.9)$$ | $$4,567$$ ($$6.5\%$$) | $$0.8498$$ | $$0.8572$$ | $$-0.0074$$ *(underpriced)* |
| $$[0.9, 1.0]$$ | $$11,100$$ ($$15.9\%$$) | $$0.9724$$ | $$0.9772$$ | $$-0.0048$$ *(underpriced)* |

Notice the subtle **favorite–longshot bias** revealed by $$Q - \pi_Q$$—and why **it does not create a standalone tradable edge**:
- **Mid-Price Bias:** In buckets below $$0.50$$, the quoted mid-price $$Q$$ is slightly higher than the empirical win rate $$\pi_Q$$ ($$Q - \pi_Q > 0$$), while in buckets above $$0.80$$, $$Q$$ is slightly lower than $$\pi_Q$$ ($$Q - \pi_Q < 0$$).
- **No Unconditional Edge After Spread and Fees:** Because $$Q = (\text{upBid} + \text{upAsk})/2$$ is a mid-price rather than an executable quote, betting against an "overpriced" bucket requires crossing the **half-spread** ($$\approx 0.5\text{¢}$$, since the minimum tick size is $$1\text{¢}$$) plus paying the **Polymarket taker fee** $$\gamma \, Q(1 - Q)$$ from Section 6 (which adds another $$0.2\text{¢}\text{–}1.8\text{¢}$$). Together, the half-spread and taker fee form a $$0.7\text{¢}\text{–}2.4\text{¢}$$ **no-arbitrage band** around $$\pi_Q$$ that absorbs the calibration gap (and posting passively as a maker only gets filled conditionally when BTC moves adversely).

#### 3. Evolution Across the 5-Minute Window ($$t = 15\text{s} \to 270\text{s}$$)

Computing the Murphy decomposition separately at each timestamp $$t$$ inside the $$300\text{s}$$ window shows why separating $$\mathrm{UNC}$$, $$\mathrm{RES}$$, and $$\mathrm{REL}$$ is so much more informative than looking at raw Brier Score alone:

| Elapsed $$t$$ (Remaining $$\tau$$) | Uncertainty $$\mathrm{UNC}$$ | Resolution $$\mathrm{RES}(t)$$ | Calibration $$\mathrm{REL}(t)$$ | Brier Score $$\mathrm{BS}(t)$$ | Skill $$\mathrm{BSS}(t)$$ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| $$t = 15\text{s}$$ ($$\tau = 285\text{s}$$) | $$0.2500$$ | $$0.0208$$ | $$0.00031$$ | $$0.2294$$ | $$8.2\%$$ |
| $$t = 30\text{s}$$ ($$\tau = 270\text{s}$$) | $$0.2500$$ | $$0.0309$$ | $$0.00034$$ | $$0.2194$$ | $$12.2\%$$ |
| $$t = 60\text{s}$$ ($$\tau = 240\text{s}$$) | $$0.2500$$ | $$0.0469$$ | $$0.00044$$ | $$0.2035$$ | $$18.6\%$$ |
| $$t = 90\text{s}$$ ($$\tau = 210\text{s}$$) | $$0.2500$$ | $$0.0651$$ | $$0.00031$$ | $$0.1851$$ | $$25.9\%$$ |
| $$t = 120\text{s}$$ ($$\tau = 180\text{s}$$) | $$0.2500$$ | $$0.0832$$ | $$0.00026$$ | $$0.1671$$ | $$33.2\%$$ |
| $$t = 150\text{s}$$ ($$\tau = 150\text{s}$$) | $$0.2500$$ | $$0.1058$$ | $$0.00033$$ | $$0.1445$$ | $$42.2\%$$ |
| $$t = 180\text{s}$$ ($$\tau = 120\text{s}$$) | $$0.2500$$ | $$0.1292$$ | $$0.00025$$ | $$0.1210$$ | $$51.6\%$$ |
| $$t = 210\text{s}$$ ($$\tau = 90\text{s}$$) | $$0.2500$$ | $$0.1582$$ | $$0.00029$$ | $$0.0920$$ | $$63.2\%$$ |
| $$t = 240\text{s}$$ ($$\tau = 60\text{s}$$) | $$0.2500$$ | $$0.1922$$ | $$0.00068$$ | $$0.0584$$ | $$76.6\%$$ |
| $$t = 270\text{s}$$ ($$\tau = 30\text{s}$$) | $$0.2500$$ | $$0.2292$$ | $$0.00024$$ | $$0.0210$$ | $$91.6\%$$ |

<svg viewBox="0 0 680 296" width="100%" style="max-width:680px;display:block;margin:1.5em auto;" role="img" aria-label="Murphy decomposition components across the 300-second BTC 5-minute window: Uncertainty stays constant at 0.25, Calibration stays near 0, Resolution climbs from 0.021 to 0.229, and Brier Score falls from 0.229 to 0.021">
  <!-- Horizontal grid lines (y from 0 to 0.25) -->
  <line x1="68" y1="28" x2="508" y2="28" stroke="currentColor" stroke-opacity="0.18" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="72" x2="508" y2="72" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="116" x2="508" y2="116" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="160" x2="508" y2="160" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="68" y1="204" x2="508" y2="204" stroke="currentColor" stroke-opacity="0.12" stroke-width="1" stroke-dasharray="3,3"/>

  <!-- Axes -->
  <line x1="68" y1="248" x2="518" y2="248" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>
  <line x1="68" y1="248" x2="68" y2="18" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.2"/>

  <!-- Y-axis ticks & labels -->
  <text x="58" y="252" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.00</text>
  <text x="58" y="208" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.05</text>
  <text x="58" y="164" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.10</text>
  <text x="58" y="120" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.15</text>
  <text x="58" y="76" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.20</text>
  <text x="58" y="32" text-anchor="end" font-size="11.5" fill="currentColor" fill-opacity="0.65">0.25</text>

  <!-- X-axis ticks & labels (t = 0s .. 300s) -->
  <text x="68" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">0s</text>
  <text x="156" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">60s</text>
  <text x="244" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">120s</text>
  <text x="332" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">180s</text>
  <text x="420" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">240s</text>
  <text x="508" y="268" text-anchor="middle" font-size="11.5" fill="currentColor" fill-opacity="0.65">300s</text>
  <text x="288" y="288" text-anchor="middle" font-size="12.5" fill="currentColor" fill-opacity="0.8">Elapsed time t inside 5-minute BTC round</text>

  <!-- 1. Uncertainty UNC = 0.2500 (flat dashed line) -->
  <line x1="90" y1="28" x2="464" y2="28" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.6" stroke-dasharray="5,4"/>

  <!-- 2. Resolution RES(t) rising from 0.0208 to 0.2292 -->
  <polyline points="90,229.7 112,220.8 156,206.7 200,190.7 244,174.8 288,154.9 332,134.3 376,108.8 420,78.9 464,46.3" fill="none" stroke="#16a34a" stroke-opacity="0.9" stroke-width="2.2"/>

  <!-- 3. Brier Score BS(t) = UNC - RES(t) + REL(t) falling from 0.2294 to 0.0210 -->
  <polyline points="90,46.1 112,54.9 156,68.9 200,85.1 244,101.0 288,120.8 332,141.5 376,167.0 420,196.6 464,229.5" fill="none" stroke="#2563eb" stroke-opacity="0.9" stroke-width="2.2"/>

  <!-- 4. Calibration REL(t) ~ 0.0003 hugging 0 -->
  <polyline points="90,247.7 112,247.7 156,247.6 200,247.7 244,247.8 288,247.7 332,247.8 376,247.7 420,247.4 464,247.8" fill="none" stroke="#dc2626" stroke-opacity="0.85" stroke-width="2"/>

  <!-- Legend / Right annotations -->
  <line x1="520" y1="28" x2="546" y2="28" stroke="currentColor" stroke-opacity="0.6" stroke-width="1.6" stroke-dasharray="5,4"/>
  <text x="552" y="32" text-anchor="start" font-size="11.5" fill="currentColor" fill-opacity="0.8">UNC = 0.250</text>

  <line x1="520" y1="62" x2="546" y2="62" stroke="#16a34a" stroke-opacity="0.9" stroke-width="2.2"/>
  <text x="552" y="66" text-anchor="start" font-size="11.5" fill="#16a34a" fill-opacity="0.95">RES(t) ↑ (info)</text>

  <line x1="520" y1="96" x2="546" y2="96" stroke="#2563eb" stroke-opacity="0.9" stroke-width="2.2"/>
  <text x="552" y="100" text-anchor="start" font-size="11.5" fill="#2563eb" fill-opacity="0.95">BS(t) ↓ (error)</text>

  <line x1="520" y1="244" x2="546" y2="244" stroke="#dc2626" stroke-opacity="0.85" stroke-width="2"/>
  <text x="552" y="247" text-anchor="start" font-size="11.5" fill="#dc2626" fill-opacity="0.95">REL(t) ≈ 0.0003</text>
</svg>

Three insights stand out from the time-in-round decomposition:

1. **Why Raw Brier Score Alone Is Misleading Early in the Round:**
   At $$t = 15\text{s}$$, the market's Brier Score is $$0.2294$$—barely better than guessing $$0.50$$ ($$0.2500$$). Looking only at $$\mathrm{BS}$$ might suggest the market is poorly calibrated early in the round. Murphy's decomposition proves the opposite: **calibration error $$\mathrm{REL}(15\text{s}) = 0.00031$$ is already near zero**. The score is high at $$t = 15\text{s}$$ solely because $$95\%$$ of BTC's 5-minute Brownian path has not happened yet, bounding the achievable **Resolution** at $$\mathrm{RES}(15\text{s}) = 0.0208$$.
2. **Pure Information Filtration ($$\mathrm{RES}(t) \uparrow \implies \mathrm{BS}(t) \downarrow$$):**
   Because $$\mathrm{UNC} \equiv 0.2500$$ is constant and $$\mathrm{REL}(t) \approx 0.0003$$ is negligible at every timestamp, $$\mathrm{BS}(t) \approx 0.2500 - \mathrm{RES}(t)$$. The green $$\mathrm{RES}(t)$$ curve and blue $$\mathrm{BS}(t)$$ curve are exact mirror images across $$0.125$$, directly measuring how the filtration of BTC spot price reveals information from $$8.2\%$$ of total variance at $$t = 15\text{s}$$ to $$91.6\%$$ at $$t = 270\text{s}$$.
3. **Market-Making Efficiency ($$\mathrm{REL} \ll \mathrm{RES}$$):**
   Across the entire dataset, $$\mathrm{REL} = 0.00011$$ is **three orders of magnitude smaller** than $$\mathrm{RES} = 0.1053$$—meaning Polymarket's order book extracts almost the full theoretical Brier Skill Score available at each second of the 5-minute window.

### References

1. A. H. Murphy, "A New Vector Partition of the Probability Score," *Journal of Applied Meteorology*, vol. 12, no. 4, pp. 595–600, 1973. [PDF](https://journals.ametsoc.org/downloadpdf/journals/apme/12/4/1520-0450_1973_012_0595_anvpot_2_0_co_2.pdf).
2. G. W. Brier, "Verification of Forecasts Expressed in Terms of Probability," *Monthly Weather Review*, vol. 78, no. 1, pp. 1–3, 1950. [PDF](https://journals.ametsoc.org/downloadpdf/journals/mwre/78/1/1520-0493_1950_078_0001_vofeit_2_0_co_2.pdf).
3. Polymarket Documentation, ["Trading Fees"](https://docs.polymarket.com/trading/fees), `fee = C * feeRate * p * (1 - p)`.
