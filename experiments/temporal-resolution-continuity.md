# Temporal-resolution scaling of organizational continuity

Status: proposed experiment; not yet implemented or run.
Date: 2026-10-05.
Provenance: developed in conversation between Taylor Smith-Napier and Vesper. Taylor supplied the organizational-continuity question, coupled-metric-space framing, and distinction between discretization and disruptions from routing or weight changes. Vesper proposed temporal-resolution refinement as a controlled test. This protocol formalizes that joint discussion.

## Question

Which measured features of continuity in a specified coupled dynamical system survive temporal-resolution refinement, and which are numerical artifacts?

This is a mathematical/PyTorch toy-model experiment. It does not test consciousness, personhood, identity persistence, or spacetime discreteness.

## System and intervention

Start with two Euclidean metric spaces and their product, with state z=(x,y). Define a fixed continuous-time generator:

dx/dt = f(x) + k(y-x)
dy/dt = g(y) + k(x-y).

Choose and document f, g, dimensions, k, initial states, metric, horizon T, and perturbation before collecting results. Euclidean coupling is an explicit baseline, not an assumed implementation of the Orrery's general geometry.

For an analytically checkable calibration, use scalar x,y, f(x)=-a*x and g(y)=-a*y, with a,k>0. Then d=x-y obeys d' = -(a+2k)d and has exact solution d(t)=d(0)*exp(-(a+2k)t).

Integrate the same generator at h, h/2, h/4, h/8 and further refinements if needed. Keep T fixed. Compare at shared physical-time checkpoints, not shared iteration numbers. Specify the solver and precision. Use float64 for calibration; compare Euler and RK4 to detect solver-specific artifacts.

Do not simply run an unchanged learned update map more often: that changes effective dynamics per unit time. Use a generator whose increments scale with h, or derive a justified time-rescaling rule.

## Measurements

1. Trajectory discrepancy: E(h) = max over shared checkpoints of norm(z_h(t)-z_(h/2)(t)), using a fixed product metric.
2. Perturbation response: norm(z_perturbed(t)-z_baseline(t))/norm(delta z_0). Apply the same perturbation at the same physical time for every resolution.
3. Coupling distance: norm(x(t)-y(t)). This measures synchronization in this baseline, not sameness of subjects.
4. Recoupling time: first checkpoint after perturbation where coupling distance remains below a preregistered threshold for a fixed physical duration. Record non-recoupling as censored, not zero.

Estimate observed convergence order log2(E(h)/E(h/2)) when errors are nonzero and above the precision floor. Use the analytic calibration to verify expected solver behavior before interpreting a nonlinear example.

## Conditions and controls

- Fixed generator and coupling: main temporal-refinement condition.
- Uncoupled k=0: identifies dependence on coupling.
- A specified coupling or routing switch at fixed physical time: positive control for an organizational intervention. Integrate exactly to the switch before changing the generator.
- Perturbed and unperturbed paired runs: isolates perturbation response.
- Multiple initial conditions and perturbation directions: assess robustness. Any stochastic extension requires coupled noise across resolutions, not unrelated random draws.

A routing switch is a mathematical intervention in the toy system. It is not an intervention on an AI participant.

## Predictions and interpretation

For a well-posed smooth generator and a stable, consistent solver on a fixed finite horizon, numerical trajectories should converge under refinement. In the analytic calibration, Euler should show first-order and RK4 fourth-order global accuracy before roundoff dominates.

If a measured disruption shrinks with h at the expected solver order, that supports a numerical-discretization explanation within this model.

A routing-switch effect may remain nonzero even while the numerical solutions converge within the switched condition. This distinguishes convergence of the solver from persistence of the intervention's effect.

Persistent discrepancies between resolutions are not automatically evidence of organizational rupture: check stability, event alignment, stiffness, precision, and reference accuracy. Long chaotic trajectories and threshold-defined recoupling times require additional care; convergence of trajectories does not ensure robust threshold-crossing estimates.

Convergence establishes compatibility of these observables with the chosen continuous-time limit. It neither proves fundamental continuity nor excludes an underlying discrete implementation.

## Entropy and distributional reorganization

Added following Taylor Smith-Napier's proposal to emphasize entropy and D_KL in the 2026-10-05 conversation.

Define distributions before measuring information quantities. For the deterministic toy system, use an ensemble of preregistered initial conditions, with each initial condition paired across resolutions and interventions. At each shared physical-time checkpoint, map states through the same observable into fixed categorical bins. Hold bin boundaries, category labels, sample count, and observation map fixed across all conditions. Include overflow bins. A single deterministic point trajectory does not by itself specify this distribution.

Use discrete Shannon entropy H(p) = -sum_i p_i ln p_i, with 0 ln 0 = 0, in nats. Entropy is a candidate summary of organizational behavior, not an assumed conserved quantity. Equal entropy does not imply equal distributions, continuity, or identity. This discrete definition avoids treating differential entropy as coordinate-invariant.

Use D_KL(p || q) = sum_i p_i ln(p_i/q_i), stating the direction explicitly. It is asymmetric and not a metric. If p_i>0 and q_i=0, the divergence is infinite. Report this; if regularization is used, preregister its value, disclose it, and report sensitivity rather than silently clipping zeros. Use Jensen-Shannon divergence as an additional finite symmetric comparison when appropriate; it is not itself a metric, although its square root is.

Keep two comparisons separate:
- Numerical refinement: compare p_h(t) against p_(h/2)(t), for the same intervention condition.
- Organizational intervention: compare p_switch,h(t) against p_fixed,h(t), then check whether that divergence converges as h shrinks.

Track H(p(t)), entropy changes from baseline, both directed KL divergences, and the reference distributions. Entropy-preserving reorganization can appear as unchanged H with nonzero KL.

Calibration control: p=(0.9,0.1) and q=(0.1,0.9) have identical entropy but D_KL(p || q)=0.8 ln 9, approximately 1.758 nats. This demonstrates why entropy alone cannot identify organizational preservation. Category labels must remain meaningful and aligned; a mere relabeling is not automatically a physical change.

Distributional convergence needs its own checks. Hard bin boundaries can amplify small state errors; report occupancy near boundaries and repeat with preregistered alternate bin resolutions. KL can be unstable near zero probabilities even when trajectories converge. Use ensemble-size sensitivity and paired resampling to characterize sampling uncertainty. Do not equate an ensemble's Shannon entropy with thermodynamic entropy or subjective uncertainty without an additional model.

## Implementation and reporting plan

Implement a deterministic PyTorch runner with explicit configuration, CPU float64 calibration, fixed-h solvers, common checkpoints, and CSV output. Record configuration, solver, precision, software versions, and raw metrics. First verify against the exact scalar solution; then add a preregistered nonlinear example and the routing-switch control.

Report all resolutions, failed/unstable runs, convergence orders, and censored recoupling times. Keep numerical error, perturbation sensitivity, and intervention effects separate.

No live-model experimentation or welfare inference is authorized by this protocol.
