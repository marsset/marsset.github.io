---
title:  "Autonomous Driving Data Loop: Practice Problems"
date:  2026-10-26 09:00:00 +0800
categories:
  - ai
tags: ai
classes: wide
layout: single
use_math: true
excerpt: >
  fourteen practice problems for an autonomous-driving data loop role: ten to talk through, four to code in PyTorch.
---

Fourteen practice problems for an autonomous-driving data loop role. The first ten are discussion questions covering the loop from collection to evaluation; the last four are PyTorch coding problems. Only the questions are listed, for self-testing and repeated practice. A good shape for each answer: clarify → framework → detail → metrics → risks.

### 1. The data loop end to end

The data loop is often written as "collect → mine → pre-label → train → evaluate → feed back". In your own words: how does a complete autonomous-driving data loop run, what problem does each stage solve, and why is it called a "flywheel"?

**Follow-up:** strict DAgger needs an expert to label the states the *student* model visits, but on a real car you cannot let the model drive itself into mistakes. What does industry do to approximate this, and what are the limits of each approach?

### 2. Trigger design

You have just joined and are asked to design the on-vehicle trigger system. How would you categorize triggers? And how do you judge whether a trigger is good or bad?

### 3. Data mining

An algorithm engineer tells you: "Our model does badly in construction zones; we need more data." The data lake holds several petabytes of historical data, mostly unlabeled. How do you find the construction-zone data in it?

### 4. Distribution and coverage

Your manager asks: "Is our training set comprehensive enough? Which scenarios are missing?" How do you answer — that is, how do you quantify the *coverage* of a training set?

### 5. Auto-labeling pipeline

Every month hundreds of thousands of clips need labels, and fully manual labeling is too expensive. An offline large model can produce 3D boxes automatically, but it makes mistakes. How do you design a semi-automatic labeling pipeline that keeps quality high while using as little human effort as possible? The key question: which samples need a human to look at them, and which can be trusted to the model?

### 6. Loop ROI and metrics

At the end of the year your manager asks: "We put a lot of people and compute into the data loop this year. Was it worth it? What metrics prove it?" Which metrics would you design, and what dashboard would you build?

### 7. Root-causing a regression

A week after a new model version ships, the test team reports that the urban takeover rate is 20% higher than with the previous version. You are asked to lead the investigation. How do you analyze it, step by step?

### 8. Active learning

What is active learning? In an autonomous-driving data loop, what strategies would you use to pick the data "most worth labeling", and what are the problems with each?

### 9. Data scaling for end-to-end models

The team is moving from a modular stack to an end-to-end model (sensor input in, trajectory out). What new requirements or challenges does an end-to-end model put on the data loop? How does it differ from the data loop for a traditional perception model?

### 10. World-model data generation

Some long-tail scenarios happen only a few times a year across the whole fleet — cargo falling off the vehicle ahead, a pedestrian darting out from between two parked cars. How do you get data for these? What is the value, and what are the risks, of generating it with a world model or a simulator?

### 11. IoU matrix (coding)

Implement, in PyTorch, the pairwise IoU (intersection area ÷ union area) between two sets of axis-aligned boxes.

```python
def box_iou(boxes1: torch.Tensor, boxes2: torch.Tensor) -> torch.Tensor:
    """
    boxes1: (N, 4), each row [x1, y1, x2, y2], with x1 < x2 and y1 < y2
    boxes2: (M, 4), same format
    returns: (N, M), entry (i, j) is the IoU of boxes1[i] and boxes2[j]
    """
```

- No Python loops; compute everything with tensor operations.
- The IoU of two boxes that do not overlap is 0.

**Follow-ups:**

1. What happens with degenerate boxes (zero width or height)?
2. When N and M are both 100,000, what goes wrong with this function? Where is the bottleneck, and how do you handle it?
3. Does this approach still work for rotated boxes `[cx, cy, w, h, θ]` (vehicles in BEV)? How would you compute it?

### 12. Non-maximum suppression (coding)

Among heavily overlapping detection boxes, keep only the highest-scoring one. You may use `box_iou` from problem 11.

```python
def nms(boxes: torch.Tensor, scores: torch.Tensor, iou_threshold: float) -> torch.Tensor:
    """
    boxes:  (N, 4), [x1, y1, x2, y2]
    scores: (N,), confidence of each box
    iou_threshold: boxes with IoU above this are duplicates
    returns: original indices of the kept boxes, highest score first, shape (K,)
    """
```

1. Sort by score, highest first.
2. Take the highest-scoring remaining box and keep it.
3. Remove every box whose IoU with it exceeds the threshold.
4. Repeat 2 and 3 on the remaining boxes until none are left.

Loops are allowed, but think about which part can be vectorized. When done, check the returned shape and device against the signature.

**Follow-ups:**

1. Cars, pedestrians and cyclists should each be suppressed only against their own class. How do you do it with a single call to `nms`? What are the pitfalls of the trick?
2. In dense crowds, or with vehicles occluding each other, what goes wrong with standard NMS? How would you improve it?
3. In BEV 3D detection, why are duplicate pedestrian boxes often not removed?

### 13. Numerically stable cross-entropy (coding)

Implement cross-entropy loss yourself, without `F.cross_entropy`, `F.log_softmax`, `torch.logsumexp` or `torch.softmax`.

```python
def cross_entropy(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """
    logits:  (B, C), raw scores from the model
    targets: (B,), integer class labels in 0 to C-1
    returns: scalar, the mean loss over the batch
    """
```

- Logits such as 1000 or −1000 must not produce `inf` or `nan`.
- No Python loops.
- Self-check: `logits = torch.tensor([[1000., 0.], [0., 1000.]])`, `targets = torch.tensor([1, 1])` should give 500.

**Follow-ups:**

1. After subtracting the maximum $$m$$, why is the loss *exactly* unchanged? (The question is not why you subtract it.)
2. Does the gradient flow through `max` in backpropagation? Does that make the gradient wrong?
3. A label of −1 means "ignore": it should not count towards the loss. How do you change the function, and what are the pitfalls?

### 14. Picking uncertain samples, without duplicates (coding)

The labeling budget is limited. From a large pool of data the model has already run on, pick the samples most worth sending for labels.

```python
def select_for_labeling(probs: torch.Tensor, embeddings: torch.Tensor,
                        k: int, sim_threshold: float) -> torch.Tensor:
    """
    probs:      (N, C), class probabilities of each sample, each row sums to 1
    embeddings: (N, D), feature vector of each sample
    k:          maximum number of samples to pick
    sim_threshold: cosine similarity above this counts as a duplicate
    returns:    indices of the picked samples, most uncertain first, length at most k
    """
```

1. Measure uncertainty with the predictive entropy; higher entropy is more worth labeling.
2. Pick starting from the most uncertain; skip a sample that is too similar to one already picked (for example, adjacent frames of the same clip).
3. Stop once k samples are picked or the candidates run out.
4. Note: a probability can be exactly 0.

The entropy is

$$
H = -\sum_{c=1}^{C} p_c \log p_c .
$$

When done, think about it: what does this problem have in common with NMS?

**Follow-ups:**

1. With 100 million samples in the data lake and 512-dimensional embeddings, is this approach still feasible? What would you do?
2. When does high entropy *not* mean a sample is worth labeling? Are there samples with very low entropy that are well worth labeling?
