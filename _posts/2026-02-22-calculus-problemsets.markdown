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

<div class="problem" markdown="1">

$$
f(x)=
\begin{cases}
1, & x \in \mathbb{Q} \\
0, & x \in \mathbb{R} \setminus \mathbb{Q}
\end{cases}
$$

The Dirichlet function $f$ is not Riemann integrable. However, it is Lebesgue integrable:

$$
\int_a^b f(x)\,dx = 0
$$

</div>


<div class="problem" markdown="1">

$$
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
$$

This is [Basel problem](https://en.wikipedia.org/wiki/Basel_problem). It's also $\zeta(2)$.

</div>


<div class="problem" markdown="1">

$$
T(x)=
\begin{cases}
\dfrac{1}{q}, & \text{if } x=\dfrac{p}{q} \text{ in lowest terms} \\[8pt]
0, & \text{if } x \notin \mathbb{Q}
\end{cases}
$$

This is [Thomae’s function](https://en.wikipedia.org/wiki/Thomae%27s_function) (Popcorn function). It's discontinuous at every rational number but Riemann integrable.

![popcorn](/assets/image/Thomae_function.png){: .align-center }
<p style="text-align:center; font-size: 0.7em;">
Point plot on the interval (0,1). The topmost point in the middle shows f(1/2) = 1/2.
</p>

$$
\int_a^b T(x)\,dx = 0
$$

</div>
