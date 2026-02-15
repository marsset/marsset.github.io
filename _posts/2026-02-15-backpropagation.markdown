---
title:  "BackPropagation"
date:  2026-02-15 17:00:00 +0800
categories:
  - AI
tags: AI
classes: wide
layout: single
use_math: true
---
Backpropagation is a technique propsed in 1986 [^bp] to train a feedforward neural network
(i.e. no feedback).

```
x -> f0 -> f1 -> .. -> fn-1 -> fn -> y
---------------------------------------
     input      hidden       output
     layer      layers       layer
```
, each layer is a function:

$$
f_i(x) = \sigma_{i}(W_ix + b_i)
$$

where:

- $x_i \in \mathbb{R}^{d_i}$ is the input vector
- $W_i \in \mathbb{R}^{m_i \times d_i}$ is the weight matrix
- $b_i \in \mathbb{R}^{m_i}$ is the bias vector
- $\sigma_{i}(\cdot)$ is the activation function, which is non-linear, often fixed prior to training such as RELU, optimized only over parameters.
- $f_i(x) \in \mathbb{R}^{m_i}$ is the output vector

Let $\theta$ to be the set of all tunable paramters $W$, $b$, $\sigma$, and our nerual
network is a function:

$$
F(\theta, x) = f_n(...f_1(f_0(x)))
$$

To measure how good we fit the training set
$\mathcal{D} = \{(x_i, y_i)\}_{i=1}^{N}$,
 let's use mean squared error as the cost function:

$$
J(\theta) = \frac{1}{N} \sum_{i=1}^{N} \lVert F(\theta, x_i) - y_i \rVert^2
$$

How to find a good $\theta$ that minimize $J$ as possible?

Usually you need to pick some intial $\theta_0$ smartly, from which you ahead in the negative gradient direction (the neural network shall be designed to guarantee gradient exists) for a better next $\theta$,

$$
\theta_{k+1} = \theta_k - \eta \nabla J
$$

, until the $J$ is small enough as you expect.

How to find the gradient $\nabla J$ for a given $\theta$?
To illustrate this, let's define some helper concepts.

$$
F_i(\theta, x) = f_i(...f_1(f_0(x)))
$$

As the following show, we can observe the prefix are the same and we don't need to recompute them every time:

$$
\frac{\partial J}{\partial W_i^k} =
\underbrace{
\frac{\partial J}{\partial F_n} *
\frac{\partial F_n}{\partial F_{n-1}} *
...
\frac{\partial F_{i+1}}{\partial F_i}
}_{\text{prefix}}
*
\frac{\partial F_i}{\partial W_{i}^k}
$$

$$
\frac{\partial J}{\partial W_{i-1}^k} =
\underbrace{
\frac{\partial J}{\partial F_n} *
\frac{\partial F_n}{\partial F_{n-1}} *
...
\frac{\partial F_{i+1}}{\partial F_i}
}_{\text{prefix}}
*
\frac{\partial F_i}{\partial F_{i-1}}
*
\frac{\partial F_{i-1}}{\partial W_{i-1}^k}
$$

Thus if we compute the gradient backwards and reuse the prefix accumulatively, this is the backpropagation algorithm.


[^bp]: Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. Nature, 323(6088), 533–536.

[^deep-learning]: Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep Learning. Chapter 6. MIT Press. Available at http://www.deeplearningbook.org
