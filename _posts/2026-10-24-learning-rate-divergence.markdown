---
title:  "Learning Rate and Feature Scale"
date:  2026-10-24 09:00:00 +0800
categories:
  - ai
tags: ai
classes: wide
layout: single
use_math: true
excerpt: >
  a two-parameter linear regression that goes to nan in twelve steps, and why the fix is to rescale the data rather than the step.
---

The smallest model there is: fit $$y = wx + b$$ to a cloud of points by gradient descent on the mean squared error. It should be the "hello world" of training loops. Written the obvious way, it goes to `nan` in about a dozen steps.

### The run

```python
import torch

torch.manual_seed(0)
N = 10000
x = torch.randn(N) * 100.                 # std 100
y = 2. * x + 3. + torch.randn(N) * 100    # true w = 2, b = 3, noise std 100

w = torch.randn(1, requires_grad=True)
b = torch.randn(1, requires_grad=True)
lr = 0.1
for step in range(1000):
    y_hat = w * x + b
    L = ((y_hat - y) ** 2).mean()
    L.backward()
    with torch.no_grad():
        w -= lr * w.grad
        b -= lr * b.grad
    w.grad.zero_()
    b.grad.zero_()
    print(f"step: {step}, loss: {L.item():.1f}, w: {w.item():.4f}, b: {b.item():.4f}")
```

```
step: 0, loss: 65153.7, w: 4699.5249, b: -0.0817
step: 1, loss: 221522984960.0, w: -9426813.0000, b: 1005.3713
step: 2, loss: 892100991262916608.0, w: 18917451776.0000, b: -2016194.5000
...
step: 5, loss: inf, ...
...
step: 11, loss: inf, w: -inf, b: nan
step: 12, loss: nan, w: nan, b: nan
```

$$w$$ starts at $$-0.32$$. One step later it is $$4700$$; the next, $$-9.4 \times 10^6$$. Each step multiplies the error by about $$-2000$$: the sign flips every time and the magnitude grows by three orders. The loss, which is the square, overflows `float32` (largest finite value about $$3.4 \times 10^{38}$$) first and reads `inf` from step 5. A few steps later $$w$$ itself overflows, an `inf - inf` turns up somewhere in the gradient, and from then on everything is `nan`.

Nothing in the code is wrong. Every line does what it says. The step size is simply too large for this data, and the interesting part is that "too large" can be computed exactly.

### Why it diverges

The loss is

$$
L(w, b) = \frac{1}{N} \sum_{i=1}^{N} (w x_i + b - y_i)^2 ,
$$

a quadratic in $$(w, b)$$. A quadratic is described completely by its minimum $$\theta^* = (w^*, b^*)$$ and its Hessian, which here is constant:

$$
H = \begin{pmatrix} \partial^2 L / \partial w^2 & \partial^2 L / \partial w \partial b \\ \partial^2 L / \partial b \partial w & \partial^2 L / \partial b^2 \end{pmatrix}
= 2 \begin{pmatrix} \overline{x^2} & \bar{x} \\ \bar{x} & 1 \end{pmatrix} ,
$$

with the bars meaning averages over the data. For a quadratic the gradient is exactly $$H(\theta - \theta^*)$$, so one step of gradient descent with learning rate $$\eta$$ does

$$
\theta_{t+1} - \theta^* = (I - \eta H)(\theta_t - \theta^*) .
$$

Decompose the error along the eigenvectors of $$H$$. Along an eigenvector with eigenvalue $$\lambda$$ the error is multiplied by $$1 - \eta \lambda$$ every step, independently of every other direction. It shrinks only if $$\lvert 1 - \eta\lambda \rvert < 1$$, so the whole thing converges only if

$$
\eta < \frac{2}{\lambda_{\max}} .
$$

Here $$\bar{x} \approx -1.07$$ is negligible next to $$\overline{x^2} \approx 10039$$, so $$H$$ is nearly diagonal and its eigenvalues are nearly

$$
\lambda_w \approx 2\,\overline{x^2} \approx 20078 , \qquad \lambda_b \approx 2 .
$$

