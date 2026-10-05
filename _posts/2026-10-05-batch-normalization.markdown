---
title:  "batch normalization"
date:  2026-10-05 09:00:00 +0800
categories:
  - ai
tags: ai
classes: wide
layout: single
use_math: true
excerpt: >
  standardization with the statistics borrowed from whoever else is in the batch.
---

Standardization is the oldest trick in statistics. Take a set of numbers, subtract their mean, divide by their standard deviation, and what comes out has mean $$0$$ and variance $$1$$. The shape of the distribution is untouched; only its location and scale move. A z-score is exactly this.

Batch normalization is that operation, dropped in between layers of a network:

$$
y = \frac{x - \mathrm{E}[x]}{\sqrt{\mathrm{Var}[x] + \epsilon}} \cdot \gamma + \beta \tag{1}
$$

The fraction is plain standardization, with $$\epsilon$$ added under the root so a channel that happens to be constant does not divide by zero. Everything interesting is in the three choices around it.

**Whose mean.** $$\mathrm{E}[x]$$ and $$\mathrm{Var}[x]$$ are computed per channel, across the examples in the current mini-batch. So a given activation is standardized against whatever else happened to be in the batch with it.

**Then undone, if wanted.** $$\gamma$$ and $$\beta$$ are learned, one pair per channel, initialised to $$1$$ and $$0$$. Setting $$\gamma = \sqrt{\mathrm{Var}[x]}$$ and $$\beta = \mathrm{E}[x]$$ recovers the input exactly, so the layer can represent the identity and standardization is only where it starts, not a constraint it is held to.

Which invites the obvious objection: why standardize at all, if the layer is free to undo it? Because the two routes are not equally easy to optimise. Without the layer, a channel’s scale is the joint product of every weight feeding into it, so nothing can adjust it alone — pull one thread and the whole thing moves. With the layer, that scale is $$\gamma$$: one number, decoupled from everything upstream, a single gradient step away. $$\gamma$$ does not widen what the network can express — a convolution could always rescale its own output by rescaling its weights. It changes where the scale lives, from a property spread across every upstream weight to a single parameter that can be learned on its own.

**Two modes.** At evaluation there is no batch to take statistics from, so running averages collected during training stand in. A batch-norm network therefore computes something different in training than in inference.

### Example

The example below is a complete training run: 512 noisy $$8 \times 8$$ images that ramp either left-to-right or top-to-bottom, and a small convolutional network with a single batch-norm layer learning to tell the two apart.

```python
import torch, torch.nn as nn, torch.nn.functional as F
from torch.utils.data import TensorDataset, DataLoader

torch.manual_seed(0)

# 512 one-channel 8x8 images. Class 0 ramps left-to-right, class 1 top-to-bottom.
ramp = torch.linspace(-1, 1, 8)
y = torch.randint(2, (512,))
x = torch.where(y.view(-1, 1, 1, 1).bool(), ramp.view(1, 1, 8, 1), ramp.view(1, 1, 1, 8))
x = x + 1.5 * torch.randn(512, 1, 8, 8)

loader = DataLoader(TensorDataset(x, y), batch_size=64, shuffle=True)

net = nn.Sequential(
    nn.Conv2d(1, 16, 3, padding=1),
    nn.BatchNorm2d(16),            # given C = 16; never told the batch size
    nn.ReLU(),
    nn.AdaptiveAvgPool2d(1),
    nn.Flatten(),
    nn.Linear(16, 2),
)
opt = torch.optim.Adam(net.parameters(), lr=1e-2)

for epoch in range(5):
    for xb, yb in loader:          # xb is (64, 1, 8, 8)
        loss = F.cross_entropy(net(xb), yb)
        opt.zero_grad(); loss.backward(); opt.step()
    net.eval()                     # switch bn to its running statistics
    with torch.no_grad():
        acc = (net(x).argmax(1) == y).float().mean()
    net.train()
    print(f"epoch {epoch}  loss {loss.item():.3f}  acc {acc:.2f}")
```

```
epoch 0  loss 0.684  acc 0.48
epoch 1  loss 0.645  acc 0.65
epoch 2  loss 0.598  acc 0.93
epoch 3  loss 0.516  acc 0.95
epoch 4  loss 0.512  acc 0.94
```

The batch size is written exactly once, as `batch_size=64` on the `DataLoader`, and it never reaches the layer. `nn.BatchNorm2d(16)` is told the channel count and nothing more: $$\gamma$$, $$\beta$$ and the running statistics all come out as vectors of length 16, obtained by reducing over $$N$$, $$H$$ and $$W$$. And because `shuffle=True` redraws the grouping every epoch, an image is standardized against different neighbours each time it is seen.

### References

1. S. Ioffe, C. Szegedy, "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift," *ICML*, 2015. [arXiv:1502.03167](https://arxiv.org/abs/1502.03167).
