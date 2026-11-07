---
title:  "Probability Formulas Cheatsheet"
date:  2026-11-04 12:18:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
excerpt: >
  a compact quick-reference cheatsheet of core probability identities: conditioning, tower property, total variance, covariance, generating functions, and tail inequalities.
---

### 1. Events & Conditioning

| Name | Formula |
| :--- | :--- |
| **Inclusion–Exclusion** | $$\mathbb{P}(A \cup B) = \mathbb{P}(A) + \mathbb{P}(B) - \mathbb{P}(A \cap B)$$ |
| **Conditional Probability** | $$\mathbb{P}(A \mid B) = \dfrac{\mathbb{P}(A \cap B)}{\mathbb{P}(B)}$$ |
| **Chain Rule** | $$\mathbb{P}(A_1 \cap \cdots \cap A_n) = \mathbb{P}(A_1)\,\mathbb{P}(A_2 \mid A_1)\cdots \mathbb{P}(A_n \mid A_1 \cap \cdots \cap A_{n-1})$$ |
| **Law of Total Probability** | $$\mathbb{P}(A) = \sum_{i} \mathbb{P}(A \mid B_i)\,\mathbb{P}(B_i)$$ |
| **Bayes' Theorem** | $$\mathbb{P}(B_i \mid A) = \dfrac{\mathbb{P}(A \mid B_i)\,\mathbb{P}(B_i)}{\sum_{j} \mathbb{P}(A \mid B_j)\,\mathbb{P}(B_j)}$$ |

---

### 2. Expectation & Tower Laws

| Name | Formula |
| :--- | :--- |
| **Linearity of Expectation** | $$\mathbb{E}[aX + bY + c] = a\,\mathbb{E}[X] + b\,\mathbb{E}[Y] + c$$ |
| **LOTUS (Discrete / Continuous)** | $$\mathbb{E}[g(X)] = \sum_{x} g(x)\,p_X(x) = \int_{-\infty}^{\infty} g(x)\,f_X(x)\,dx$$ |
| **Tail-Sum Formula ($$X \ge 0$$)** | $$\mathbb{E}[X] = \int_{0}^{\infty} \mathbb{P}(X > t)\,dt \quad\Big(\text{discrete: } \sum_{k=1}^{\infty} \mathbb{P}(X \ge k)\Big)$$ |
| **Tower Property (Law of Total Expectation)** | $$\mathbb{E}[Y] = \mathbb{E}\big[\mathbb{E}[Y \mid X]\big]$$ |
| **Nested Tower Property** | $$\mathbb{E}\big[\mathbb{E}[Y \mid X, Z] \;\mid\; X\big] = \mathbb{E}[Y \mid X]$$ |
| **Taking Out What Is Known** | $$\mathbb{E}[h(X)\,Y \mid X] = h(X)\,\mathbb{E}[Y \mid X]$$ |
| **Independence Product** | $$X \perp Y \;\Longrightarrow\; \mathbb{E}[XY] = \mathbb{E}[X]\,\mathbb{E}[Y]$$ |

---

### 3. Variance, Covariance & Total Variance

