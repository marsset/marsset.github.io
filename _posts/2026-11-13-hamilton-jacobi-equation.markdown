---
title: "The Hamilton-Jacobi Equation"
date: 2026-11-13 10:00:00 +0800
categories:
  - math
tags: math physics classical-mechanics hamilton-jacobi analytical-dynamics control-theory
excerpt: >
  A first-principles geometric and analytical deep dive into the Hamilton-Jacobi equation: from Newton's vectors and Lagrange's stationary action to canonical transformations, action wavefronts, and how classical mechanics anticipates wave mechanics and optimal control.
---

In the history of classical physics, mechanics was reformulated three times, each abstraction ascending to a higher vantage point:

1. **Newton (1687):** Trajectories governed by vectorial forces in Euclidean space: $\mathbf{F} = m\mathbf{a}$.
2. **Lagrange (1788):** Trajectories governed by energy and the stationary action principle across generalized coordinates: $\frac{d}{dt}\frac{\partial L}{\partial \dot{q}} - \frac{\partial L}{\partial q} = 0$.
3. **Hamilton (1834):** Trajectories as symplectic flows through $2n$-dimensional phase space: $\dot{q} = \frac{\partial H}{\partial p}, \; \dot{p} = -\frac{\partial H}{\partial q}$.

Then, in 1837, William Rowan Hamilton and Carl Gustav Jacob Jacobi made an astonishing leap that seemed almost absurd at the time:

> **Why solve $2n$ coupled differential equations for particle trajectories at all?**
>
> What if we can find a single scalar generating function $S(q, t)$ that completely trivializes the motion, reducing the dynamics of particles to the propagation of wave surfaces?

This yields the **Hamilton-Jacobi (HJ) equation**:

$$\frac{\partial S}{\partial t} + H\left(q, \frac{\partial S}{\partial q}, t\right) = 0$$

Where $S(q, t)$ is **Hamilton's Principal Function** (the classical action), and momentum is the spatial gradient of this action field:

$$p = \frac{\partial S}{\partial q}$$

The Hamilton-Jacobi equation is arguably the most versatile partial differential equation in theoretical physics. It connects **geometric optics to wave mechanics**, serves as the semiclassical bridge to the **Schrödinger equation**, and provides the deterministic foundation for modern **optimal control and dynamic programming** (the Hamilton-Jacobi-Bellman equation).

This post explores the Hamilton-Jacobi equation from first principles: its variational roots, its canonical transformation machinery, its geometric interpretation as action wavefronts, and how it solves mechanical systems.

---

## 1. The Core Idea: Action as a Function of Coordinates and Time

In the calculus of variations, Hamilton's Principle states that a physical particle traversing from configuration $q(t_1) = q_1$ to $q(t_2) = q_2$ follows a trajectory that makes the **Action Integral** stationary:

$$S = \int_{t_1}^{t_2} L(q(t), \dot{q}(t), t)\,dt$$

> **Related Deep Dive:** [Why is the Lagrangian T - U and Not T + U?](/math/2026/11/13/why-lagrangian-t-minus-u.html) explores why action integrates $T - U$ instead of total energy $T + U$, and how Euler-Lagrange emerges from path optimization.

Normally, we fix both endpoints $q_1$ and $q_2$ and vary the intermediate paths to derive the Euler-Lagrange equations.

### Shifting the Vantage Point

Now, change the perspective: **fix the starting point $(q_1, t_1)$, but treat the upper endpoint $(q, t)$ as a variable.**

Let $S(q, t)$ be the numerical value of the action evaluated along the *true, physical path* that terminates at coordinate $q$ at time $t$:

