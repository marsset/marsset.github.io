---
title:  "Itô's Lemma"
date:  2026-10-13 09:00:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
excerpt: >
  the chain rule for Brownian motion, and the extra term that makes stochastic calculus a separate subject.
---


### The lemma

Everything below is about an **Itô process** — a quantity whose movement splits into a smooth part and a random part:

$$
\mathrm{d}X_t = \mu_t\,\mathrm{d}t + \sigma_t\,\mathrm{d}W_t .
$$

$$X_t$$ is the quantity being modelled, at time $$t$$: a price, a log price, a rate. $$\mathrm{d}X_t$$ is how much it moves over an instant, and the equation says that movement has exactly two sources.

$$W_t$$ is a **standard Brownian motion** (aka **Wiener process**) — and the only randomness in sight. It starts at $$W_0 = 0$$, has continuous paths, and its increments over disjoint intervals are independent with $$W_{t+h} - W_t \sim N(0, h)$$ — variance equal to the elapsed time. Independence is what makes that variance additive: writing $$v(h)$$ for the variance over a step of length $$h$$, splitting one step into two forces $$v(a+b) = v(a) + v(b)$$, and a non-decreasing function obeying that must be $$v(h) = ch$$. Calling the motion *standard* fixes $$c = 1$$.

$$\sigma_t$$ is the **volatility** — how much of that randomness is let through. The subscript matters: it need not be a constant, but may itself be a process, provided it is adapted, meaning its value at time $$t$$ is knowable at time $$t$$ rather than read off the future.

$$\mu_t$$ is the **drift** — the rate of the smooth, trend-like part, per unit of time. Also a process, also adapted. $$\mathrm{d}t$$ is the time increment the two are measured against.

With the symbols accounted for, the lemma itself:

> **Itô's lemma.** Let $$f(t,x)$$ be twice continuously differentiable. Then $$f(t, X_t)$$ is itself an Itô process, and
>
> $$
> \require{HTML}
> \mathrm{d}f(t, X_t) = \left( \frac{\partial f}{\partial t} + \mu_t\,\frac{\partial f}{\partial x} + \class{ito-term}{\frac12 \sigma_t^2\,\frac{\partial^2 f}{\partial x^2}} \right) \mathrm{d}t \;+\; \sigma_t\,\frac{\partial f}{\partial x}\,\mathrm{d}W_t .
> $$

### What ordinary calculus drops

The quickest way to see what the underlined term is doing is to try the problem with ordinary calculus and watch it come out wrong. The total differential of $$f(t,x)$$ is

$$
\mathrm{d}f = \frac{\partial f}{\partial t}\,\mathrm{d}t + \frac{\partial f}{\partial x}\,\mathrm{d}X_t ,
$$

and substituting $$\mathrm{d}X_t = \mu_t\,\mathrm{d}t + \sigma_t\,\mathrm{d}W_t$$ expands it to

$$
\mathrm{d}f = \frac{\partial f}{\partial t}\,\mathrm{d}t + \mu_t\,\frac{\partial f}{\partial x}\,\mathrm{d}t + \sigma_t\,\frac{\partial f}{\partial x}\,\mathrm{d}W_t .
$$

All three of those appear in the lemma unchanged. But the lemma carries a fourth — the underlined $$\tfrac12\sigma_t^2 f_{xx}\,\mathrm{d}t$$ — and nothing in this calculation produces anything resembling it. The answer is wrong, and wrong by omission rather than by error — which means the mistake is in a step that looked like it cost nothing.

That step is the first one. The total differential is not a law handed down from anywhere; it is a Taylor expansion with everything past first order discarded. Written out in full it reads

$$
\mathrm{d}f = f_t\,\mathrm{d}t + f_x\,\mathrm{d}X + \tfrac12 f_{xx}\,(\mathrm{d}X)^2 + f_{tx}\,\mathrm{d}t\,\mathrm{d}X + \tfrac12 f_{tt}\,(\mathrm{d}t)^2 + \cdots
$$

and cutting it off after two terms is legitimate only when the rest are negligible beside $$\mathrm{d}t$$.

For an Itô process they are not. Granting $$(\mathrm{d}W)^2 = \mathrm{d}t$$, which the next section establishes, each discarded term can be sized directly:

$$
(\mathrm{d}X)^2 = (\mu_t\,\mathrm{d}t + \sigma_t\,\mathrm{d}W_t)^2 = \mu_t^2\,(\mathrm{d}t)^2 + 2\mu_t\sigma_t\,\mathrm{d}t\,\mathrm{d}W_t + \sigma_t^2\,(\mathrm{d}W_t)^2 = \sigma_t^2\,\mathrm{d}t .
$$

The first two pieces are of higher order than $$\mathrm{d}t$$ and vanish; the third does not. So $$f_{tx}\,\mathrm{d}t\,\mathrm{d}X$$ and $$\tfrac12 f_{tt}(\mathrm{d}t)^2$$ may be dropped, while

$$
\tfrac12 f_{xx}\,(\mathrm{d}X)^2 = \tfrac12\,\sigma_t^2\,\frac{\partial^2 f}{\partial x^2}\,\mathrm{d}t
$$

may not. It is the fourth term.

### Why $$(\mathrm{d}W)^2 = \mathrm{d}t$$

Taken one at a time, that equation is false. The square of a single increment is still a random variable:

$$
\mathbb{E}\big[(\Delta W)^2\big] = h , \qquad \operatorname{Var}\big[(\Delta W)^2\big] = 2h^2 .
$$

Its mean is $$h$$, but it scatters around $$h$$ rather than equalling it.

What the equation says is that the scatter averages away once the squares are added up. Cut $$[0, t]$$ into $$n$$ pieces of length $$h = t/n$$. The increments are independent, so

$$
\mathbb{E}\Big[\sum_{i=1}^{n}(\Delta W_i)^2\Big] = nh = t ,
$$

$$
\operatorname{Var}\Big[\sum_{i=1}^{n}(\Delta W_i)^2\Big] = n \cdot 2h^2 = 2th \;\longrightarrow\; 0 .
$$

The mean is pinned at $$t$$ for every partition, and the variance vanishes as the partition refines. A quantity whose variance collapses onto a fixed mean converges to that mean, so

$$
\sum_{i=1}^{n}(\Delta W_i)^2 \;\longrightarrow\; t .
$$

This is the quadratic variation, written $$[W, W]_t = t$$. So $$(\mathrm{d}W)^2 = \mathrm{d}t$$ is notation, and what it abbreviates is

$$
\int_0^t (\mathrm{d}W_s)^2 = \int_0^t \mathrm{d}s = t .
$$

Every squared increment going into that sum is random. The sum is not.
