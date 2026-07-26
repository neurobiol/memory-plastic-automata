from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional
import hashlib, json, math
import numpy as np

EPS = 1e-12

@dataclass(frozen=True)
class SimConfig:
    geometry: str
    formalism: str
    plasticity: str
    intrinsic_enabled: bool
    structural_enabled: bool
    schedule: str
    task: str
    seed: int
    L: int
    T: int
    snapshot_every: int = 50
    metric_stride: int = 10
    p0: float = 0.20
    gamma: float = 0.62
    sigma_birth: float = 0.60
    sigma_survive: float = 0.60
    memory_strength: float = 0.30
    tau_memory: float = 30.0
    alpha_async: float = 0.50
    sequential_events_per_sweep: float = 1.0
    block_fraction: float = 0.125
    eta_weight: float = 0.010
    weight_decay: float = 0.002
    weight_sum: float = 8.0
    intrinsic_target_activity: float = 0.42
    eta_intrinsic: float = 0.002
    intrinsic_bias_limit: float = 0.30
    structural_interval: int = 40
    structural_target_fraction: float = 0.75
    structural_rewire_probability: float = 0.25
    structural_min_degree: int = 2
    structural_utility_tau: float = 50.0
    structural_swap_tolerance: float = 0.01
    theta_input: float = 0.45
    theta_memory: float = 0.20
    theta_phase: float = 0.10
    dephase: float = 0.25
    diagonal_ablation: bool = False
    imprint_start: int = 100
    imprint_duration: int = 50
    imprint_strength: float = 0.90
    second_imprint_start: int = 260
    second_imprint_duration: int = 50
    lesion_time: int = 300
    second_lesion_time: int = 400
    lesion_fraction: float = 0.08
    save_dense: bool = False
    profile: str = "main"
    sensitivity_point: int = -1


def stable_int(text: str) -> int:
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=4).digest(), "little")


def rng_for(seed: int, label: str) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([int(seed), stable_int(label)]))


def clip01(a: np.ndarray) -> np.ndarray:
    return np.clip(a, 0.0, 1.0)


def pearson_map(a: np.ndarray, b: np.ndarray) -> float:
    av = a.ravel() - float(a.mean())
    bv = b.ravel() - float(b.mean())
    den = math.sqrt(float(np.sum(av * av) * np.sum(bv * bv)))
    return float(np.sum(av * bv) / (den + EPS))


def binary_entropy(p: np.ndarray) -> float:
    q = np.clip(p, EPS, 1 - EPS)
    return float(np.mean(-(q * np.log2(q) + (1 - q) * np.log2(1 - q))))


def geometry_degree(g: str) -> int:
    return {"square_vn": 4, "square_moore": 8, "hex_cells": 6, "honeycomb": 3,
            "extended_moore_r2": 24, "extended_hex_r2": 18, "honeycomb_nnn": 9}[g]


def geometry_family(g: str) -> str:
    if g in {"square_vn", "square_moore", "extended_moore_r2"}: return "square"
    if g in {"hex_cells", "extended_hex_r2"}: return "hex"
    return "honeycomb"


def cell_coordinates(L: int, geometry: str) -> Tuple[np.ndarray, np.ndarray]:
    yy, xx = np.mgrid[0:L, 0:L]
    if geometry_family(geometry) == "square":
        return xx.astype(float), yy.astype(float)
    return xx.astype(float) + 0.5 * (yy % 2), yy.astype(float) * (math.sqrt(3) / 2)


def _hex_ring_offsets(radius: int) -> List[Tuple[int, int]]:
    out = set()
    for parity in (0, 1):
        for dq in range(-radius, radius + 1):
            for dr in range(-radius, radius + 1):
                ds = -dq - dr
                if max(abs(dq), abs(dr), abs(ds)) <= radius and (dq, dr) != (0, 0):
                    r0 = parity
                    x0 = (r0 - (r0 & 1)) // 2
                    rr = r0 + dr
                    xx = dq + (rr - (rr & 1)) // 2
                    out.add((dr, xx - x0))
    pts = []
    for dr, dc in out:
        x = dc + 0.5 * (dr % 2)
        y = dr * math.sqrt(3) / 2
        pts.append((x * x + y * y, dr, dc))
    pts.sort()
    need = 3 * radius * (radius + 1)
    return [(dr, dc) for _, dr, dc in pts[:need]]