The largest allowed learning rate is $$2 / 20078 \approx 10^{-4}$$. At $$\eta = 0.1$$ the factor along $$w$$ is

$$
1 - 0.1 \times 20078 \approx -2007 ,
$$

which is the $$-2000$$ read off the log above: $$(4699.5 - 2.02) / (-0.32 - 2.02) \approx -2007$$. The theory predicts the blow-up to four digits.

### Watching it in one dimension

Since each eigen-direction evolves on its own, one direction is enough to see every regime. Take the simplest quadratic, $$L(\theta) = \theta^2$$: its minimum is $$\theta^* = 0$$ and its curvature is $$\lambda = 2$$, so each step multiplies $$\theta$$ by $$1 - 2\eta$$. As $$\eta$$ grows, the factor sweeps from $$1$$ down through $$0$$ to $$-1$$ and beyond, and the iterates go through five phases:

- $$\eta < 1/\lambda$$: the factor is in $$(0, 1)$$. Every step lands short of the minimum, on the same side, sliding down one wall of the bowl.
- $$\eta = 1/\lambda$$: the factor is $$0$$. One step, exactly onto the minimum.
- $$1/\lambda < \eta < 2/\lambda$$: the factor is in $$(-1, 0)$$. Every step overshoots to the other wall, but less far each time, so it zig-zags in.
- $$\eta = 2/\lambda$$: the factor is $$-1$$. It overshoots by exactly as much as it started, and bounces between $$\pm\theta_0$$ forever.
- $$\eta > 2/\lambda$$: the factor is below $$-1$$. Each bounce climbs higher up the opposite wall than the last. This is the run above.

Press play to let $$\eta$$ sweep through all five, or grab the bar and hold it at any value. The left panel is the bowl with each step drawn as a chord from one iterate to the next; the right is $$\theta_t$$ against the step count.

<div id="lr-demo">
<style>
#lr-demo{border:1px solid rgba(128,128,128,.4);border-radius:8px;padding:.8em 1em .5em;margin:1.5em 0}
#lr-demo .row{display:flex;flex-wrap:wrap;gap:.6em 1.4em;align-items:center;font-size:.9em;margin-bottom:.4em}
#lr-demo b{font-variant-numeric:tabular-nums}
#lr-demo button{font:inherit;font-size:.9em;color:inherit;background:transparent;border:1px solid rgba(128,128,128,.5);border-radius:5px;padding:.15em .8em;cursor:pointer;min-width:5em}
#lr-demo svg{display:block;width:100%;height:auto;touch-action:pan-y;outline:none}
#lr-demo svg:focus-visible{outline:2px solid rgba(59,130,246,.6);outline-offset:2px}
</style>
<div class="row">
<button type="button">Pause</button>
<span>η = <b class="eta">0.10</b></span>
<span>1 − ηλ = <b class="r">0.80</b></span>
<b class="ph">converges, sliding down one side</b>
</div>
<svg viewBox="0 0 640 300" tabindex="0" role="img" aria-label="gradient descent on L(theta) = theta squared; drag the bar or use the arrow keys to change the learning rate"></svg>
</div>

