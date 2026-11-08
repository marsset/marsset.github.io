---
title:  "3D Gaussian Splatting"
date:  2026-10-11 09:00:00 +0800
categories:
  - ai
tags: ai
excerpt: >
  notes, starting from what a rendered pixel is actually measuring.
---


### Luminance

Photometry is radiometry weighted by the eye, whose sensitivity is far from flat across wavelengths. The weighting is the luminous efficiency function $$V(\lambda)$$, a dimensionless curve peaking at $$1$$ where the eye is sharpest, and luminance is spectral radiance integrated against it:

$$
L_v = 683 \int L_e(\lambda)\, V(\lambda)\, d\lambda . \tag{1}
$$

Here $$L_e(\lambda)$$ is the spectral radiance, $$V(\lambda)$$ discards what the eye cannot use, and the factor $$683\,\mathrm{lm/W}$$ is not empirical but definitional: the SI fixes the candela by declaring monochromatic light at $$540\,\mathrm{THz}$$ — about $$555\,\mathrm{nm}$$ — to have a luminous efficacy of exactly that. So $$L_v$$ is radiance as the eye counts it, and it is what a pixel is ultimately a number for.

### A Gaussian as a patch of fog

The primitive everything is built from is a single 3D Gaussian, and the most useful way to picture one is as a small patch of fog: densest at the centre, thinning smoothly outward in every direction, with no surface and no edge anywhere.

$$
G(x) = \exp\!\left(-\tfrac12\,(x - \mu)^{\top}\, \Sigma^{-1}\, (x - \mu)\right) . \tag{2}
$$

$$\mu$$ says where the patch sits. The covariance $$\Sigma$$ says how big it is, how stretched, and which way it is turned, which is why the fog is an ellipsoidal smear in general rather than a ball.

