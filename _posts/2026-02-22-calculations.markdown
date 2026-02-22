---
title:  "calculus problemset"
date:  2026-02-22 10:00:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
excerpt: >
  Record some calculus problems met along the daily study.
---

<div class="problem" markdown="1">
$$
\lim_{x \to 0} \frac{\sin(ax)}{x} = a
$$

by taylor expansion,

$$
f(x)
=
\sum_{n=0}^{\infty}
\frac{f^{(n)}(a)}{n!}(x-a)^n
$$

</div>

<div class="problem" markdown="1">

$$
\int_{0}^{\infty} \frac{\sin x}{x} \, dx = \frac{\pi}{2}
$$

This is called [Dirichlet Integral](https://en.wikipedia.org/wiki/Dirichlet_integral). Plugin into $e^{-sx}$

$$
F(s) = \int_{0}^{\infty} e^{-sx}\frac{\sin x}{x}\,dx
$$

by differentiating $s$ we can eliminate the denominator.

$$
F'(s)
=
-\int_{0}^{\infty}
e^{-sx}\sin x
\,dx
$$

use the exponential form $\sin x = \frac{e^{ix} - e^{-ix}}{2i}$, we can get

$$
F'(s) = -\frac{1}{s^2+1}
$$

by knowledge we know

$$
F(s) = - \arctan(s) + C
$$

since $F(\infty) = 0$,

$$
F(0) = \frac{\pi}{2}
$$

</div>