<script>
(function(){
  var root = document.getElementById('lr-demo');
  if (!root) return;
  var svg = root.querySelector('svg'),
      btn = root.querySelector('button'),
      eo  = root.querySelector('.eta'),
      ro  = root.querySelector('.r'),
      po  = root.querySelector('.ph');
  var LAM = 2, TH0 = -2, NSTEP = 16, EMIN = 0, EMAX = 1.2, LO = 0.01, HI = 1.17;
  var HOP = 360, REST = 900, SWEEP = (HI - 0.03) / 18000;
  var BLUE = '#3b82f6', AMBER = '#f59e0b', RED = '#ef4444';
  var A = { l: 40, r: 316, t: 26, b: 206, x0: -3.2, x1: 3.2, y0: 0, y1: 10.24 };
  var B = { l: 360, r: 628, t: 26, b: 206, y0: -3.2, y1: 3.2 };
  var S = { l: 40, r: 628, y: 256 };
  function ax(v){ return A.l + (v - A.x0) / (A.x1 - A.x0) * (A.r - A.l); }
  function ay(v){ return A.b - (v - A.y0) / (A.y1 - A.y0) * (A.b - A.t); }
  function bx(t){ return B.l + t / NSTEP * (B.r - B.l); }
  function by(v){ return B.b - (v - B.y0) / (B.y1 - B.y0) * (B.b - B.t); }
  function sx(e){ return S.l + (e - EMIN) / (EMAX - EMIN) * (S.r - S.l); }
  function f(v){ return v.toFixed(1); }
  function txt(x, y, s, anchor, op){
    return '<text x="' + f(x) + '" y="' + f(y) + '" text-anchor="' + (anchor || 'middle') +
           '" font-size="11" fill="currentColor" fill-opacity="' + (op || 0.6) + '">' + s + '</text>';
  }
  function line(x1, y1, x2, y2, op){
    return '<line x1="' + f(x1) + '" y1="' + f(y1) + '" x2="' + f(x2) + '" y2="' + f(y2) +
           '" stroke="currentColor" stroke-opacity="' + op + '" stroke-width="1"/>';
  }
  function phase(e){
    var r = 1 - LAM * e;
    if (Math.abs(r) < 0.012)     return ['lands on the minimum in one step', BLUE];
    if (Math.abs(r + 1) < 0.012) return ['bounces between the walls forever', AMBER];
    if (r > 0)                   return ['converges, sliding down one side', BLUE];
    if (r > -1)                  return ['converges, zig-zagging across', BLUE];
    return ['diverges', RED];
  }

  var stat = [], i, v;
  stat.push('<defs><clipPath id="lr-ca"><rect x="' + A.l + '" y="' + A.t + '" width="' + (A.r - A.l) + '" height="' + (A.b - A.t) + '"/></clipPath>' +
            '<clipPath id="lr-cb"><rect x="' + B.l + '" y="' + B.t + '" width="' + (B.r - B.l) + '" height="' + (B.b - B.t) + '"/></clipPath></defs>');
  stat.push(txt(A.l, 14, 'L(θ) = θ²', 'start', 0.75));
  stat.push(line(A.l, ay(0), A.r, ay(0), 0.3));
  [-2, 0, 2].forEach(function(t){
    stat.push(line(ax(t), ay(0), ax(t), ay(0) + 4, 0.4));
    stat.push(txt(ax(t), ay(0) + 17, t < 0 ? '−' + (-t) : t));
  });
  stat.push(txt(A.r, ay(0) + 17, 'θ', 'end'));
  var par = [];
  for (i = 0; i <= 120; i++){ v = A.x0 + (A.x1 - A.x0) * i / 120; par.push(f(ax(v)) + ',' + f(ay(v * v))); }
  stat.push('<polyline points="' + par.join(' ') + '" fill="none" stroke="currentColor" stroke-opacity="0.5" stroke-width="1.5"/>');
  stat.push(txt(B.l, 14, 'θₜ against step t', 'start', 0.75));
  [-2, 2].forEach(function(t){
    stat.push(line(B.l, by(t), B.r, by(t), 0.12));
    stat.push(txt(B.l - 6, by(t) + 4, t < 0 ? '−' + (-t) : t, 'end'));
  });
  stat.push(line(B.l, by(0), B.r, by(0), 0.3));
  stat.push(txt(B.l - 6, by(0) + 4, '0', 'end'));
  [0, 8, 16].forEach(function(t){ stat.push(txt(bx(t), B.b + 17, t)); });
  var bands = [[0, 0.5, BLUE, 0.14, 'one side'], [0.5, 1, BLUE, 0.28, 'zig-zag'], [1, EMAX, RED, 0.28, 'diverges']];
  bands.forEach(function(b){
    stat.push('<rect x="' + f(sx(b[0])) + '" y="' + (S.y - 4) + '" width="' + f(sx(b[1]) - sx(b[0])) +
              '" height="8" fill="' + b[2] + '" fill-opacity="' + b[3] + '"/>');
    stat.push(txt((sx(b[0]) + sx(b[1])) / 2, S.y - 12, b[4], 'middle', 0.5));
  });
  [[0, '0'], [0.5, '1/λ'], [1, '2/λ']].forEach(function(t){
    stat.push(line(sx(t[0]), S.y - 7, sx(t[0]), S.y + 7, 0.5));
    stat.push(txt(sx(t[0]), S.y + 22, t[1]));
  });
  stat.push(txt(S.r, S.y + 22, 'η', 'end'));
  stat = stat.join('');

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var eta = 0.1, dir = 1, hopT = 0, last = null, visible = true, dragging = false, playing;

  function draw(){
    var ph = phase(eta), c = ph[1], r = 1 - LAM * eta, th = [TH0], k, nVis = NSTEP, out = [];
    for (k = 1; k <= NSTEP; k++){ th.push(Math.max(-1e3, Math.min(1e3, th[k - 1] * r))); }
    for (k = 1; k <= NSTEP; k++){ if (Math.abs(th[k]) > 3.2){ nVis = k; break; } }
    var t = reduced ? nVis * HOP : hopT, kk = Math.min(nVis, Math.floor(t / HOP)), u = 0;
    if (kk < nVis){ u = (t - kk * HOP) / HOP; u = (1 - Math.cos(Math.PI * u)) / 2; }
    var P = th.map(function(q){ return [ax(q), ay(q * q)]; });
    var Q = th.map(function(q, j){ return [bx(j), by(q)]; });
    function lerp(p, a, b){ return [p[a][0] + (p[b][0] - p[a][0]) * u, p[a][1] + (p[b][1] - p[a][1]) * u]; }
    var pa = kk < nVis ? lerp(P, kk, kk + 1) : P[nVis], qa = kk < nVis ? lerp(Q, kk, kk + 1) : Q[nVis];
    function path(p, upto, op, w){
      var s = [];
      for (var j = 0; j <= upto; j++) s.push(f(p[j][0]) + ',' + f(p[j][1]));
      return '<polyline points="' + s.join(' ') + '" fill="none" stroke="' + c + '" stroke-opacity="' + op + '" stroke-width="' + w + '"/>';
    }
    function trail(p, a){
      var s = [];
      for (var j = 0; j <= kk && j <= nVis; j++) s.push(f(p[j][0]) + ',' + f(p[j][1]));
      s.push(f(a[0]) + ',' + f(a[1]));
      return '<polyline points="' + s.join(' ') + '" fill="none" stroke="' + c + '" stroke-opacity="0.85" stroke-width="1.8"/>';
    }
    function dots(p){
      var s = '';
      for (var j = 0; j <= nVis; j++){
        s += '<circle cx="' + f(p[j][0]) + '" cy="' + f(p[j][1]) + '" r="2.8" fill="' + c + '" fill-opacity="' + (j <= kk ? 0.9 : 0.25) + '"/>';
      }
      return s;
    }
    out.push('<g clip-path="url(#lr-ca)">' + path(P, nVis, 0.2, 1.2) + trail(P, pa) + dots(P) +
             '<circle cx="' + f(pa[0]) + '" cy="' + f(pa[1]) + '" r="6" fill="' + c + '"/></g>');
    out.push('<g clip-path="url(#lr-cb)">' + path(Q, nVis, 0.2, 1.2) + trail(Q, qa) + dots(Q) +
             '<circle cx="' + f(qa[0]) + '" cy="' + f(qa[1]) + '" r="5" fill="' + c + '"/></g>');
    out.push('<circle cx="' + f(sx(eta)) + '" cy="' + S.y + '" r="9" fill="' + c + '" style="cursor:grab"/>');
    svg.innerHTML = stat + out.join('');
    eo.textContent = eta.toFixed(2);
    ro.textContent = r.toFixed(2).replace('-', '−');
    po.textContent = ph[0];
    po.style.color = c;
    if (!reduced && hopT > nVis * HOP + REST) hopT = 0;
  }

  function setPlaying(p){ playing = p; btn.textContent = p ? 'Pause' : 'Play'; }
  function frame(ts){
    var dt = last === null ? 0 : Math.min(50, ts - last);
    last = ts;
    if (visible){
      if (playing && !dragging){
        var slow = (Math.abs(eta - 0.5) < 0.03 || Math.abs(eta - 1) < 0.03) ? 0.2 : 1;
        eta += dir * dt * SWEEP * slow;
        if (eta >= HI){ eta = HI; dir = -1; }
        if (eta <= 0.03){ eta = 0.03; dir = 1; }
      }
      hopT += dt;
      draw();
    }
    requestAnimationFrame(frame);
  }

  function toSvg(e){
    var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
    return p.matrixTransform(svg.getScreenCTM().inverse());
  }
  function setEta(e){
    e = Math.max(LO, Math.min(EMAX, e));
    if (Math.abs(e - 0.5) < 0.012) e = 0.5;
    if (Math.abs(e - 1) < 0.012) e = 1;
    eta = e;
  }
  function fromX(x){ setEta(EMIN + (x - S.l) / (S.r - S.l) * (EMAX - EMIN)); }
  svg.addEventListener('pointerdown', function(e){
    var p = toSvg(e);
    if (p.y < S.y - 26 || p.y > S.y + 26) return;
    dragging = true; setPlaying(false); hopT = 0;
    svg.setPointerCapture(e.pointerId);
    fromX(p.x);
    e.preventDefault();
  });
  svg.addEventListener('pointermove', function(e){ if (dragging) fromX(toSvg(e).x); });
  function release(){ if (dragging){ dragging = false; hopT = 0; } }
  svg.addEventListener('pointerup', release);
  svg.addEventListener('pointercancel', release);
  svg.addEventListener('keydown', function(e){
    var d = { ArrowLeft: -0.01, ArrowDown: -0.01, ArrowRight: 0.01, ArrowUp: 0.01 }[e.key];
    if (d){ setPlaying(false); setEta(Math.round((eta + d) * 100) / 100); hopT = 0; e.preventDefault(); }
    else if (e.key === ' '){ setPlaying(!playing); e.preventDefault(); }
  });
  btn.addEventListener('click', function(){ setPlaying(!playing); });

  if ('IntersectionObserver' in window){
    new IntersectionObserver(function(es){ visible = es[0].isIntersecting; }).observe(root);
  }
  setPlaying(!reduced);
  requestAnimationFrame(frame);
})();
</script>