def neighbor_offsets_by_row(g: str) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
    if g == "square_vn":
        x = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return x, x
    if g == "square_moore":
        x = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]
        return x, x
    if g == "extended_moore_r2":
        x = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3) if (dy, dx) != (0, 0)]
        return x, x
    if g == "hex_cells":
        return [(-1,-1),(-1,0),(0,-1),(0,1),(1,-1),(1,0)], [(-1,0),(-1,1),(0,-1),(0,1),(1,0),(1,1)]
    if g == "extended_hex_r2":
        x = _hex_ring_offsets(2)
        return x, x
    if g == "honeycomb":
        return [(-1,0),(1,0),(0,1)], [(-1,0),(1,0),(0,-1)]
    if g == "honeycomb_nnn":
        return [(-1,0),(1,0),(0,1),(-1,-1),(-1,1),(1,-1),(1,1),(0,-1),(-2,0)], [(-1,0),(1,0),(0,-1),(-1,-1),(-1,1),(1,-1),(1,1),(0,1),(2,0)]
    raise KeyError(g)


def precompute_neighbors(L: int, g: str) -> Tuple[np.ndarray, np.ndarray]:
    even, odd = neighbor_offsets_by_row(g)
    K = max(len(even), len(odd))
    nr = np.zeros((K, L, L), np.int16)
    nc = np.zeros((K, L, L), np.int16)
    cols = np.arange(L)
    for r in range(L):
        offs = odd if r % 2 else even
        for k, (dr, dc) in enumerate(offs):
            nr[k, r, :] = (r + dr) % L
            nc[k, r, :] = (cols + dc) % L
    return nr, nc


def gather(a: np.ndarray, nr: np.ndarray, nc: np.ndarray) -> np.ndarray:
    K, L, _ = nr.shape
    out = np.empty((K, L, L), a.dtype)
    for k in range(K):
        for r in range(L):
            out[k, r, :] = a[nr[k, r, :], nc[k, r, :]]
    return out


def make_pattern(L: int, g: str, kind: str) -> np.ndarray:
    X, Y = cell_coordinates(L, g)
    x = X - X.mean(); y = Y - Y.mean(); s = max(abs(x).max(), abs(y).max(), 1)
    x /= s; y /= s; r = np.sqrt(x * x + y * y)
    p = np.zeros((L, L), float)
    if kind == "A":
        p[((r > .28) & (r < .36)) | ((((abs(x) < .04) | (abs(y) < .04))) & (r < .40))] = 1
    else:
        p[(((abs(y - x) < .05) | (abs(y + x) < .05)) & (r < .42)) | (((x - .28) ** 2 + (y + .28) ** 2 < .02) | ((x + .28) ** 2 + (y - .28) ** 2 < .02))] = 1
    return p