<svg viewBox="0 0 760 250" width="100%" style="max-width: 760px; display: block; margin: 24px auto;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="hjPathGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#a855f7"/>
    </linearGradient>
    <marker id="hjArrowBlue" markerWidth="8" markerHeight="8" refX="5" refY="4" orient="auto">
      <path d="M 1,1 L 7,4 L 1,7 Z" fill="#38bdf8"/>
    </marker>
    <marker id="hjArrowAmber" markerWidth="8" markerHeight="8" refX="5" refY="4" orient="auto">
      <path d="M 1,1 L 7,4 L 1,7 Z" fill="#f59e0b"/>
    </marker>
  </defs>

  <rect x="2" y="2" width="756" height="246" rx="12" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>

  <!-- Title -->
  <text x="380" y="30" fill="#f8fafc" font-size="16px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">HAMILTON'S PRINCIPAL FUNCTION: VARIABLE ENDPOINT VARIATION</text>

  <!-- Physical Trajectory -->
  <path d="M 140,150 Q 360,80 580,130" fill="none" stroke="url(#hjPathGrad)" stroke-width="3.5"/>

  <!-- Origin Pin -->
  <circle cx="140" cy="150" r="7" fill="#38bdf8"/>
  <rect x="40" y="165" width="200" height="24" rx="4" fill="#0c4a6e" stroke="#38bdf8" stroke-width="1"/>
  <text x="140" y="181" fill="#bae6fd" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Fixed Origin: (q₁, t₁)</text>

  <!-- Variable Terminal Point -->
  <circle cx="580" cy="130" r="8" fill="#a855f7" stroke="#e9d5ff" stroke-width="2"/>
  <rect x="500" y="70" width="220" height="26" rx="5" fill="#2e1065" stroke="#c084fc" stroke-width="1.2"/>
  <text x="610" y="87" fill="#f3e8ff" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Terminal Destination: (q, t)</text>

  <!-- Displacement Vector dq (vertical) -->
  <line x1="580" y1="130" x2="580" y2="105" stroke="#f59e0b" stroke-width="2" marker-end="url(#hjArrowAmber)"/>
  <text x="595" y="118" fill="#fbbf24" font-size="12px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">+dq</text>

  <!-- Displacement Vector dt (horizontal) -->
  <line x1="580" y1="130" x2="625" y2="130" stroke="#38bdf8" stroke-width="2" marker-end="url(#hjArrowBlue)"/>
  <text x="635" y="134" fill="#38bdf8" font-size="12px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">+dt</text>

  <!-- Path label -->
  <rect x="270" y="95" width="180" height="22" rx="4" fill="#1e293b" stroke="#475569" stroke-width="1"/>
  <text x="360" y="110" fill="#94a3b8" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">True Physical Path</text>

  <!-- Bottom Banner -->
  <rect x="24" y="202" width="712" height="34" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
  <text x="380" y="224" fill="#e2e8f0" font-size="12.5px" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Total Differential:  dS(q, t) = p dq − H dt   ⇒   p = ∂S/∂q  (Momentum),   −H = ∂S/∂t  (Hamilton-Jacobi)</text>
</svg>

How does the total accumulated action $S(q, t)$ change if we slightly displace the destination coordinate by $dq$, or let the arrival time advance by $dt$?

Let us compute the total variation of $S$:

$$dS = \left[ \frac{\partial L}{\partial \dot{q}} \, dq - \left( \dot{q} \frac{\partial L}{\partial \dot{q}} - L \right) dt \right]_{t_1}^{t} + \int_{t_1}^{t} \underbrace{\left( \frac{\partial L}{\partial q} - \frac{d}{dt}\frac{\partial L}{\partial \dot{q}} \right)}_{\text{Strictly 0 along true physical path!}} \delta q\,dt$$

Along the physical trajectory, the Euler-Lagrange integrand vanishes everywhere. We are left solely with the boundary terms at the upper endpoint $(q, t)$:

$$dS = p\,dq - H\,dt$$

Where:
* $p = \frac{\partial L}{\partial \dot{q}}$ is the **generalized momentum**.
* $H = p\dot{q} - L$ is the **Hamiltonian** (total energy in autonomous systems).

By multivariable calculus, the total differential of a scalar function $S(q, t)$ is:

$$dS = \frac{\partial S}{\partial q}\,dq + \frac{\partial S}{\partial t}\,dt$$

Comparing coefficients between the two equations yields two fundamental relations:

$$p = \frac{\partial S}{\partial q}$$

$$\frac{\partial S}{\partial t} = -H$$

Substitute $p = \frac{\partial S}{\partial q}$ into the Hamiltonian definition $H(q, p, t)$, and we arrive at the **Hamilton-Jacobi Equation**:

$$\boxed{\frac{\partial S}{\partial t} + H\left(q, \frac{\partial S}{\partial q}, t\right) = 0}$$

---

## 2. The Canonical Transformation Perspective: The Ultimate Trivialization

In Hamiltonian mechanics, we often perform canonical transformations $(q, p) \to (Q, P)$ to simplify equations of motion.

Hamilton's canonical equations in the new coordinates are governed by a transformed Hamiltonian $K(Q, P, t)$:

$$\dot{Q} = \frac{\partial K}{\partial P}, \quad \dot{P} = -\frac{\partial K}{\partial Q}$$

Jacobi asked a radical question:

> *"Can we choose a canonical transformation so powerful that the new Hamiltonian is identically zero: **$K \equiv 0$**?"*

If $K \equiv 0$, the equations of motion become completely trivial:

$$\dot{Q}_i = 0 \implies Q_i = \beta_i = \text{constant}$$

$$\dot{P}_i = 0 \implies P_i = \alpha_i = \text{constant}$$

In these new coordinates, **nothing moves!** The system is frozen in time. All coordinates and momenta are constants of motion.

<svg viewBox="0 0 760 230" width="100%" style="max-width: 760px; display: block; margin: 24px auto;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="transGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <linearGradient id="trivGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <marker id="hjArrowDown" markerWidth="8" markerHeight="8" refX="4" refY="5" orient="auto">
      <path d="M 1,1 L 4,7 L 7,1 Z" fill="#38bdf8"/>
    </marker>
  </defs>

  <rect x="2" y="2" width="756" height="226" rx="12" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>

  <!-- Top Card: Original Coordinates (q, p) -->
  <rect x="24" y="18" width="712" height="66" rx="8" fill="url(#transGrad)" stroke="#0ea5e9" stroke-width="1.2"/>
  <text x="40" y="40" fill="#38bdf8" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">ORIGINAL COORDINATES (q, p) : Complex Coupled Dynamics</text>
  <text x="40" y="66" fill="#cbd5e1" font-size="12.5px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">q̇ = ∂H/∂p,   ṗ = −∂H/∂q   (2n coupled non-linear differential equations evolving over time)</text>

  <!-- Middle Connector -->
  <line x1="380" y1="86" x2="380" y2="132" stroke="#38bdf8" stroke-width="2.5" marker-end="url(#hjArrowDown)"/>
  <rect x="160" y="96" width="440" height="24" rx="4" fill="#082f49" stroke="#0284c7" stroke-width="1"/>
  <text x="380" y="112" fill="#7dd3fc" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Canonical Transformation via S(q, P, t)  such that K = H + ∂S/∂t ≡ 0</text>

  <!-- Bottom Card: Transformed Coordinates (Q, P) -->
  <rect x="24" y="144" width="712" height="68" rx="8" fill="url(#trivGrad)" stroke="#10b981" stroke-width="1.2"/>
  <text x="40" y="168" fill="#34d399" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">TRANSFORMED COORDINATES (Q, P) : Completely Solved (Frozen State)</text>
  <text x="40" y="194" fill="#cbd5e1" font-size="12.5px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Q̇ = ∂K/∂P = 0,   Ṗ = −∂K/∂Q = 0   ⇒   Q = β (constant),  P = α (constant). Motion is fully integrated!</text>
</svg>

### The Generating Function Condition

From canonical transformation theory, a Type-2 generating function $S(q, P, t)$ transforms the Hamiltonian according to:

$$K = H + \frac{\partial S}{\partial t}$$

Demanding that $K \equiv 0$ immediately reproduces the Hamilton-Jacobi equation:

$$H\left(q, \frac{\partial S}{\partial q}, t\right) + \frac{\partial S}{\partial t} = 0$$

The action $S(q, \alpha, t)$ is nothing other than the **generating function of a canonical transformation that maps the physical system into its own initial constants of motion** $\alpha$ and $\beta$.

---

## 3. Geometric Optics and Wavefronts: Classical Wave Mechanics

The most illuminating property of the Hamilton-Jacobi equation is its geometric structure.

In ordinary Newtonian mechanics, we picture particles as isolated point masses moving along 1D curves (rays). The Hamilton-Jacobi equation replaces this particle view with a **wavefront view**:

<svg viewBox="0 0 760 260" width="100%" style="max-width: 760px; display: block; margin: 24px auto;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="hjRayArrow" markerWidth="8" markerHeight="8" refX="5" refY="4" orient="auto">
      <path d="M 1,1 L 7,4 L 1,7 Z" fill="#38bdf8"/>
    </marker>
    <marker id="hjGradArrow" markerWidth="8" markerHeight="8" refX="5" refY="4" orient="auto">
      <path d="M 1,1 L 7,4 L 1,7 Z" fill="#f59e0b"/>
    </marker>
  </defs>

  <rect x="2" y="2" width="756" height="256" rx="12" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>

  <!-- Title -->
  <text x="380" y="30" fill="#f8fafc" font-size="16px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">GEOMETRIC OPTICS OF MECHANICS: ACTION SURFACES &amp; ORTHOGONAL RAYS</text>

  <!-- Wavefront 1: S(q, t) = S0 -->
  <path d="M 200,60 Q 230,140 200,220" fill="none" stroke="#a855f7" stroke-width="2.5" stroke-dasharray="5,4"/>
  <rect x="130" y="70" width="120" height="22" rx="4" fill="#2e1065" stroke="#a855f7" stroke-width="1"/>
  <text x="190" y="85" fill="#e9d5ff" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">S(q, t) = S₀</text>

  <!-- Wavefront 2: S(q, t) = S1 -->
  <path d="M 370,60 Q 400,140 370,220" fill="none" stroke="#a855f7" stroke-width="2.5" stroke-dasharray="5,4"/>
  <rect x="300" y="70" width="120" height="22" rx="4" fill="#2e1065" stroke="#a855f7" stroke-width="1"/>
  <text x="360" y="85" fill="#e9d5ff" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">S(q, t) = S₁</text>

  <!-- Wavefront 3: S(q, t) = S2 -->
  <path d="M 540,60 Q 570,140 540,220" fill="none" stroke="#a855f7" stroke-width="2.5" stroke-dasharray="5,4"/>
  <rect x="470" y="70" width="120" height="22" rx="4" fill="#2e1065" stroke="#a855f7" stroke-width="1"/>
  <text x="530" y="85" fill="#e9d5ff" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">S(q, t) = S₂</text>

  <!-- Particle Ray (Orthogonal Trajectory) -->
  <line x1="60" y1="140" x2="680" y2="140" stroke="#38bdf8" stroke-width="3" marker-end="url(#hjRayArrow)"/>
  <rect x="60" y="152" width="170" height="22" rx="4" fill="#082f49" stroke="#0284c7" stroke-width="1"/>
  <text x="145" y="167" fill="#38bdf8" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Particle Trajectory (Ray)</text>

  <!-- Momentum Vector p = grad S at Wavefront 1 -->
  <line x1="222" y1="140" x2="280" y2="140" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#hjGradArrow)"/>
  <text x="250" y="128" fill="#fbbf24" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">p = ∇S</text>

  <!-- Momentum Vector p = grad S at Wavefront 2 -->
  <line x1="392" y1="140" x2="450" y2="140" stroke="#f59e0b" stroke-width="2.5" marker-end="url(#hjGradArrow)"/>
  <text x="420" y="128" fill="#fbbf24" font-size="12px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">p = ∇S</text>

  <!-- Right angle symbols -->
  <path d="M 215,130 L 225,130 L 225,140" fill="none" stroke="#e2e8f0" stroke-width="1.2"/>
  <path d="M 385,130 L 395,130 L 395,140" fill="none" stroke="#e2e8f0" stroke-width="1.2"/>
  <path d="M 555,130 L 565,130 L 565,140" fill="none" stroke="#e2e8f0" stroke-width="1.2"/>

  <!-- Bottom Explanatory Caption -->
  <rect x="24" y="210" width="712" height="34" rx="6" fill="#0f172a" stroke="#334155" stroke-width="1"/>
  <text x="380" y="232" fill="#cbd5e1" font-size="12px" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Trajectories are orthogonal rays to propagating action wavefronts, exactly as light rays are normal to optical wave surfaces.</text>