Our regression sat at $$\eta = 0.1$$ against an edge of $$2/\lambda_w \approx 10^{-4}$$ — a thousand times past it, far off the right end of that bar.

### Why a smaller learning rate is not the fix

The natural response is to drop $$\eta$$ below the threshold. At $$\eta = 5 \times 10^{-5}$$:

```
step: 0,   loss: 65153.7, w: 2.0278, b: 0.0983
step: 1,   loss: 10146.8, w: 2.0187, b: 0.0984
step: 100, loss: 10146.0, w: 2.0187, b: 0.1142
step: 999, loss: 10145.5, w: 2.0187, b: 0.2508
```

$$w$$ is now fine — it is essentially solved in one step, because $$\eta \lambda_w \approx 1$$. But $$b$$ barely moves. Its factor is

$$
1 - 5 \times 10^{-5} \times 2 = 0.9999 ,
$$

so after a thousand steps the gap to $$b^*$$ has closed by only $$1 - 0.9999^{1000} \approx 10\%$$. Getting it to close properly needs tens of thousands of steps.

This is the real problem. The learning rate is capped by the steepest direction and the speed is set by the flattest one. The ratio of the two,

$$
\kappa = \frac{\lambda_{\max}}{\lambda_{\min}} \approx 10^4 ,
$$

