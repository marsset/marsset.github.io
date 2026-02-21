---
title:  "fourier series"
date:  2026-02-21 10:00:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
---

Here is fourier series expansion of a periodic function $f$:

$$
f(x)
=
\sum_{n=-\infty}^{\infty}
\hat f(n)\, e^{inx}
$$

where

$$
\hat f(n)
=
\frac{1}{2\pi}
\int_{-\pi}^{\pi}
f(t)\, e^{-int}\, dt
$$


Intuitively speaking, it projects function $f$ over an infinite orthogonal basis $e^{inx}$ and $\hat f$ is the inner product $\langle f, e^{inx} \rangle$.


### Why is it right?

The rightness mainly is about convergency, which means to show the partial sum of the series approach
the original function at limit.

$$
S_N f(x)
=
\sum_{n=-N}^{N}
\hat f(n)\, e^{inx}
$$

$$
S_N f(x) \to f(x)
\quad \text{as } N \to \infty
$$

Dirichlet's approach [^dirichlet-kernel] is to rewrite the partial sum as the convolution as below:

$$
S_N f(x)
=
\frac{1}{2\pi}
\int_{-\pi}^{\pi}
f(t)\, D_N(x - t)\, dt
$$

where $D_N$ is now called Dirichlet kernel,

$$
D_N(x)
=
\sum_{n=-N}^{N} e^{inx}
=
\frac{\sin\!\big((N+\tfrac12)x\big)}
{\sin(x/2)}
$$

$D_N$ goes to diac function at limits, which gives the answer.

[^wikipeida]: https://en.wikipedia.org/wiki/Convergence_of_Fourier_series

[^dirichlet-kernel]: Dirichlet, G. L. (1829). On the convergency of the trigonometrical series which serves to represent an arbitrary function between given limits (R. Fujisawa, Trans. 1885). Crelle’s Journal, 4, 249–266. [english](https://www.jstage.jst.go.jp/article/subutsukiji1885b/3/3/3_3_249/_pdf/-char/ja), [french](https://arxiv.org/pdf/0806.1294)

[^riemann]: Riemann, G. F. B. (1854/2004). On the representation of a function by a trigonometric series. In: Bernhard Riemann, Collected Papers (Transl. R. Baker, C. Christenson & H. Orde), Kendrick Press, Heber City, UT.