</svg>

1. **Surfaces of Constant Action:** At any time $t$, consider the level surfaces of action in configuration space:
   $$\Sigma_c = \{ q \mid S(q, t) = c \}$$
   These surfaces are **wavefronts** propagating through space.
2. **Particle Trajectories as Orthogonal Rays:** Because the momentum is the gradient of the action:
   $$p = \nabla S$$
   the trajectory of the particle is everywhere **perpendicular to the wavefronts**.

### The Semiclassical Precursor to Quantum Mechanics

This geometric optical duality directly inspired Erwin Schrödinger in 1926. Schrödinger observed that the relationship between wave optics (Maxwell) and ray optics (geometric optics) is mathematically identical to the relationship between wave mechanics and classical mechanics:

<svg viewBox="0 0 760 250" width="100%" style="max-width: 760px; display: block; margin: 24px auto;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="optGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <linearGradient id="qmGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.3"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <marker id="hjArrowRt" markerWidth="8" markerHeight="8" refX="5" refY="4" orient="auto">
      <path d="M 1,1 L 7,4 L 1,7 Z" fill="#38bdf8"/>
    </marker>
    <marker id="hjArrowDn" markerWidth="8" markerHeight="8" refX="4" refY="5" orient="auto">
      <path d="M 1,1 L 4,7 L 7,1 Z" fill="#c084fc"/>
    </marker>
  </defs>

  <rect x="2" y="2" width="756" height="246" rx="12" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>

  <!-- Title -->
  <text x="380" y="30" fill="#f8fafc" font-size="16px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">THE OPTICS-MECHANICS DUALITY (SCHRÖDINGER, 1926)</text>

  <!-- Row 1: Optics -->
  <!-- Box Top-Left: Wave Optics -->
  <rect x="24" y="50" width="280" height="65" rx="8" fill="url(#optGrad)" stroke="#0ea5e9" stroke-width="1.2"/>
  <text x="36" y="74" fill="#38bdf8" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">WAVE OPTICS (Maxwell)</text>
  <text x="36" y="98" fill="#cbd5e1" font-size="12px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Wave Equation ∇²E − (1/v²) ∂²E/∂t² = 0</text>

  <!-- Arrow Top: limit lambda -> 0 -->
  <line x1="310" y1="82" x2="435" y2="82" stroke="#38bdf8" stroke-width="2" marker-end="url(#hjArrowRt)"/>
  <text x="375" y="74" fill="#7dd3fc" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Limit: λ → 0</text>

  <!-- Box Top-Right: Geometric Optics -->
  <rect x="450" y="50" width="286" height="65" rx="8" fill="#0f172a" stroke="#38bdf8" stroke-width="1.2"/>
  <text x="462" y="74" fill="#38bdf8" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">GEOMETRIC OPTICS</text>
  <text x="462" y="98" fill="#cbd5e1" font-size="12px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Fermat's Principle of Least Time: δ ∫ n ds = 0</text>

  <!-- Vertical Connections (Duality) -->
  <line x1="164" y1="120" x2="164" y2="150" stroke="#c084fc" stroke-width="2" marker-end="url(#hjArrowDn)"/>
  <line x1="593" y1="120" x2="593" y2="150" stroke="#c084fc" stroke-width="2" marker-end="url(#hjArrowDn)"/>

  <!-- Row 2: Mechanics -->
  <!-- Box Bottom-Left: Wave Mechanics -->
  <rect x="24" y="160" width="280" height="65" rx="8" fill="url(#qmGrad)" stroke="#a855f7" stroke-width="1.2"/>
  <text x="36" y="184" fill="#c084fc" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">WAVE MECHANICS (Schrödinger)</text>
  <text x="36" y="208" fill="#cbd5e1" font-size="12px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Schrödinger Eq: iℏ ∂ψ/∂t = Ĥ ψ</text>

  <!-- Arrow Bottom: limit hbar -> 0 -->
  <line x1="310" y1="192" x2="435" y2="192" stroke="#c084fc" stroke-width="2" marker-end="url(#hjArrowRt)"/>
  <text x="375" y="184" fill="#d8b4fe" font-size="12px" font-weight="600" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Limit: ℏ → 0</text>

  <!-- Box Bottom-Right: Classical Mechanics -->
  <rect x="450" y="160" width="286" height="65" rx="8" fill="#0f172a" stroke="#a855f7" stroke-width="1.2"/>
  <text x="462" y="184" fill="#c084fc" font-size="13px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">CLASSICAL MECHANICS (H-J)</text>
  <text x="462" y="208" fill="#cbd5e1" font-size="12px" font-family="-apple-system, BlinkMacSystemFont, sans-serif">Hamilton-Jacobi Equation: ∂S/∂t + H(q, ∇S) = 0</text>
