---
title:  "fourier series"
date:  2026-02-21 10:00:00 +0800
categories:
  - math
tags: math
classes: wide
layout: single
use_math: true
excerpt: fourier series, dirichlet kernel, fourier transform
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

The rightness is mainly about convergency, which means to show the partial sum of the series approach
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


Dirichlet's approach [^dirichlet-kernel] is to rewrite the partial sum as the convolution form, which
basically exchanges two layer sum order and thus converts from frequency domain into time domain:


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

$D_N$ goes to dirac function $\delta(x)$ at limit, which gives the answer.


### Edge cases

Here is an animation of to simulate a square wave with fourier series which demostrates Gibbs phenomenon.

![square_wave](/assets/image/Fourier_series_for_square_wave.gif){: .align-center }

### What's Fourier transform

Fourier transform reveals us frequency domain information.

$$
\hat{f}(\omega)
=
\int_{-\infty}^{\infty}
f(x)\, e^{-i \omega x}\, dx
$$

and convert it back,

$$
f(x)
=
\frac{1}{2\pi}
\int_{-\infty}^{\infty}
\hat{f}(\omega)\, e^{i \omega x}\, d\omega
$$

Here is the frequency of a violin melody:

![violin](/assets/image/violin_frequency.png){: .align-center }

Here is a spectrum of light emitted by the blue flame of a butane torch.

![spectrum](/assets/image/Spectrum_of_blue_flame.png){: .align-center }

Here is a MRI image, which underlying using fourier transform.

![mri](/assets/image/mri.jpeg){: .align-center }

Here is a 4d radar point cloud photo(from [qamcom](https://www.qamcom.com/thesis-4d-imaging-radar/))
 for driverless car, which also uses fourier transform.

![mri](/assets/image/4d-radar-point-cloud.webp){: .align-center }

### why asymmetric?

Notice there is a $\frac{1}{2\pi}$ in the reverse transform which breaks the symmetric. This is called non-unitary. [^riemann]

[^dirichlet-kernel]: Dirichlet, G. L. (1829). On the convergency of the trigonometrical series which serves to represent an arbitrary function between given limits (R. Fujisawa, Trans. 1885). Crelle’s Journal, 4, 249–266. [english](https://www.jstage.jst.go.jp/article/subutsukiji1885b/3/3/3_3_249/_pdf/-char/ja), [french](https://arxiv.org/pdf/0806.1294)

[^riemann]: Riemann, G. F. B. (1854). On the representation of a function by a trigonometric series. In: Bernhard Riemann, Collected Papers (Transl. R. Baker, C. Christenson & H. Orde 2004), Kendrick Press, Heber City, UT. [english](https://www.math.purdue.edu/~kdatchev/428/r12.pdf)
