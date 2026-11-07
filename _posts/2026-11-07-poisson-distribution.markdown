---
title:  "Poisson Distribution: From Rare Events to Counting Processes"
date:   2026-11-07 14:00:00 +0800
categories:
  - math
tags: [math, probability, stochastic-processes]
classes: wide
layout: single
use_math: true
excerpt: >
  A first-principles derivation of the Poisson distribution from the binomial limit, moment generating functions, waiting times, and counting processes.
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
* Success (an event occurs) with probability $$p = \frac{\mu}{n}$$.
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

### 3. Characteristic Function & Additivity

The characteristic function of a Poisson random variable is:

$$
\varphi_K(t) = \mathbb{E}\left[ e^{itK} \right] = \sum_{k=0}^{\infty} e^{itk} \frac{\lambda^k e^{-\lambda}}{k!} = e^{-\lambda} \sum_{k=0}^{\infty} \frac{(\lambda e^{it})^k}{k!}
$$

Evaluating the sum:

$$
\varphi_K(t) = e^{-\lambda} \cdot e^{\lambda e^{it}} = \exp\left( \lambda (e^{it} - 1) \right)
$$

This algebraic form provides an immediate proof of **Poisson additivity**:

If $$X \sim \operatorname{Pois}(\lambda_1)$$ and $$Y \sim \operatorname{Pois}(\lambda_2)$$ are independent random variables, the characteristic function of their sum is the product of their individual functions:

$$
\varphi_{X+Y}(t) = \varphi_X(t) \cdot \varphi_Y(t) = \exp\left( \lambda_1(e^{it} - 1) \right) \cdot \exp\left( \lambda_2(e^{it} - 1) \right) = \exp\left( (\lambda_1 + \lambda_2)(e^{it} - 1) \right)
$$

By the uniqueness theorem of characteristic functions:

$$
X + Y \sim \operatorname{Pois}(\lambda_1 + \lambda_2)
$$

Independent Poisson streams aggregate into another Poisson stream whose intensity is simply the sum of individual arrival rates.

---

### 4. The Continuous-Time Dual: The Exponential Waiting Time

The Poisson distribution counts how many events occur in fixed time. What about the continuous time you must wait between events?

Let $$T_1$$ denote the time until the very first event occurs.

The statement $$T_1 > t$$ means that **zero events** occurred in the interval $$[0, t]$$:

$$
\mathbb{P}(T_1 > t) = \mathbb{P}(K = 0 \text{ in } [0, t]) = \frac{(\lambda t)^0 e^{-\lambda t}}{0!} = e^{-\lambda t}
$$

The cumulative distribution function (CDF) of the waiting time is:

$$
F_{T_1}(t) = \mathbb{P}(T_1 \le t) = 1 - e^{-\lambda t} \qquad (t \ge 0)
$$

Differentiating gives the probability density function (PDF):

$$
f_{T_1}(t) = \lambda e^{-\lambda t}
$$

The waiting time between Poisson arrivals follows an **Exponential distribution** with mean $$\mathbb{E}[T_1] = \frac{1}{\lambda}$$.

#### Memorylessness
The exponential waiting time satisfies the memoryless property:

$$
\mathbb{P}(T_1 > s + t \mid T_1 > s) = \frac{\mathbb{P}(T_1 > s + t)}{\mathbb{P}(T_1 > s)} = \frac{e^{-\lambda(s + t)}}{e^{-\lambda s}} = e^{-\lambda t} = \mathbb{P}(T_1 > t)
$$

No matter how long you have already waited for an event to happen, the probability distribution of the remaining time until the next arrival is identical to the day you started waiting.

---

### 5. Summary: Discrete Counts and Continuous Time

| Property | Value | Interpretation |
| :--- | :--- | :--- |
| **Support** | $$k \in \{0, 1, 2, \dots\}$$ | Discrete count of occurrences. |
| **Parameter** | $$\lambda > 0$$ | Mean arrival rate per unit time. |
| **PMF** | $$\frac{\lambda^k e^{-\lambda}}{k!}$$ | Law of rare events in the limit of small intervals. |
| **Mean & Variance** | $$\mathbb{E}[K] = \operatorname{Var}(K) = \lambda$$ | Hallmark of purely uncorrelated random arrivals. |
| **Inter-Arrival Time** | $$\operatorname{Exp}(\lambda)$$ | Continuous, memoryless waiting time between consecutive events. |
| **Sum of Streams** | $$\sum \lambda_i$$ | Independent Poisson sources aggregate additively. |
