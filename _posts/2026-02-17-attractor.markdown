---
title:  "attractor"
date:  2026-02-17 10:00:00 +0800
categories:
  - AI
tags: AI
classes: wide
layout: single
use_math: true
---

Attractors are beautiful [^chaos-james].

Lorenz system shows even a simple three ODEs can give you a chaotic behavior.

$$
\begin{cases}
x' = \sigma (y - x) \\[6pt]
y' = x(\rho - z) - y \\[6pt]
z' = xy - \beta z
\end{cases}
$$

![Lorenz](/assets/image/A_Trajectory_Through_Phase_Space_in_a_Lorenz_Attractor.gif){: .align-center }
<p style="text-align:center; font-size: 0.7em;">
 when $\rho = 28$, $\sigma = 10$, and $\beta = \frac{8}{3}$ (from wikipedia)
</p>


An even simpler example is logistic map:

$$
x_{n+1} = r x_n (1 - x_n)
$$

, after crossing $r \approx 3.56995$, it enters chaos.

<p align="center">
<img src="/assets/image/Logistic_Bifurcation_map_High_Resolution.png"  style="width:100%;">
</p>

<div style="width:100%; margin: 0.7em auto; text-align:center; font-size: 0.7em">
Bifurcation diagram for the logistic map. The attractor for any value of the
parameter r is shown on the vertical line at that r. (from wikipedia)
</div>

Also see its relationship to Mandelbrot set $\mathcal{M}$ which is the set of complex parameters $c \in \mathbb{C}$ for which the sequence defined by

$$
z_{0} = 0, \qquad
z_{n+1} = z_n^2 + c
$$

remains bounded. That is,

$$
\mathcal{M}
= \left\{ c \in \mathbb{C} \;\middle|\;
\sup_{n \ge 0} |z_n| < \infty \right\}
$$


<p align="center">
<img src="/assets/image/Verhulst-Mandelbrot-Bifurcation.jpg"  style="width:100%;">
</p>
<div style="width:100%; margin: 0.7em auto; text-align:center; font-size: 0.7em">
Correspondence between the Mandelbrot set and the bifurcation diagram of the quadratic map(from wikipedia)
</div>

Finally check Ikeda map:

$$
z_{n+1} = a + b\, z_n e^{i\left(k - \frac{p}{1 + \lvert z_n \rvert^2}\right)}
$$


<p align="center">
<img src="/assets/image/Ikeda_map_a=1_b=0.9_k=0.4_p=6.jpg"  style="width:100%;">
</p>
<div style="width:100%; margin: 0.7em auto; text-align:center; font-size: 0.7em">
Ikeda attractor for parameters a=1, b=0.9, k=0.4 and p=6. (from wikipedia)
</div>

[^chaos-james]: Gleick, James. Chaos: Making a New Science. New York: Viking Books, 1987.