| Name | Formula |
| :--- | :--- |
| **Variance Identity** | $$\operatorname{Var}(X) = \mathbb{E}\big[(X - \mathbb{E}[X])^2\big] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$$ |
| **Scaling & Shift** | $$\operatorname{Var}(aX + b) = a^2\operatorname{Var}(X)$$ |
| **Covariance Identity** | $$\operatorname{Cov}(X, Y) = \mathbb{E}\big[(X - \mathbb{E}[X])(Y - \mathbb{E}[Y])\big] = \mathbb{E}[XY] - \mathbb{E}[X]\,\mathbb{E}[Y]$$ |
| **Correlation** | $$\rho(X, Y) = \dfrac{\operatorname{Cov}(X, Y)}{\sqrt{\operatorname{Var}(X)\operatorname{Var}(Y)}} \in [-1, 1]$$ |
| **Variance of a Sum** | $$\operatorname{Var}(X + Y) = \operatorname{Var}(X) + \operatorname{Var}(Y) + 2\operatorname{Cov}(X, Y)$$ |
| **Variance of a Linear Combination** | $$\operatorname{Var}\!\left(\sum_{i=1}^n X_i\right) = \sum_{i=1}^n \operatorname{Var}(X_i) + 2\sum_{i < j} \operatorname{Cov}(X_i, X_j)$$ |
| **Bilinearity of Covariance** | $$\operatorname{Cov}(aX + bY, Z) = a\operatorname{Cov}(X, Z) + b\operatorname{Cov}(Y, Z)$$ |
| **Law of Total Variance (Eve's Law)** | $$\operatorname{Var}(Y) = \mathbb{E}\big[\operatorname{Var}(Y \mid X)\big] + \operatorname{Var}\big(\mathbb{E}[Y \mid X]\big)$$ |
| **Law of Total Covariance** | $$\operatorname{Cov}(X, Y) = \mathbb{E}\big[\operatorname{Cov}(X, Y \mid Z)\big] + \operatorname{Cov}\big(\mathbb{E}[X \mid Z],\, \mathbb{E}[Y \mid Z]\big)$$ |
| **Pythagorean / MSE Decomposition** | $$\mathbb{E}\big[(Y - g(X))^2\big] = \mathbb{E}\big[\operatorname{Var}(Y \mid X)\big] + \mathbb{E}\big[(\mathbb{E}[Y \mid X] - g(X))^2\big]$$ |

---

### 4. Moment & Cumulant Generating Functions

| Name | Formula |
| :--- | :--- |
| **Moment Generating Function (MGF)** | $$M_X(t) = \mathbb{E}[e^{tX}], \qquad \mathbb{E}[X^k] = M_X^{(k)}(0)$$ |
| **MGF of Independent Sum** | $$X \perp Y \;\Longrightarrow\; M_{X+Y}(t) = M_X(t)\,M_Y(t)$$ |
| **Cumulant Generating Function (CGF)** | $$K_X(t) = \ln \mathbb{E}[e^{tX}], \qquad K_X'(0) = \mathbb{E}[X], \quad K_X''(0) = \operatorname{Var}(X)$$ |
| **Characteristic Function** | $$\varphi_X(t) = \mathbb{E}[e^{itX}]$$ |
| **Probability Generating Function (PGF)** | $$G_X(z) = \mathbb{E}[z^X], \qquad \mathbb{P}(X = k) = \dfrac{G_X^{(k)}(0)}{k!}$$ |

---

### 5. Inequalities & Concentration Bounds

| Name | Formula |
| :--- | :--- |
| **Union Bound (Boole's)** | $$\mathbb{P}\!\left(\bigcup_{i=1}^n A_i\right) \le \sum_{i=1}^n \mathbb{P}(A_i)$$ |
| **Jensen's Inequality ($$\varphi$$ convex)** | $$\varphi(\mathbb{E}[X]) \le \mathbb{E}[\varphi(X)]$$ |
| **Cauchy–Schwarz Inequality** | $$\bigl\lvert\mathbb{E}[XY]\bigr\rvert \le \sqrt{\mathbb{E}[X^2]\,\mathbb{E}[Y^2]}$$ |
| **Markov's Inequality ($$X \ge 0, a > 0$$)** | $$\mathbb{P}(X \ge a) \le \dfrac{\mathbb{E}[X]}{a}$$ |
| **Chebyshev's Inequality ($$a > 0$$)** | $$\mathbb{P}\big(\lvert X - \mathbb{E}[X]\rvert \ge a\big) \le \dfrac{\operatorname{Var}(X)}{a^2}$$ |
| **Chernoff Bound ($$t > 0$$)** | $$\mathbb{P}(X \ge a) \le \inf_{t > 0} e^{-ta}\,\mathbb{E}[e^{tX}]$$ |
| **Hoeffding's Inequality ($$X_i \in [a_i, b_i]$$ indep.)** | $$\mathbb{P}\big(S_n - \mathbb{E}[S_n] \ge t\big) \le \exp\!\left(-\dfrac{2t^2}{\sum_{i=1}^n (b_i - a_i)^2}\right)$$ |

---

### 6. Common Distributions

| Distribution | PMF / PDF | $$\mathbb{E}[X]$$ | $$\operatorname{Var}(X)$$ |
| :--- | :--- | :--- | :--- |
| **$$\mathrm{Bernoulli}(p)$$** | $$p^x(1-p)^{1-x},\; x \in \{0, 1\}$$ | $$p$$ | $$p(1 - p)$$ |
| **$$\mathrm{Binomial}(n, p)$$** | $$\binom{n}{k}p^k(1-p)^{n-k}$$ | $$np$$ | $$np(1 - p)$$ |
| **$$\mathrm{Geometric}(p)$$** (trials to 1st success) | $$(1 - p)^{k-1}p,\; k \ge 1$$ | $$\dfrac{1}{p}$$ | $$\dfrac{1 - p}{p^2}$$ |
| **$$\mathrm{Poisson}(\lambda)$$** | $$\dfrac{\lambda^k e^{-\lambda}}{k!},\; k \ge 0$$ | $$\lambda$$ | $$\lambda$$ |
| **$$\mathrm{Uniform}(a, b)$$** | $$\dfrac{1}{b - a},\; x \in [a, b]$$ | $$\dfrac{a + b}{2}$$ | $$\dfrac{(b - a)^2}{12}$$ |
| **$$\mathrm{Exponential}(\lambda)$$** | $$\lambda e^{-\lambda x},\; x \ge 0$$ | $$\dfrac{1}{\lambda}$$ | $$\dfrac{1}{\lambda^2}$$ |
| **$$\mathrm{Normal}(\mu, \sigma^2)$$** | $$\dfrac{1}{\sqrt{2\pi\sigma^2}}\exp\!\left(-\dfrac{(x-\mu)^2}{2\sigma^2}\right)$$ | $$\mu$$ | $$\sigma^2$$ |
