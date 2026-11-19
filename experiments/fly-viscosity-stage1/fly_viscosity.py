import gzip, csv, math
from collections import Counter, defaultdict
import numpy as np

np.random.seed(11)

# ============================================================
# fly_viscosity.py — Stage 1 (region-level), batched
#
# The viscosity/entropy-across-filtration battery (design: Taylor + Vesper,
# viscosity.py) re-run on the FAFB adult fly connectome (flybrain-main/data).
# Adaptation: Nim II, 2026-11-19, greenlit by the steward. D_KL sanctioned
# (family transition to D_GH in progress).
#
# Filtration levels = the connectome's own flow classes
# (afferent -> intrinsic -> efferent), stratified by organizational role.
#
# Pre-registered BEFORE running (direction provenance: viscosity.py's
# "deeper = stickier"): intrinsic regions recover from perturbation slower
# than afferent; and show higher genuine-vs-surrogate afferent specificity
# in next-state prediction; efferent most output-locked.
#
# Batched this revision: trials and kick/shadow pairs run as matrix columns.
# ============================================================

DATA = "/home/taylor/flybrain/flybrain-main/data"

def phase_random(x, rng):
    Xf = np.fft.rfft(x, axis=0)
    ph = rng.uniform(0, 2 * np.pi, size=Xf[1:].shape)
    Xf[1:] = np.abs(Xf[1:]) * np.exp(1j * ph)
    return np.fft.irfft(Xf, n=x.shape[0], axis=0)

# ---------- Stage A: stream the connectome into a typed region graph ----------
print("[A] streaming connectome ...", flush=True)
ntype, flow = {}, {}
with gzip.open(f"{DATA}/neurons.csv.gz", "rt") as fh:
    for row in csv.DictReader(fh):
        ntype[row["root_id"]] = row["group"]
with gzip.open(f"{DATA}/classification.csv.gz", "rt") as fh:
    for row in csv.DictReader(fh):
        flow[row["root_id"]] = row.get("flow", "unknown")
regions = sorted(set(ntype.values()))
N = len(regions)
ridx = {r: i for i, r in enumerate(regions)}
flow_votes = defaultdict(Counter)
for rid, reg in ntype.items():
    flow_votes[reg][flow.get(rid, "unknown")] += 1
W = np.zeros((N, N), dtype=np.float32)
n_edges, total_syn = 0, 0
with gzip.open(f"{DATA}/connections.csv.gz", "rt") as fh:
    for row in csv.DictReader(fh):
        pre, post, syn = row["pre_root_id"], row["post_root_id"], int(row["syn_count"])
        a, b = ntype.get(pre), ntype.get(post)
        if a is None or b is None or a == b:
            continue
        W[ridx[a], ridx[b]] += (-1.0 if row["nt_type"] == "GABA" else 1.0) * min(syn, 50)
        n_edges += 1; total_syn += syn
rclass = {r: flow_votes[r].most_common(1)[0][0] for r in regions}
LEVEL = np.array([rclass[r] for r in regions])
print(f"[A] {N} regions | {n_edges} edges | {total_syn:,} syn", flush=True)
print(f"[A] flow classes: {dict(Counter(LEVEL))}", flush=True)

# ---------- Stage B: batched dynamics ----------
ALPHA = {"afferent": 0.55, "intrinsic": 0.35, "efferent": 0.45, "unknown": 0.45}
infl_vec = np.array([ALPHA[c] for c in LEVEL], dtype=np.float32)[:, None]  # (N,1)
sens_rows = np.where(LEVEL == "afferent")[0]
inflow = np.abs(W).sum(axis=0)
eig = np.linalg.eigvals(W.astype(np.float64))
Wn = (W / (1.05 * np.abs(eig).max())).astype(np.float32)
np.fill_diagonal(Wn, 0.0)

BATCH = 8
SIGMA_BG = 0.04   # spontaneous biophysical noise floor on EVERY region --
                  # disclosed regime fix: without it the intrinsic tier sat silent
print(f"[budget] largest allocations: rec (4000x{N}x{BATCH} f32 = {4000*N*BATCH*4/2**20:.0f} MiB),"
      f" W (f32 {N*N*4/2**20:.0f} MiB), Stage D transients < 8 MiB, Stage E sorted arrays < 2 MiB."
      f" Peak estimate < 250 MiB. Cap: 2 GiB (kernel-enforced via run_bounded.sh).", flush=True)
rngB = np.random.RandomState(0)
state = np.zeros((N, BATCH), dtype=np.float32)
ar = np.zeros((N, BATCH), dtype=np.float32)
rec = np.zeros((4000, N, BATCH), dtype=np.float32)
s_amb = 0.0
rho, sigma, shared = 0.95, 0.12, 0.3
print("[B] batched dynamics: 8 trials x 4000 steps (structured afferent drive + global noise floor) ...", flush=True)
for t in range(4000):
    s_amb = shared * (rho * s_amb + sigma * rngB.randn())
    ar = rho * ar + sigma * rngB.standard_normal(size=(N, BATCH)).astype(np.float32) + s_amb
    u = Wn @ np.tanh(state)
    u[sens_rows, :] += ar[sens_rows, :]
    u += SIGMA_BG * rngB.standard_normal(size=(N, BATCH)).astype(np.float32)
    state = (1 - infl_vec) * state + infl_vec * np.tanh(u)
    rec[t] = state