<svg viewBox="0 0 640 250" width="100%" style="max-width:640px;display:block;margin:1.4em auto;" role="img" aria-label="a single 3D Gaussian drawn as a soft blob, dense at the centre and fading smoothly outward, beside its density profile along a line through the centre">
  <defs><radialGradient id="gs-fog"><stop offset="0.0" stop-color="#5b7cfa" stop-opacity="0.95"/><stop offset="0.1" stop-color="#5b7cfa" stop-opacity="0.908"/><stop offset="0.2" stop-color="#5b7cfa" stop-opacity="0.794"/><stop offset="0.3" stop-color="#5b7cfa" stop-opacity="0.634"/><stop offset="0.4" stop-color="#5b7cfa" stop-opacity="0.462"/><stop offset="0.5" stop-color="#5b7cfa" stop-opacity="0.308"/><stop offset="0.6" stop-color="#5b7cfa" stop-opacity="0.188"/><stop offset="0.7" stop-color="#5b7cfa" stop-opacity="0.105"/><stop offset="0.8" stop-color="#5b7cfa" stop-opacity="0.053"/><stop offset="0.9" stop-color="#5b7cfa" stop-opacity="0.025"/><stop offset="1.0" stop-color="#5b7cfa" stop-opacity="0.011"/></radialGradient></defs>
  <ellipse cx="158.0" cy="108.0" rx="132.0" ry="81.0" transform="rotate(-22.0 158.0 108.0)" fill="url(#gs-fog)"/>
  <polyline points="198.8,91.5 199.4,93.2 199.8,94.9 200.0,96.7 200.0,98.6 199.9,100.4 199.6,102.4 199.1,104.3 198.4,106.2 197.5,108.2 196.5,110.2 195.3,112.1 194.0,114.0 192.5,116.0 190.9,117.8 189.1,119.7 187.2,121.4 185.1,123.2 183.0,124.8 180.7,126.4 178.3,127.9 175.9,129.3 173.4,130.7 170.8,131.9 168.1,133.0 165.4,134.1 162.7,135.0 160.0,135.8 157.2,136.4 154.5,137.0 151.7,137.4 149.0,137.7 146.4,137.9 143.7,138.0 141.2,137.9 138.7,137.7 136.3,137.4 134.0,136.9 131.8,136.3 129.7,135.6 127.7,134.8 125.9,133.9 124.2,132.8 122.6,131.7 121.2,130.4 120.0,129.0 118.9,127.6 118.0,126.1 117.2,124.5 116.6,122.8 116.2,121.1 116.0,119.3 116.0,117.4 116.1,115.6 116.4,113.6 116.9,111.7 117.6,109.8 118.5,107.8 119.5,105.8 120.7,103.9 122.0,102.0 123.5,100.0 125.1,98.2 126.9,96.3 128.8,94.6 130.9,92.8 133.0,91.2 135.3,89.6 137.7,88.1 140.1,86.7 142.6,85.3 145.2,84.1 147.9,83.0 150.6,81.9 153.3,81.0 156.0,80.2 158.8,79.6 161.5,79.0 164.3,78.6 167.0,78.3 169.6,78.1 172.3,78.0 174.8,78.1 177.3,78.3 179.7,78.6 182.0,79.1 184.2,79.7 186.3,80.4 188.3,81.2 190.1,82.1 191.8,83.2 193.4,84.3 194.8,85.6 196.0,87.0 197.1,88.4 198.0,89.9 198.8,91.5" fill="none" stroke="#5b7cfa" stroke-opacity="0.45" stroke-width="1"/>
  <polyline points="239.6,75.0 240.7,78.4 241.5,81.9 242.0,85.4 242.0,89.1 241.8,92.9 241.1,96.7 240.1,100.6 238.8,104.5 237.1,108.4 235.0,112.3 232.7,116.2 230.0,120.1 227.0,123.9 223.7,127.7 220.1,131.3 216.3,134.9 212.2,138.3 207.9,141.6 203.4,144.8 198.7,147.8 193.8,150.7 188.7,153.3 183.5,155.8 178.2,158.1 172.8,160.1 167.4,161.9 161.9,163.5 156.4,164.9 150.9,166.0 145.5,166.9 140.1,167.5 134.7,167.8 129.5,167.9 124.4,167.8 119.4,167.4 114.6,166.7 110.0,165.8 105.6,164.6 101.4,163.2 97.5,161.6 93.8,159.7 90.4,157.6 87.2,155.3 84.4,152.8 81.9,150.1 79.7,147.2 77.9,144.2 76.4,141.0 75.3,137.6 74.5,134.1 74.0,130.6 74.0,126.9 74.2,123.1 74.9,119.3 75.9,115.4 77.2,111.5 78.9,107.6 81.0,103.7 83.3,99.8 86.0,95.9 89.0,92.1 92.3,88.3 95.9,84.7 99.7,81.1 103.8,77.7 108.1,74.4 112.6,71.2 117.3,68.2 122.2,65.3 127.3,62.7 132.5,60.2 137.8,57.9 143.2,55.9 148.6,54.1 154.1,52.5 159.6,51.1 165.1,50.0 170.5,49.1 175.9,48.5 181.3,48.2 186.5,48.1 191.6,48.2 196.6,48.6 201.4,49.3 206.0,50.2 210.4,51.4 214.6,52.8 218.5,54.4 222.2,56.3 225.6,58.4 228.8,60.7 231.6,63.2 234.1,65.9 236.3,68.8 238.1,71.8 239.6,75.0" fill="none" stroke="#5b7cfa" stroke-opacity="0.3" stroke-width="1"/>
  <line x1="35.6" y1="157.4" x2="280.4" y2="58.6" stroke="currentColor" stroke-opacity="0.65" stroke-width="1" stroke-dasharray="5 4"/>
  <polyline points="372.0,184.8 374.1,184.7 376.1,184.4 378.1,184.2 380.2,183.9 382.2,183.6 384.3,183.3 386.4,182.9 388.4,182.5 390.4,182.0 392.5,181.4 394.6,180.8 396.6,180.2 398.6,179.4 400.7,178.6 402.8,177.7 404.8,176.8 406.9,175.7 408.9,174.5 410.9,173.3 413.0,171.9 415.1,170.5 417.1,168.9 419.1,167.2 421.2,165.4 423.2,163.5 425.3,161.5 427.4,159.3 429.4,157.1 431.4,154.7 433.5,152.2 435.6,149.7 437.6,147.0 439.6,144.2 441.7,141.3 443.8,138.4 445.8,135.4 447.9,132.3 449.9,129.2 451.9,126.1 454.0,122.9 456.0,119.8 458.1,116.6 460.1,113.5 462.2,110.5 464.2,107.5 466.3,104.6 468.4,101.8 470.4,99.1 472.5,96.6 474.5,94.2 476.6,92.0 478.6,90.0 480.6,88.2 482.7,86.6 484.8,85.2 486.8,84.1 488.9,83.2 490.9,82.5 492.9,82.1 495.0,82.0 497.1,82.1 499.1,82.5 501.1,83.2 503.2,84.1 505.2,85.2 507.3,86.6 509.4,88.2 511.4,90.0 513.5,92.0 515.5,94.2 517.5,96.6 519.6,99.1 521.6,101.8 523.7,104.6 525.8,107.5 527.8,110.5 529.9,113.5 531.9,116.6 534.0,119.8 536.0,122.9 538.0,126.1 540.1,129.2 542.2,132.3 544.2,135.4 546.2,138.4 548.3,141.3 550.4,144.2 552.4,147.0 554.5,149.7 556.5,152.2 558.5,154.7 560.6,157.1 562.6,159.3 564.7,161.5 566.8,163.5 568.8,165.4 570.8,167.2 572.9,168.9 575.0,170.5 577.0,171.9 579.0,173.3 581.1,174.5 583.1,175.7 585.2,176.8 587.2,177.7 589.3,178.6 591.4,179.4 593.4,180.2 595.5,180.8 597.5,181.4 599.5,182.0 601.6,182.5 603.7,182.9 605.7,183.3 607.8,183.6 609.8,183.9 611.9,184.2 613.9,184.4 616.0,184.7 618.0,184.8" fill="none" stroke="#5b7cfa" stroke-width="1.8" stroke-linejoin="round"/>
  <line x1="372.0" y1="186.0" x2="618.0" y2="186.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/>
  <line x1="413.0" y1="186.0" x2="413.0" y2="191.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/><text x="413.0" y="205.0" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">&#8722;2&#963;</text><line x1="454.0" y1="186.0" x2="454.0" y2="191.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/><text x="454.0" y="205.0" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">&#8722;1&#963;</text><line x1="495.0" y1="186.0" x2="495.0" y2="191.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/><text x="495.0" y="205.0" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">0</text><line x1="536.0" y1="186.0" x2="536.0" y2="191.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/><text x="536.0" y="205.0" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">1&#963;</text><line x1="577.0" y1="186.0" x2="577.0" y2="191.0" stroke="currentColor" stroke-opacity="0.55" stroke-width="1"/><text x="577.0" y="205.0" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">2&#963;</text>
  <text x="158" y="232" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">a single Gaussian</text>
  <text x="495" y="232" text-anchor="middle" font-size="13" fill="currentColor" fill-opacity="0.75" font-family="Georgia, serif">density along the dashed line</text>