def make_lesion_mask(L: int, g: str, fraction: float, which: int = 1) -> np.ndarray:
    X, Y = cell_coordinates(L, g)
    x = (X - X.mean()) / (np.max(abs(X - X.mean())) + EPS)
    y = (Y - Y.mean()) / (np.max(abs(Y - Y.mean())) + EPS)
    rad = max(.06, math.sqrt(max(fraction, 1e-6)) * .35)
    cx, cy = ((0, 0) if which == 1 else (.3, -.25))
    return (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad


def morphology(p: np.ndarray, nr: np.ndarray, nc: np.ndarray) -> Dict[str, float]:
    neigh = gather(p, nr, nc)
    centered = p - p.mean()
    F = abs(np.fft.fft2(centered)) ** 2
    F[0, 0] = 0
    local = neigh.mean(0)
    codes = np.clip((local * 4).astype(int), 0, 3)
    counts = np.bincount(codes.ravel(), minlength=4).astype(float)
    probs = counts[counts > 0] / counts.sum()
    return {
        "spectral_peak_fraction": float(F.max() / (F.sum() + EPS)),
        "orientation_anisotropy": float(np.std(np.mean(neigh - p[None, :, :], axis=(1, 2))) / (np.mean(abs(neigh - p[None, :, :])) + EPS)),
        "neighbor_pattern_entropy": float(-np.sum(probs * np.log2(probs))),
    }


def init_state(cfg: SimConfig) -> Dict[str, np.ndarray]:
    p = (rng_for(cfg.seed, "init").random((cfg.L, cfg.L)) < cfg.p0).astype(float)
    d = {"p": p.copy(), "m": p.copy(), "bias": np.zeros_like(p)}
    if cfg.formalism == "ql":
        d.update(x=np.zeros_like(p), y=np.zeros_like(p), z=2 * p - 1)
    return d


def init_connectivity(cfg: SimConfig, K: int):
    active = np.ones((K, cfg.L, cfg.L), bool)
    if cfg.structural_enabled:
        active[:] = False
        rng = rng_for(cfg.seed, "struct_init")
        target = max(cfg.structural_min_degree, min(K, int(round(cfg.structural_target_fraction * K))))
        for r in range(cfg.L):
            for c in range(cfg.L):
                active[rng.choice(K, target, replace=False), r, c] = True
    deg = np.maximum(active.sum(0), 1)
    weights = active.astype(float) * (cfg.weight_sum / deg)[None, :, :]
    return weights, np.zeros_like(weights)


def soft_target(p, inp, degree, cfg):
    # Input is already normalized by weight_sum, so use common centers across geometries.
    B = np.exp(-((inp - 3.0) ** 2) / (2 * cfg.sigma_birth ** 2))
    S = np.exp(-((inp - 2.5) ** 2) / (2 * cfg.sigma_survive ** 2))
    return clip01((1 - p) * B + p * S)


def stimulus(q, t, cfg, A, B):
    if cfg.task in {"imprint", "lesion", "repeated_lesion"} and cfg.imprint_start <= t < cfg.imprint_start + cfg.imprint_duration:
        q = (1 - cfg.imprint_strength) * q + cfg.imprint_strength * A
    if cfg.task == "order_ab":
        if cfg.imprint_start <= t < cfg.imprint_start + cfg.imprint_duration:
            q = (1 - cfg.imprint_strength) * q + cfg.imprint_strength * A
        if cfg.second_imprint_start <= t < cfg.second_imprint_start + cfg.second_imprint_duration:
            q = (1 - cfg.imprint_strength) * q + cfg.imprint_strength * B
    if cfg.task == "order_ba":
        if cfg.imprint_start <= t < cfg.imprint_start + cfg.imprint_duration:
            q = (1 - cfg.imprint_strength) * q + cfg.imprint_strength * B
        if cfg.second_imprint_start <= t < cfg.second_imprint_start + cfg.second_imprint_duration:
            q = (1 - cfg.imprint_strength) * q + cfg.imprint_strength * A
    return clip01(q)


def state_update(st, w, active, nr, nc, cfg, t, A, B, mask=None):
    p = st["p"]
    inp = np.sum(w * active * gather(p, nr, nc), axis=0)
    q = soft_target(p, inp + st["bias"], geometry_degree(cfg.geometry), cfg)
    q = clip01(q + cfg.memory_strength * .10 * (st["m"] - .5))
    q = stimulus(q, t, cfg, A, B)
    if cfg.formalism == "markov":
        new = clip01((1 - cfg.gamma) * p + cfg.gamma * q)
        st["p"][:] = new if mask is None else np.where(mask, new, p)
    else:
        x, y, z = st["x"], st["y"], st["z"]
        xn = (1 - cfg.dephase) * x + cfg.theta_input * (inp / (cfg.weight_sum + EPS) - .5)
        yn = (1 - cfg.dephase) * y + cfg.theta_memory * (st["m"] - .5) + cfg.theta_phase * x
        zn = (1 - cfg.gamma) * z + cfg.gamma * (2 * q - 1) + .10 * y
        if cfg.diagonal_ablation:
            xn[:] = 0
            yn[:] = 0
        norm = np.sqrt(xn * xn + yn * yn + zn * zn)
        cm = norm > 1
        xn[cm] /= norm[cm]; yn[cm] /= norm[cm]; zn[cm] /= norm[cm]
        if mask is None:
            st["x"][:] = xn; st["y"][:] = yn; st["z"][:] = zn; st["p"][:] = clip01((1 + zn) / 2)
        else:
            for k, a in (("x", xn), ("y", yn), ("z", zn)):
                st[k][mask] = a[mask]
            st["p"][mask] = clip01((1 + zn[mask]) / 2)


def memory_update(st, cfg, mask=None):
    if mask is None:
        st["m"] = (1 - 1 / cfg.tau_memory) * st["m"] + (1 / cfg.tau_memory) * st["p"]
        if cfg.intrinsic_enabled:
            st["bias"] += cfg.eta_intrinsic * (cfg.intrinsic_target_activity - st["p"])
    else:
        st["m"][mask] = (1 - 1 / cfg.tau_memory) * st["m"][mask] + (1 / cfg.tau_memory) * st["p"][mask]
        if cfg.intrinsic_enabled:
            st["bias"][mask] += cfg.eta_intrinsic * (cfg.intrinsic_target_activity - st["p"][mask])
    st["bias"] = np.clip(st["bias"], -cfg.intrinsic_bias_limit, cfg.intrinsic_bias_limit)


def plastic_update(st, w, active, utility, nr, nc, cfg, t):
    co = st["p"][None, :, :] * gather(st["p"], nr, nc)
    utility *= 1 - 1 / cfg.structural_utility_tau
    utility += (1 / cfg.structural_utility_tau) * co
    if cfg.plasticity == "plastic":
        w += cfg.eta_weight * (co - co.mean(0, keepdims=True)) * active
        w -= cfg.weight_decay * w
        w[:] = np.maximum(w, 0) * active
        den = w.sum(0, keepdims=True)
        zero = den[0] <= EPS
        if np.any(zero):
            w[:, zero] = active[:, zero].astype(float)
            den = w.sum(0, keepdims=True)
        w *= cfg.weight_sum / (den + EPS)
    adds = rems = 0
    if cfg.structural_enabled and (t + 1) % cfg.structural_interval == 0:
        K, L, _ = active.shape
        rng = rng_for(cfg.seed + t + 1, "rewire")
        target = max(cfg.structural_min_degree, min(K, int(round(cfg.structural_target_fraction * K))))
        for r in range(L):
            for c in range(L):
                if rng.random() > cfg.structural_rewire_probability:
                    continue
                act = np.where(active[:, r, c])[0]
                ina = np.where(~active[:, r, c])[0]
                if len(act) < target and len(ina):
                    k = ina[np.argmax(utility[ina, r, c])]
                    active[k, r, c] = True; w[k, r, c] = cfg.weight_sum / target; adds += 1
                elif len(act) > target:
                    k = act[np.argmin(utility[act, r, c])]
                    active[k, r, c] = False; w[k, r, c] = 0; rems += 1
                elif len(act) == target and len(act) and len(ina):
                    worst = act[np.argmin(utility[act, r, c])]
                    best = ina[np.argmax(utility[ina, r, c])]
                    if utility[best, r, c] > utility[worst, r, c] + cfg.structural_swap_tolerance:
                        active[worst, r, c] = False; w[worst, r, c] = 0; rems += 1
                        active[best, r, c] = True; w[best, r, c] = cfg.weight_sum / target; adds += 1
        den = w.sum(0, keepdims=True)
        zero = den[0] <= EPS
        if np.any(zero):
            deg = np.maximum(active.sum(0), 1)
            w[:, zero] = active[:, zero].astype(float)
            den = w.sum(0, keepdims=True)
        w *= cfg.weight_sum / (den + EPS)
    return adds, rems


def simulate(cfg: SimConfig, dense: bool = False):
    nr, nc = precompute_neighbors(cfg.L, cfg.geometry)
    K = nr.shape[0]
    st = init_state(cfg)
    w, utility = init_connectivity(cfg, K)
    active = w > 0
    A = make_pattern(cfg.L, cfg.geometry, "A")
    B = make_pattern(cfg.L, cfg.geometry, "B")
    lm1 = make_lesion_mask(cfg.L, cfg.geometry, cfg.lesion_fraction, 1)
    lm2 = make_lesion_mask(cfg.L, cfg.geometry, cfg.lesion_fraction, 2)
    traces = []
    store = {}
    times = []
    adds = rems = 0
    for t in range(cfg.T):
        if cfg.schedule == "synchronous":
            state_update(st, w, active, nr, nc, cfg, t, A, B)
            memory_update(st, cfg)
        elif cfg.schedule == "alpha_async":
            mask = rng_for(cfg.seed + t, "alpha").random((cfg.L, cfg.L)) < cfg.alpha_async
            state_update(st, w, active, nr, nc, cfg, t, A, B, mask)
            memory_update(st, cfg, mask)
        elif cfg.schedule == "block_async":
            rng = rng_for(cfg.seed + t, "block")
            idx = rng.permutation(cfg.L * cfg.L)
            block = max(1, int(cfg.block_fraction * cfg.L * cfg.L))
            for s in range(0, cfg.L * cfg.L, block):
                mask = np.zeros((cfg.L, cfg.L), bool)
                mask.flat[idx[s:s + block]] = True
                state_update(st, w, active, nr, nc, cfg, t, A, B, mask)
                memory_update(st, cfg, mask)
        elif cfg.schedule == "sequential":
            rng = rng_for(cfg.seed + t, "seq")
            events = int(cfg.sequential_events_per_sweep * cfg.L * cfg.L)
            for _ in range(events):
                mask = np.zeros((cfg.L, cfg.L), bool)
                mask[int(rng.integers(cfg.L)), int(rng.integers(cfg.L))] = True
                state_update(st, w, active, nr, nc, cfg, t, A, B, mask)
                memory_update(st, cfg, mask)
        else:
            raise KeyError(cfg.schedule)
        if cfg.task in {"lesion", "repeated_lesion"} and t == cfg.lesion_time:
            st["p"][lm1] = 0
            if cfg.formalism == "ql":
                st["x"][lm1] = 0; st["y"][lm1] = 0; st["z"][lm1] = -1
        if cfg.task == "repeated_lesion" and t == cfg.second_lesion_time:
            st["p"][lm2] = 0
            if cfg.formalism == "ql":
                st["x"][lm2] = 0; st["y"][lm2] = 0; st["z"][lm2] = -1
        a, r = plastic_update(st, w, active, utility, nr, nc, cfg, t)
        adds += a; rems += r; active = w > 0
        if dense and (t % cfg.snapshot_every == 0 or t == cfg.T - 1):
            times.append(t)
            for k in ("p", "m", "bias"):
                store.setdefault(k, []).append(st[k].astype(np.float32).copy())
            store.setdefault("active", []).append(active.astype(np.uint8).copy())
            if cfg.formalism == "ql":
                for k in ("x", "y", "z"):
                    store.setdefault(k, []).append(st[k].astype(np.float32).copy())
        if t % cfg.metric_stride == 0 or t == cfg.T - 1:
            p = st["p"]
            neigh = gather(p, nr, nc)
            m = morphology(p, nr, nc)
            traces.append({
                "activity": float(p.mean()),
                "entropy": binary_entropy(p),
                "autocorr": float(np.mean((p - p.mean())[None, :, :] * (neigh - neigh.mean((1, 2), keepdims=True))) / (np.var(p) + EPS)),
                "interface": float(np.mean(abs(neigh - p[None, :, :]))),
                "corr_A": pearson_map(p, A),
                "corr_B": pearson_map(p, B),
                **m,
            })
    tail = traces[max(0, len(traces) - max(3, len(traces) // 5)):]
    avg = lambda k: float(np.mean([x[k] for x in tail]))
    out = {
        "geometry": cfg.geometry,
        "formalism": cfg.formalism,
        "plasticity": cfg.plasticity,
        "intrinsic_enabled": int(cfg.intrinsic_enabled),
        "structural_enabled": int(cfg.structural_enabled),
        "schedule": cfg.schedule,
        "task": cfg.task,
        "seed": cfg.seed,
        "L": cfg.L,
        "T": cfg.T,
        "profile": cfg.profile,
        "sensitivity_point": cfg.sensitivity_point,
        "activity_late": avg("activity"),
        "entropy_late": avg("entropy"),
        "autocorr_late": avg("autocorr"),
        "interface_density_late": avg("interface"),
        "corr_A_late": avg("corr_A"),
        "corr_B_late": avg("corr_B"),
        "spectral_peak_fraction_late": avg("spectral_peak_fraction"),
        "orientation_anisotropy_late": avg("orientation_anisotropy"),
        "neighbor_pattern_entropy_late": avg("neighbor_pattern_entropy"),
        "structural_link_fraction_late": float(active.mean()),
        "structural_additions_total": adds,
        "structural_removals_total": rems,
        "bias_mean_late": float(st["bias"].mean()),
        "memory_mean_late": float(st["m"].mean()),
        "coherence_late": float(np.mean(np.sqrt(st["x"]**2 + st["y"]**2))) if cfg.formalism == "ql" else 0.0,
    }
    if cfg.task in {"lesion", "repeated_lesion"}:
        out["repair_reference_corr"] = pearson_map(st["p"], A)
    if cfg.task in {"order_ab", "order_ba"}:
        out["order_bias"] = out["corr_B_late"] - out["corr_A_late"]
    traj = None
    if dense:
        traj = {k: np.stack(v) for k, v in store.items()}
        traj.update(times=np.array(times, np.int32), pattern_A=A.astype(np.float32), pattern_B=B.astype(np.float32), lesion1=lm1.astype(np.uint8), lesion2=lm2.astype(np.uint8), config_json=np.array(json.dumps(asdict(cfg))))
    return out, traj