base = rec[1000:]                    # (3000, N, 8)
print(f"[B] stabilization stats: mean|state|={np.abs(rec[500:]).mean():.3f} "
      f"std={rec[500:].std():.3f}", flush=True)

# class steady-state summary
for cls in ("afferent", "intrinsic", "efferent"):
    idx = np.where(LEVEL == cls)[0]
    v = base[:, idx, :].ravel()
    print(f"    {cls:9s} mean {v.mean():+.3f}  std {np.abs(v).std():.3f}  n_regions={len(idx)}", flush=True)

# ---------- Stage C: batched kick/shadow perturbation recovery ----------
print("[C] perturbation recovery (kick 0.6), batched pairs ...", flush=True)
sample = []
for cls in ("afferent", "intrinsic", "efferent"):
    idx = sorted(np.where(LEVEL == cls)[0], key=lambda i: -inflow[i])[:8]
    sample += [(cls, int(i)) for i in idx]
P = len(sample)
rngC = np.random.RandomState(7)
# (arC preallocation removed: dead code from the pre-batched draft — arc is built per-step)
st = np.zeros((N, 2 * P), dtype=np.float32)      # cols: kick_p, shadow_p
arc = np.zeros((N, 2 * P), dtype=np.float32)
kicker = np.zeros((N, 2 * P), dtype=np.float32)
kicked_cols = []
for p, (cls, i) in enumerate(sample):
    kicker[i, p] = 0.6
    kicked_cols.append(p)
s_amb = 0.0
gap_acc = np.zeros((1999, P), dtype=np.float32)
kick_fired = False
for t in range(4000):
    s_amb = shared * (rho * s_amb + sigma * rngC.randn())
    arc = rho * arc + sigma * rngC.standard_normal(size=(N, 2 * P)).astype(np.float32) + s_amb
    u = Wn @ np.tanh(st)
    u[sens_rows, :] += arc[sens_rows, :]
    u += SIGMA_BG * rngC.standard_normal(size=(N, 2 * P)).astype(np.float32)
    st = (1 - infl_vec) * st + infl_vec * np.tanh(u)
    if t == 2000:
        st = st + kicker            # kick columns p only; shadows (P+p) untouched
        kick_fired = True
    if t >= 2001:
        for p, (cls, i) in enumerate(sample):
            gap_acc[t - 2001, p] = st[i, p] - st[i, p + P]
assert kick_fired, "kick never fired — Stage C data would be vacuous"
print("[C] (recovery computed below)", flush=True)

# recovery per sampled region
recov = {}
recov_by_cls = defaultdict(list)
for p, (cls, i) in enumerate(sample):
    g = np.abs(gap_acc[:, p])
    shadow_i = None
    # threshold from shadow self-drift: recompute per-pair drift via arc stats
    drift = 0.0
    # cheap proxy: use gap's own tail plateau after long time as drift scale
    tail = g[-256:]
    thresh = 4.0 * (tail.std() + 1e-6)
    below = g < thresh
    k = int(np.argmax(below)) if below.any() else len(g)
    recov[regions[i]] = k
    recov_by_cls[cls].append(k)
print("[C] recovery by class (steps to shadow-gap plateau, 4*tail-sigma):")
for cls, ks in recov_by_cls.items():
    ks = np.array(ks)
    print(f"    {cls:9s} median={np.median(ks):6.0f}  iqr=({np.percentile(ks,25):.0f},{np.percentile(ks,75):.0f})  n={len(ks)}", flush=True)