</svg>

The rings are contours of equal density, not boundaries. The density is positive everywhere and simply becomes too small to matter, and that is the property the method rests on. A primitive with a hard edge gives an optimiser nothing to follow when it has to decide whether to move, stretch or rotate the thing; a smooth falloff is differentiable everywhere. It is also what lets many of these overlap and blend into a continuous image instead of tiling into a mosaic.

### Where that form comes from

Equation (2) is a lot of notation for a blob, but it assembles from the one-dimensional case in three steps, and each piece of the notation arrives for a reason.

**One dimension.** A Gaussian in one variable is

$$
g(x) = \exp\!\left(-\frac{x^2}{2\sigma^2}\right) . \tag{3}
$$

The ratio $$x^2/\sigma^2$$ is squared distance measured in units of the standard deviation, so the shape is the same whatever the scale. The $$\tfrac12$$ is a convention, and it is the one that makes $$\sigma^2$$ come out as exactly the variance.

**Three axes, multiplied.** Suppose for a moment the ellipsoid's axes line up with the coordinate axes, with standard deviations $$\sigma_1, \sigma_2, \sigma_3$$. Three independent one-dimensional Gaussians multiply, which means their exponents add:

$$
G(x) = \exp\!\left(-\tfrac12\left(\frac{x_1^2}{\sigma_1^2} + \frac{x_2^2}{\sigma_2^2} + \frac{x_3^2}{\sigma_3^2}\right)\right) . \tag{4}
$$

That sum is a quadratic form:

$$
\frac{x_1^2}{\sigma_1^2} + \frac{x_2^2}{\sigma_2^2} + \frac{x_3^2}{\sigma_3^2} = x^{\top} \Lambda^{-1} x , \qquad \Lambda = \mathrm{diag}(\sigma_1^2, \sigma_2^2, \sigma_3^2) . \tag{5}
$$

This is where the row-vector, inverse-matrix, column-vector sandwich comes from. It is nothing more exotic than per-axis distance divided by per-axis variance, written as a single matrix expression.

**Any orientation, by rotating.** Real ellipsoids do not line up with the axes. Let $$R$$ be the rotation that takes the ellipsoid's own frame to the world. An offset $$x$$ in the world has coordinates $$y = R^{\top} x$$ in that frame, where equation (5) still holds, so