is the condition number, and gradient descent needs on the order of $$\kappa$$ steps no matter how $$\eta$$ is chosen. Geometrically, the level sets of $$L$$ are not circles but ellipses ten thousand times longer than they are wide: a step large enough to make progress along the long axis bounces off the walls of the short one.

The cause is that $$x$$ and the constant $$1$$ that multiplies $$b$$ live on scales a hundred times apart, and the curvature goes as the square of the scale.

### The fix: standardize the input

Replace $$x$$ with $$x_n = (x - \mu) / \sigma$$, where $$\mu$$ and $$\sigma$$ are its mean and standard deviation. Now $$\bar{x}_n = 0$$ and $$\overline{x_n^2} = 1$$, and the Hessian becomes

$$
H = 2 \begin{pmatrix} 1 & 0 \\ 0 & 1 \end{pmatrix} = 2I .
$$

Both eigenvalues are $$2$$ and $$\kappa = 1$$. The ellipse is a circle. Any $$\eta < 1$$ converges, $$\eta = 0.1$$ shrinks the error by $$0.8$$ per step in every direction, and $$\eta = 0.5$$ would land on the minimum in a single step.

```python
x_mean, x_std = x.mean(), x.std()
x_n = (x - x_mean) / x_std
# ... same loop, with x_n in place of x, lr = 0.1
```