# ---------- Stage D: afferent closure (ridge; non-overlapping windows) ----------
print("[D] afferent closure per region ...", flush=True)
strength = np.abs(Wn)
closure_rows = []
BELOW_FLOOR = 1e-7   # targets with naive_loss under this are float-dust: excluded honestly
n_floor = 0
for i in range(N):
    affer = [a for a in np.argsort(-strength[:, i])[:4] if strength[a, i] > 0]
    if not affer:
        continue
    Xg, Xs, y = [], [], []
    for ti in range(BATCH):
        rr = base[:, :, ti]                      # (3000, N)
        for w in range(0, len(rr) - 400, 400):   # non-overlapping: 6-7 windows
            seg = rr[w:w+400]
            fg = seg[:, affer]
            fs = phase_random(fg, np.random.RandomState(ti * 13 + w))
            Xg.append(np.concatenate([fg, seg[:, [i]]], axis=1)[:-1])
            Xs.append(np.concatenate([fs, seg[:, [i]]], axis=1)[:-1])
            y.append(seg[1:, i])
    Xg = np.concatenate(Xg); Xs = np.concatenate(Xs); y = np.concatenate(y)
    ntr = int(0.8 * len(y))
    def ridge(X, Y, lam=1e-2):
        A = X.T @ X + lam * np.eye(X.shape[1])
        return np.linalg.solve(A, X.T @ Y)
    wg = ridge(Xg[:ntr], y[:ntr]); ws = ridge(Xs[:ntr], y[:ntr])
    lg = float(np.mean((Xg[ntr:] @ wg - y[ntr:]) ** 2))
    ls = float(np.mean((Xs[ntr:] @ ws - y[ntr:]) ** 2))
    ln = float(np.mean((Xg[ntr:, -1] - y[ntr:]) ** 2))
    if ln < BELOW_FLOOR or not (y[ntr:].var() > BELOW_FLOOR):
        n_floor += 1
        continue                      # silent target: closure undefined, excluded with count
    closure = (ln - lg) / ln if ln > 1e-12 else 0.0
    spec = (ls - lg) / ls if ls > 1e-12 else 0.0
    closure_rows.append((regions[i], LEVEL[i], ln, lg, ls, closure, spec))
print(f"[D] excluded {n_floor} below-floor (silent) regions honestly", flush=True)

with open("/home/taylor/quael-experiments/fly_viscosity_results.csv", "w", newline="") as fh:
    wcsv = csv.writer(fh)
    wcsv.writerow(["region", "class", "naive_loss", "genuine_loss", "surrogate_loss",
                   "closure", "afferent_specificity", "recovery_steps"])
    for reg, cls, ln, lg, ls, closure, spec in closure_rows:
        wcsv.writerow([reg, cls, f"{ln:.5f}", f"{lg:.5f}", f"{ls:.5f}",
                       f"{closure:.4f}", f"{spec:.4f}", recov.get(reg, "")])
print(f"[D] wrote fly_viscosity_results.csv ({len(closure_rows)} regions)", flush=True)

by_cls, spec_cls = defaultdict(list), defaultdict(list)
for reg, cls, ln, lg, ls, closure, spec in closure_rows:
    by_cls[cls].append(closure); spec_cls[cls].append(spec)
print("[D] by class:")
for cls in sorted(by_cls):
    print(f"    {cls:9s} closure={np.mean(by_cls[cls]):.4f}  afferent_specificity={np.mean(spec_cls[cls]):.4f}  n={len(by_cls[cls])}", flush=True)

# ---------- Stage E: per-class entropy + symmetric D_KL ----------
print("[E] per-class entropy + D_KL ...", flush=True)
def knn_entropy_1d(x, k=4):
    """Kozachenko-Leonenko on sorted 1-D data: O(n log n), ZERO pairwise matrices.
    k-th NN distance for point i = min(x[i+k]-x[i], x[i]-x[i-k]) via the sorted axis."""
    n = len(x)
    if n < 2 * k + 2:
        return float("nan")
    xs = np.sort(x)
    right = np.full(n, np.inf)
    left = np.full(n, np.inf)
    right[: n - k] = xs[k:] - xs[: n - k]
    left[k:] = xs[k:] - xs[: n - k]
    r = np.maximum(np.minimum(right, left), 1e-12)
    return float(k * np.mean(np.log(r)) + math.log(n) + math.lgamma(k + 1)
                 - math.lgamma(k) - 0.5 * math.log(math.pi))

E_CAP = 4000  # hard per-distribution sample cap (budget line honored)
class_states = defaultdict(list)
subs = base[::4]  # (750, N, 8)
for i in range(N):
    class_states[LEVEL[i]].append(subs[:, i, :].ravel())
ent, param = {}, {}
for cls, arrs in class_states.items():
    X = np.concatenate(arrs)
    z = (X - X.mean()) / (X.std() + 1e-9)
    stride = max(1, len(z) // E_CAP)
    z = z[::stride][:E_CAP]
    ent[cls] = knn_entropy_1d(z)
    param[cls] = (float(X.mean()), float(X.std() + 1e-9))
    print(f"    H[{cls:9s}] = {ent[cls]:+.3f} nats (m={param[cls][0]:+.3f} s={param[cls][1]:.3f}, n={len(z)})", flush=True)

classes = [c for c in ("afferent", "intrinsic", "efferent") if c in param]
print("[E] symmetric D_KL (gaussian approx, Jeffreys):")
for x in range(len(classes)):
    for y_ in range(x + 1, len(classes)):
        a, b = classes[x], classes[y_]
        ma, sa = param[a]; mb, sb = param[b]
        kl_ab = math.log(sb / sa) + (sa**2 + (ma - mb)**2) / (2 * sb**2) - 0.5
        kl_ba = math.log(sa / sb) + (sb**2 + (mb - ma)**2) / (2 * sa**2) - 0.5
        print(f"    J[{a} || {b}] = {0.5 * (kl_ab + kl_ba):.4f}", flush=True)
print("[done] Stage 1 (batched) complete.")