$$
y^{\top} \Lambda^{-1} y = x^{\top} R\, \Lambda^{-1} R^{\top} x . \tag{6}
$$

Now set $$\Sigma = R \Lambda R^{\top}$$. Because $$R$$ is orthogonal, $$R^{-1} = R^{\top}$$, and therefore $$\Sigma^{-1} = R \Lambda^{-1} R^{\top}$$ — precisely the matrix sitting in the middle of (6). The exponent is $$x^{\top} \Sigma^{-1} x$$, which is equation (2). The covariance is not an extra assumption; it is what the per-axis widths become once arbitrary orientation is allowed.

**Why it is stored as a rotation and a scale.** The six free numbers of $$\Sigma$$ are not optimised directly. As the paper puts it, covariance matrices "have physical meaning only when they are positive semi-definite", and gradient descent "cannot be easily constrained to produce such valid matrices". So the ellipsoid is parameterised instead by

$$
\Sigma = R S S^{\top} R^{\top} , \qquad S = \mathrm{diag}(s_1, s_2, s_3) , \tag{7}
$$

with a three-vector $$s$$ for scale and a quaternion for $$R$$, normalised to unit length. Any $$s$$ and any quaternion yield a legal ellipsoid, so no update can push the representation outside the set of valid covariances. Comparing (7) with (5), $$S S^{\top} = \mathrm{diag}(s_i^2) = \Lambda$$, so the stored scales are the per-axis standard deviations.

### No neural network

The paper states plainly that its Gaussians "achieve faster rendering speed and better quality *without neural components*", and that is worth taking literally, because the method is otherwise built out of the ordinary machinery of deep learning. It uses automatic differentiation, stochastic gradient descent in a standard GPU framework, and a differentiable renderer whose image loss — an $$\mathcal{L}_1$$ term combined with D-SSIM, at $$\lambda = 0.2$$ — is backpropagated to the scene.

So the tools are the usual ones. What is missing is a model. The parameters being optimised are not the weights of anything; they are the scene itself, one tuple per Gaussian: position, opacity, anisotropic covariance, and spherical harmonic coefficients for colour. The representation is **explicit** — the numbers are the primitives.

The contrast the paper draws is with NeRF, which "build[s] on continuous scene representations, typically optimizing a Multi-Layer Perceptron". There the scene is **implicit**: it lives in the weights, and finding the density and colour at a point requires a forward pass through the network. No individual weight means anything on its own, and you cannot point at one and say that it is the corner of the table. In a splat the parameters are exactly the visible, editable fog patches of the previous section, and rendering is projecting and blending them with no network to query.

Fitting a polynomial's coefficients by gradient descent is the same situation in miniature. The optimisation is real; the model is still a polynomial.

There is a second difference, easy to miss and arguably larger. 3DGS optimises each scene from scratch. There is no training set spanning scenes, nothing generalisable is learned, and a new capture means running the whole procedure again. That places it closer to classical inverse rendering than to deep learning in the usual sense. Feed-forward models such as VGGT or Depth Anything 3 are the ones that genuinely learn: trained across many scenes, then producing geometry for an unseen one in a single pass.

### An upgraded point cloud

The shortest way to place the representation among older ones is this: it is a point cloud where every point has been given more to carry. A classical point is a coordinate and nothing else — no size, no orientation, no transparency. A Gaussian is that same coordinate plus a size, an orientation, an opacity, and a colour that changes with the direction you view it from.

The paper arrives from that direction as well. It begins with the sparse point cloud that Structure-from-Motion produces anyway and turns those points into Gaussians; its own subject classification files it under point-based models; and it positions itself against earlier point methods that treated each point as a small planar circle with a normal, noting that Gaussians instead "do not require normals".

The storage makes the continuity literal. The reference implementation saves a trained scene as a `.ply` file — the ordinary point-cloud format — with one vertex per Gaussian and the extra properties as extra fields: position, then opacity, three scales, a four-component rotation, and the spherical harmonic coefficients. It even writes the `nx, ny, nz` normal fields that every point cloud carries, filled with zeros, because Gaussians have no use for them and the format expects them to be there.

### References

1. B. Kerbl, G. Kopanas, T. Leimkühler, G. Drettakis, "3D Gaussian Splatting for Real-Time Radiance Field Rendering," *ACM Transactions on Graphics*, vol. 42, no. 4, 2023. [arXiv:2308.04079](https://arxiv.org/abs/2308.04079).