```
step: 0,   loss: 51186.1, w: 40.1937,  b: -0.0128
step: 10,  loss: 10616.9, w: 184.8693, b: -0.4097
step: 50,  loss: 10143.4, w: 202.2749, b: -0.4575
step: 999, loss: 10143.4, w: 202.2772, b: -0.4575
```

Converged in about fifty steps. These are parameters of the model in standardized coordinates, $$y = w_n x_n + b_n$$. Substituting $$x_n = (x - \mu)/\sigma$$ maps them back:

$$
y = \frac{w_n}{\sigma} x + \left( b_n - \frac{w_n \mu}{\sigma} \right)
\quad\Longrightarrow\quad
w = \frac{w_n}{\sigma} , \qquad b = b_n - \frac{w_n \mu}{\sigma} .
$$

With $$\mu = -1.07$$ and $$\sigma = 100.19$$ that gives $$w = 2.0189$$ and $$b = 1.7024$$, identical to the closed-form least-squares solution `torch.linalg.lstsq`.

Two things that look like failures and are not:

- **$$b = 1.70$$, not $$3$$.** That is the best fit to *this* sample. With noise of standard deviation $$100$$ and $$10^4$$ points, the standard error of the intercept is about $$100 / \sqrt{10^4} = 1$$, so missing by $$1.3$$ is ordinary.
- **The loss stops at $$10143$$.** That is the variance of the noise, $$100^2$$. No line can do better on data that scatters this much around the true one.

(And an aside on the comment in the original code: `torch.randn(N) * 100` is not "from $$[-100, 100]$$". It is normal with standard deviation $$100$$, unbounded, with about $$99.7\%$$ of its values inside $$[-300, 300]$$. A uniform draw on $$[-100, 100]$$ would be `torch.rand(N) * 200 - 100`.)

### Why this is the classic one

Almost everyone who writes a training loop by hand meets this exact failure, and it is worth recognizing on sight: loss that *grows* instead of falling, alternating in sign, reaching `inf` and then `nan` within a few steps. The first two suspects are always the learning rate and the scale of the inputs — and the analysis above says they are the same suspect, since the largest usable learning rate is $$2/\lambda_{\max}$$ and $$\lambda_{\max}$$ is set by the scale of the data.

The deeper half, ill-conditioning, is why so much standard practice exists:

- **Input normalization.** Subtracting a mean and dividing by a standard deviation before training — the per-channel ImageNet constants, `StandardScaler` on tabular features — is exactly the $$x_n$$ above.
- **Normalization layers.** [Batch normalization]({% post_url 2026-10-05-batch-normalization %}) and layer normalization do the same thing to intermediate activations, so that deeper layers see inputs on a sane scale throughout training.
- **Adaptive optimizers.** Adam divides each parameter's step by a running estimate of that parameter's gradient magnitude, giving every coordinate its own effective learning rate. On this problem it converges with `lr = 0.1` even on the raw, unstandardized $$x$$. That only works because the badly-scaled directions here happen to line up with the coordinate axes; standardizing is still cheaper and more robust.
- **Initialization schemes.** Xavier and Kaiming initialization choose weight scales so that activations neither explode nor vanish at the start of training — the same concern about scale, applied before the first step.

In a two-parameter regression the whole story fits on one page: one Hessian, two eigenvalues, a factor of $$-2007$$. In a large network the Hessian is unimaginably bigger and nobody computes it, but when the loss goes to `nan` the diagnosis runs the same way — check the scale of the data, then the learning rate, then whether some intermediate quantity has quietly grown by orders of magnitude.