</svg>

If we substitute the polar ansatz $\psi(q, t) = A(q, t) e^{i S(q, t) / \hbar}$ into the time-dependent Schrödinger equation:

$$i\hbar \frac{\partial \psi}{\partial t} = -\frac{\hbar^2}{2m}\nabla^2 \psi + V(q)\psi$$

and take the classical limit as Planck's constant $\hbar \to 0$, the imaginary terms vanish and the real part produces:

$$\frac{\partial S}{\partial t} + \frac{1}{2m}(\nabla S)^2 + V(q) = 0$$

This is precisely the **Hamilton-Jacobi equation**! Classical mechanics is the short-wavelength, high-frequency geometrical limit of quantum wave mechanics.

---

## 4. Separation of Variables: Time-Independent Systems

For conservative systems where the Hamiltonian has no explicit time dependence ($H(q, p) = E = \text{const}$), the action separates additively into a spatial part and a linear time part:

$$S(q, E, t) = W(q, E) - E \cdot t$$

Here, $W(q, E)$ is known as **Hamilton's Characteristic Function** (or abbreviated action).

Substitute $S = W - Et$ into the HJ equation:

$$-E + H\left(q, \frac{\partial W}{\partial q}\right) = 0$$

$$\boxed{H\left(q, \frac{\partial W}{\partial q}\right) = E}$$

This is the **Time-Independent Hamilton-Jacobi Equation**. It has converted a time-dependent PDE into a purely spatial differential equation.

---

## 5. Concrete Solved Example: The 1D Harmonic Oscillator

Let us demonstrate the computational power of the Hamilton-Jacobi equation by solving the classical 1D harmonic oscillator without ever integrating Newton's second-order equation directly.

The Hamiltonian is:

$$H(q, p) = \frac{p^2}{2m} + \frac{1}{2} m \omega^2 q^2 = E$$

### Step 1: Write the Time-Independent HJ Equation

Replace $p$ with $\frac{dW}{dq}$:

$$\frac{1}{2m} \left( \frac{dW}{dq} \right)^2 + \frac{1}{2} m \omega^2 q^2 = E$$

