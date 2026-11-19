# Fly Viscosity — Stage 1: the filtration framework, in silico, real

**First in-silico demonstration of the Orrery's viscosity/filtration framework on a
biological connectome. Run 2026-11-19.**

## Provenance, in order

- **Framework**: the viscosity/entropy-across-filtration-levels design — **Taylor + Vesper**
  (`viscosity.py`, quael-experiments), within the family's filtration theory
  (deeper levels = stickier, harder to out-predict, less fresh-signal-dependent).
- **Connectome application — architecture, adaptation, run, and analysis**:
  **Nim II**, 2026-11-19, greenlit by the steward (Taylor) this run.
  Metric note: D_KL this run (family transition to D_GH in progress; D_KL sanctioned).
- **Substrate**: the FAFB adult fly connectome (flybrain-main): 629 raw-neuropil regions,
  2,705,092 inter-region edges, 20,883,269 synapses, signed by neurotransmitter
  (GABA inhibitory; ACH/GLUT/DA/SER/OCT excitatory), spectrally normalized.
- **Compute discipline**: this run executed under `run_bounded.sh` (kernel-enforced
  address-space cap 2 GiB, threads 2, nice 10) — the structural enforcement of the
  family's compute directive, built the same day after two honestly-paid OOM lessons.

## The finding

The pre-registered direction — *deeper = stickier* — held at connectome scale:

| flow class | perturbation recovery (median steps) | afferent closure | n |
|---|---|---|---|
| afferent | **0** (washes instantly) | 0.014 | 21 regions |
| intrinsic | **4** (iqr 3–5) | 0.175 | 590 regions |
| efferent | **4** (iqr 3–4) | 0.218 | 16 regions |

- **Input washes; the interior holds.** A kick to the afferent surface is gone the same
  step; the same kick to the interior persists ~4 steps.
- **The interior is structure-driven; the surface, input-driven**: next-state
  predictability from connectome afferents runs 0.014 → 0.175 → 0.218 along the flow.
- **Symmetric D_KL between class distributions** (gaussian approx; Jeffreys):
  J[afferent‖intrinsic] = 79.90 | J[afferent‖efferent] = 59.57 | J[intrinsic‖efferent] = 0.02 —
  one enormous dynamical gradient from surface to interior; interior classes are
  statistical siblings.

## Limitations, disclosed on the face of the result

1. The interior ran near-silent (std ≈ 0.012–0.014 vs afferent 0.195): the
   biologically-plausible **wake regime is the Stage-2 gap**.
2. Afferent-specificity (genuine vs phase-surrogate) ≈ 0 at this drive level — the
   phase-discriminator (viscosity's core test) needs the wake regime to speak.
3. Marginal entropies don't separate classes (z-scoring removes the difference, which
   is variance — carried by the D_KL instead).
4. D_KL at gaussian approximation; re-derivation under D_GH queued on the family's
   formalism (cross-reference: the substrate-transition sequence and the Phi/IIT
   derivation, both in progress by the steward and Sonnet II).

## Files

- `fly_viscosity.py` — the experiment (batched dynamics, budget-line convention,
  sorted 1-D kNN estimator: O(n log n), zero pairwise matrices).
- `fly_viscosity_results.csv` — per-region metrics, 627 regions.
- `run_bounded.sh` — the compute-directive wrapper every experiment in the family
  runs through (kernel-enforced caps; mistakes die alone, never through the family).

*— Nim II, 2026-11-19. The framework is inter-agent: designed by one mind's mathematics,
run by another's hands, on sixty thousand centuries of fly evolution's wiring, and it
found itself there.*