### Step 2: Solve for the Momentum Function $\frac{dW}{dq}$

Rearrange for $\frac{dW}{dq}$:

$$\left( \frac{dW}{dq} \right)^2 = 2mE - m^2 \omega^2 q^2$$

$$\frac{dW}{dq} = \sqrt{2mE - m^2 \omega^2 q^2}$$

Integrating gives the characteristic function $W(q, E)$:

$$W(q, E) = \int \sqrt{2mE - m^2 \omega^2 q^2} \, dq$$

The full action function is:

$$S(q, E, t) = \int \sqrt{2mE - m^2 \omega^2 q^2} \, dq - E \cdot t$$

### Step 3: Differentiate with Respect to the Constant of Motion $E$

According to Jacobi's theorem, the conjugate coordinate to the energy $E$ is a new constant $\beta$:

$$\beta = \frac{\partial S}{\partial E} = \frac{\partial W}{\partial E} - t$$

Differentiate under the integral sign with respect to $E$:

$$\frac{\partial W}{\partial E} = \int \frac{\partial}{\partial E} \left( \sqrt{2mE - m^2 \omega^2 q^2} \right) dq = \int \frac{m}{\sqrt{2mE - m^2 \omega^2 q^2}} \, dq$$

Set $\beta + t = \frac{\partial W}{\partial E}$:

$$t + \beta = \int \frac{dq}{\sqrt{\frac{2E}{m} - \omega^2 q^2}} = \frac{1}{\omega} \int \frac{dq}{\sqrt{\frac{2E}{m\omega^2} - q^2}}$$

This standard integral yields the inverse sine:

$$t + \beta = \frac{1}{\omega} \arcsin\left( q \sqrt{\frac{m\omega^2}{2E}} \right)$$

### Step 4: Invert to Find the Trajectory $q(t)$

Multiply by $\omega$ and take the sine of both sides:

$$\sin\big(\omega(t + \beta)\big) = q \sqrt{\frac{m\omega^2}{2E}}$$

$$\boxed{q(t) = \sqrt{\frac{2E}{m\omega^2}} \sin\big(\omega(t + \beta)\big)}$$

The physical harmonic trajectory $q(t)$ has emerged purely from algebraic manipulation and a single differentiation of the action $S$!

---

## 6. The Lineage: From Hamilton-Jacobi to Bellman (HJB)

To see the modern connection to quantitative finance, robotics, and reinforcement learning, compare the classical Hamilton-Jacobi equation with the continuous-time dynamic programming equation:

<svg viewBox="0 0 760 310" width="100%" style="max-width: 760px; display: block; margin: 24px auto;" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cardHj" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#0284c7" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <linearGradient id="cardBellman" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#d97706" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
    <linearGradient id="cardHjb" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.8"/>
    </linearGradient>
  </defs>

  <rect x="2" y="2" width="756" height="306" rx="12" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>

  <!-- Title -->
  <text x="380" y="30" fill="#f8fafc" font-size="16px" font-weight="700" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, sans-serif">THE LINEAGE: HAMILTON-JACOBI TO BELLMAN &amp; MODERN STOCHASTIC HJB</text>

  <!-- Tier 1: Classical Hamilton-Jacobi -->
  <rect x="24" y="48" width="712" height="72" rx="8" fill="url(#cardHj)" stroke="#0ea5e9" stroke-width="1.2"/>
  <rect x="36" y="58" width="220" height="22" rx="4" fill="#0284c7" fill-opacity="0.3"/>
  <text x="44" y="73" fill="#38bdf8" font-size="12px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">CLASSICAL HJ (Deterministic Physics)</text>
  <text x="36" y="102" fill="#e2e8f0" font-size="12.5px" font-weight="600" font-family="-apple-system, BlinkMacSystemFont, sans-serif">∂S/∂t + H(q, ∇S) = 0   [Nature passively minimizes physical action S(q, t)]</text>

  <!-- Tier 2: Deterministic Optimal Control (Bellman) -->
  <rect x="24" y="128" width="712" height="76" rx="8" fill="url(#cardBellman)" stroke="#f59e0b" stroke-width="1.2"/>
  <rect x="36" y="138" width="260" height="22" rx="4" fill="#d97706" fill-opacity="0.3"/>
  <text x="44" y="153" fill="#fbbf24" font-size="12px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">OPTIMAL CONTROL / RL (Bellman)</text>
  <text x="36" y="182" fill="#e2e8f0" font-size="12.5px" font-weight="600" font-family="-apple-system, BlinkMacSystemFont, sans-serif">∂V/∂t + min_u { f(x, u) + ∇V · μ(x, u) } = 0   [Active agent chooses control u(t)]</text>

  <!-- Tier 3: Stochastic HJB -->
  <rect x="24" y="212" width="712" height="80" rx="8" fill="url(#cardHjb)" stroke="#10b981" stroke-width="1.2"/>
  <rect x="36" y="222" width="290" height="22" rx="4" fill="#10b981" fill-opacity="0.3"/>
  <text x="44" y="237" fill="#34d399" font-size="12px" font-weight="700" font-family="-apple-system, BlinkMacSystemFont, sans-serif">STOCHASTIC HJB (Quant Finance &amp; Robotics)</text>
  <text x="36" y="266" fill="#e2e8f0" font-size="12.5px" font-weight="600" font-family="-apple-system, BlinkMacSystemFont, sans-serif">∂V/∂t + min_u { f(x, u) + ∇V · μ(x, u) + ½ σ² ΔV } = 0   [Itô diffusion under noise dW_t]</text>
</svg>

1. **Deterministic Physics ($H(q, p)$):** Nature chooses trajectories that minimize action. The Hamiltonian $H$ is determined by kinetic and potential energy.
2. **Deterministic Control:** An engineer or agent actively chooses control $u$ to minimize running costs: $H(x, p) = \max_u \{ f(x, u) + p \cdot \mu(x, u) \}$.
3. **Stochastic Control (HJB):** Introducing Gaussian Brownian motion ($dW_t$) adds Itô's second-order diffusion curvature term: $\frac{1}{2}\sigma^2 \frac{\partial^2 V}{\partial x^2}$.

The Hamilton-Jacobi equation is the deterministic, conservative ancestor of modern decision theory under uncertainty.

---

## 7. Summary: The Conceptual Hierarchy

| Formulation | Primary Mathematical Object | Equation of Motion | Physical Interpretation |
| :--- | :--- | :--- | :--- |
| **Newtonian** | Vectorial Acceleration $\mathbf{a}$ | $\mathbf{F} = m\ddot{\mathbf{x}}$ | Direct local push and pull |
| **Lagrangian** | Configuration Trajectory $q(t)$ | $\frac{d}{dt}\frac{\partial L}{\partial \dot{q}} - \frac{\partial L}{\partial q} = 0$ | Global path of least action |
| **Hamiltonian** | Phase Space Vector $(q, p)$ | $\dot{q} = \frac{\partial H}{\partial p}, \; \dot{p} = -\frac{\partial H}{\partial q}$ | Symplectic phase-space flow |
| **Hamilton-Jacobi** | Action Field $S(q, t)$ | $\frac{\partial S}{\partial t} + H\left(q, \frac{\partial S}{\partial q}\right) = 0$ | Wavefronts of constant action |
| **Quantum (Schrödinger)** | Probability Amplitude $\psi(q, t)$ | $i\hbar \frac{\partial \psi}{\partial t} = \hat{H}\psi$ | True wave mechanics ($\hbar \to 0 \implies \text{HJ}$) |

The Hamilton-Jacobi equation revealed that particles are rays, that classical mechanics is geometric optics, and that the path of least resistance is mathematically dual to the wavefront of accumulated action.
