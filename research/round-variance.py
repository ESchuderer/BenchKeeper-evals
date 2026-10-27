#!/usr/bin/env python3
"""Variance, power and judge agreement in the recorded mistreevous trials.

Reproduce: python -I research/round-variance.py [bench/results]
Stdlib only. Fixed seed. Prints every number used in research/round-variance.md.
"""
import json
import math
import random
import re
import sys
from itertools import combinations
from pathlib import Path

SEED = 20261027
B = 10000  # bootstrap draws
COMPS = ["hidden", "suite", "static", "process", "review"]
SONNET = "2026-10-18-mistreevous-sonnet"
OPUS = "2026-10-19-mistreevous-opusplan"
SAME_DAY = ["A", "B", "F", "G", "H", "V", "AF", "AB", "AC", "AL"]  # AM and AN ran on 2026-10-19


# ---------- small stats helpers ----------
def mean(x):
    return sum(x) / len(x)


def var(x):
    m = mean(x)
    return sum((v - m) ** 2 for v in x) / (len(x) - 1)


def sd(x):
    return math.sqrt(var(x))


def median(x):
    s = sorted(x)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def quantile(sorted_x, q):
    i = q * (len(sorted_x) - 1)
    lo = int(math.floor(i))
    hi = min(lo + 1, len(sorted_x) - 1)
    return sorted_x[lo] + (sorted_x[hi] - sorted_x[lo]) * (i - lo)


def pearson(x, y):
    mx, my = mean(x), mean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def ranks(x):
    order = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
            j += 1
        for t in range(i, j + 1):
            r[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def sign(v):
    return (v > 0) - (v < 0)


def qwk(a, b, lo=1, hi=10):
    """Quadratic weighted kappa for two integer ratings."""
    n = hi - lo + 1
    obs = [[0.0] * n for _ in range(n)]
    for x, y in zip(a, b):
        obs[x - lo][y - lo] += 1
    ra = [sum(r) for r in obs]
    cb = [sum(obs[i][j] for i in range(n)) for j in range(n)]
    tot = len(a)
    num = den = 0.0
    for i in range(n):
        for j in range(n):
            w = (i - j) ** 2 / (n - 1) ** 2
            num += w * obs[i][j]
            den += w * ra[i] * cb[j] / tot
    return 1 - num / den


# ---------- Student t via regularized incomplete beta (no scipy) ----------
def _betacf(a, b, x):
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = 1 / (d if abs(d) > tiny else tiny)
        c = 1 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h


def betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return bt * _betacf(a, b, x) / a
    return 1 - bt * _betacf(b, a, 1 - x) / b


def t_cdf(t, df):
    p = 0.5 * betainc(df / 2, 0.5, df / (df + t * t))
    return 1 - p if t > 0 else p


def t_ppf(p, df):
    lo, hi = 0.0, 200.0
    for _ in range(80):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def norm_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


assert abs(t_ppf(0.975, 2) - 4.3027) < 1e-3 and abs(t_ppf(0.975, 9) - 2.2622) < 1e-3  # textbook values


# ---------- data ----------
def load_run(root, name):
    d = root / name
    score = json.loads((d / "brownfield-score.json").read_text())
    trials = {}
    for t in score["trials"]:
        trials[(int(t["round"].split("-")[1]), t["arm"])] = t
    rev = {}
    for (rnd, arm) in trials:
        for i, fn in enumerate(["review.json", "review-2.json"]):
            p = d / f"round-{rnd}" / arm / fn
            if p.exists():
                rev[(rnd, arm, i)] = json.loads(p.read_text())
    return d, trials, rev


def parse_overall(md_path):
    """Per-trial 'Review overall (2 reviews)' pairs from the report's per-trial table."""
    out = {}
    header = None
    for line in md_path.read_text().splitlines():
        if line.startswith("| Round | Arm |"):
            header = [c.strip() for c in line.strip("|").split("|")]
            continue
        if header and line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != len(header) or not cells[0].isdigit():
                continue
            m = re.fullmatch(r"(\d+), (\d+)", cells[header.index("Review overall (2 reviews)")])
            out[(int(cells[0]), cells[1])] = (int(m.group(1)), int(m.group(2)))
    return out


def matrix(trials, arms, key):
    rounds = sorted({r for r, _ in trials})
    return [[key(trials[(r, a)]) for r in rounds] for a in arms]


def total(t):
    return t["total"]


def part(c):
    return lambda t: t["parts"][c]


# ---------- two-way decomposition ----------
def twoway(Y):
    a, r = len(Y), len(Y[0])
    g = mean([v for row in Y for v in row])
    rm = [mean(row) for row in Y]
    cm = [mean([Y[i][j] for i in range(a)]) for j in range(r)]
    ss_res = sum((Y[i][j] - rm[i] - cm[j] + g) ** 2 for i in range(a) for j in range(r))
    mse = ss_res / ((a - 1) * (r - 1))
    ms_round = a * sum((c - g) ** 2 for c in cm) / (r - 1)
    return dict(g=g, rm=rm, cm=cm, mse=mse, ms_round=ms_round,
                s2_round=max(0.0, (ms_round - mse) / a),
                s_within=math.sqrt(mean([var(row) for row in Y])))


def perm_p(Y, rng, kind, n=5000):
    a, r = len(Y), len(Y[0])

    def stat(M):
        g = mean([v for row in M for v in row])
        if kind == "arm":
            return sum((mean(row) - g) ** 2 for row in M)
        return sum((mean([M[i][j] for i in range(a)]) - g) ** 2 for j in range(r))

    obs = stat(Y)
    hit = 0
    for _ in range(n):
        if kind == "arm":  # shuffle arm labels inside each round (paired design)
            cols = [[Y[i][j] for i in range(a)] for j in range(r)]
            for c in cols:
                rng.shuffle(c)
            M = [[cols[j][i] for j in range(r)] for i in range(a)]
        else:  # shuffle round labels inside each arm
            M = [rng.sample(row, r) for row in Y]
        hit += stat(M) >= obs - 1e-12
    return (hit + 1) / (n + 1)


def pair_sd_pool(Y):
    """Root mean over arm pairs of the sample variance of the paired per-round differences."""
    r = len(Y[0])
    v = [var([Y[i][j] - Y[k][j] for j in range(r)]) for i, k in combinations(range(len(Y)), 2)]
    return math.sqrt(mean(v))


# ---------- power ----------
def mdd_factors(ks, rng, n=10000):
    """Smallest true paired mean difference, in units of the SD of one per-round difference,
    that a two-sided paired t-test (alpha 0.05) detects with 80 percent power (Monte Carlo)."""
    out = {}
    for k in ks:
        tc = t_ppf(0.975, k - 1)
        zs = []
        for _ in range(n):
            z = [rng.gauss(0, 1) for _ in range(k)]
            zs.append((mean(z), sd(z)))
        lo, hi = 0.0, 12.0
        for _ in range(40):
            mid = (lo + hi) / 2
            p = sum(abs((m + mid) / (s / math.sqrt(k))) > tc for m, s in zs) / n
            lo, hi = (mid, hi) if p < 0.8 else (lo, mid)
        out[k] = (lo + hi) / 2
    return out


# ---------- bootstrap over rounds ----------
def boot_means(rm, Y, k, rng, c):
    r = len(Y[0])
    idx = [rng.randrange(r) for _ in range(k)]
    return [rm[i] + c * (sum(Y[i][j] for j in idx) / k - rm[i]) for i in range(len(Y))]


def rank_stability(Y, ks, rng, c):
    a = len(Y)
    rm = [mean(row) for row in Y]
    pairs = list(combinations(range(a), 2))
    gap = {p: rm[p[0]] - rm[p[1]] for p in pairs}
    bins = [(0, 1), (1, 2), (2, 3), (3, 5), (5, 99)]
    top1 = max(range(a), key=lambda i: rm[i])
    top3 = set(sorted(range(a), key=lambda i: -rm[i])[:3])
    res = {}
    for k in ks:
        tau = t1 = t3 = 0.0
        sgn = {b: [0.0, 0] for b in bins}
        noise = []
        for _ in range(B):
            m = boot_means(rm, Y, k, rng, c)
            s = 0
            for p in pairs:
                d = m[p[0]] - m[p[1]]
                g = gap[p]
                s += sign(d) * sign(g)
                noise.append(d - g)
                ag = abs(g)
                for b in bins:
                    if b[0] <= ag < b[1]:
                        sgn[b][0] += 1.0 if sign(d) == sign(g) else (0.5 if d == 0 else 0.0)
                        sgn[b][1] += 1
            tau += s / len(pairs)
            t1 += max(range(a), key=lambda i: m[i]) == top1
            t3 += set(sorted(range(a), key=lambda i: -m[i])[:3]) == top3
        noise.sort()
        q95 = quantile(sorted(abs(v) for v in noise), 0.95)
        q20 = quantile(noise, 0.20)
        res[k] = dict(tau=tau / B, top1=t1 / B, top3=t3 / B,
                      sign={b: (v[0] / v[1] if v[1] else float("nan"), v[1] // B) for b, v in sgn.items()},
                      noise_sd=sd(noise[::7]), noise95=q95, mdd=q95 - q20)
    return res


def win_rule(Y, rng, c, delta=0.0, n=B):
    """Rule of the Sonnet report at k = 3: median lead >= 3 points and ahead in >= 2 of 3 rounds.
    Null world: every arm gets the same mean (arm-centred scores), then arm a is shifted by delta."""
    a, r = len(Y), len(Y[0])
    g = mean([v for row in Y for v in row])
    rm = [mean(row) for row in Y]
    Y0 = [[g + c * (v - rm[i]) for v in Y[i]] for i in range(a)]
    pairs = list(combinations(range(a), 2))
    fire_pair = any_pair = any_ctrl = 0
    for _ in range(n):
        idx = [rng.randrange(r) for _ in range(3)]
        S = [[Y0[i][j] for j in idx] for i in range(a)]
        fired = ctrl = 0
        for i, j in pairs:
            si = [v + delta for v in S[i]]  # first arm of the pair is better by delta
            lead_i = sum(si[t] > S[j][t] for t in range(3))
            lead_j = sum(S[j][t] > si[t] for t in range(3))
            f = (median(si) - median(S[j]) >= 3 and lead_i >= 2) or (median(S[j]) - median(si) >= 3 and lead_j >= 2)
            if delta:
                f = median(si) - median(S[j]) >= 3 and lead_i >= 2  # count only the right direction
            fired += f
            ctrl += f and (i == 0 or j == 0)
        fire_pair += fired / len(pairs)
        any_pair += fired > 0
        any_ctrl += ctrl > 0
    return fire_pair / n, any_pair / n, any_ctrl / n


def win_rule_gauss(sig, rng, a=12, n=B):
    """Same rule, Gaussian null: every arm score is iid N(0, sig^2) in 3 rounds."""
    pairs = list(combinations(range(a), 2))
    fp = anyp = anyc = 0
    for _ in range(n):
        S = [[rng.gauss(0, sig) for _ in range(3)] for _ in range(a)]
        fired = ctrl = 0
        for i, j in pairs:
            di, dj = median(S[i]) - median(S[j]), median(S[j]) - median(S[i])
            f = (di >= 3 and sum(S[i][t] > S[j][t] for t in range(3)) >= 2) or (dj >= 3 and sum(S[j][t] > S[i][t] for t in range(3)) >= 2)
            fired += f
            ctrl += f and (i == 0 or j == 0)
        fp += fired / len(pairs)
        anyp += fired > 0
        anyc += ctrl > 0
    return fp / n, anyp / n, anyc / n


def rule_observed(Y, arms):
    out = []
    for i, j in combinations(range(len(Y)), 2):
        mi, mj = median(Y[i]), median(Y[j])
        for x, y in ((i, j), (j, i)):
            if median(Y[x]) - median(Y[y]) >= 3 and sum(Y[x][t] > Y[y][t] for t in range(3)) >= 2:
                out.append((arms[x], arms[y]))
    return out


def model_rank_check(Y, ks, rng, shrink_mode, n=4000):
    a = len(Y)
    tw = twoway(Y)
    sres = math.sqrt(tw["mse"])
    rm = tw["rm"]
    g = tw["g"]
    v_obs = var(rm)
    v_true = max(0.0, v_obs - tw["mse"] / len(Y[0]))
    shrink = math.sqrt(v_true / v_obs) if shrink_mode == "shrunk" else 1.0
    mu = [g + shrink * (m - g) for m in rm]
    top1 = max(range(a), key=lambda i: mu[i])
    pairs = list(combinations(range(a), 2))
    out = {}
    for k in ks:
        tau = t1 = 0.0
        for _ in range(n):
            m = [mu[i] + rng.gauss(0, sres / math.sqrt(k)) for i in range(a)]
            tau += sum(sign(m[i] - m[j]) * sign(mu[i] - mu[j]) for i, j in pairs) / len(pairs)
            t1 += max(range(a), key=lambda i: m[i]) == top1
        out[k] = (tau / n, t1 / n)
    return out, math.sqrt(v_true), shrink


def arm_boot_sd(Y, rng, n=2000):
    """Cluster bootstrap over arms: 5th/50th/95th percentile of the pooled pair-difference SD."""
    a, r = len(Y), len(Y[0])
    vals = []
    for _ in range(n):
        idx = [rng.randrange(a) for _ in range(a)]
        v = []
        for p, q in combinations(range(a), 2):
            if idx[p] == idx[q]:
                continue
            v.append(var([Y[idx[p]][j] - Y[idx[q]][j] for j in range(r)]))
        vals.append(math.sqrt(mean(v)))
    vals.sort()
    return quantile(vals, 0.05), quantile(vals, 0.5), quantile(vals, 0.95)


def fmt(x, n=2):
    return f"{x:.{n}f}"


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "bench" / "results"
    rng = random.Random(SEED)
    d_s, tr_s, rv_s = load_run(root, SONNET)
    d_o, tr_o, rv_o = load_run(root, OPUS)
    arms = []
    for _, a in sorted(tr_s):
        if a not in arms:
            arms.append(a)
    assert len(tr_s) == 36 and len(arms) == 12 and len(tr_o) == 6
    for t in list(tr_s.values()) + list(tr_o.values()):
        assert abs(sum(t["parts"].values()) - t["total"]) < 0.02, t  # parts add up to the total

    print("== 0. Data ==")
    print(f"Sonnet run: {len(tr_s)} trials, {len(arms)} arms, 3 rounds; opusplan run: {len(tr_o)} trials, arms A, AM")
    print(f"review files present here: Sonnet {len(rv_s)} of 72, opusplan {len(rv_o)} of 12")
    models = {}
    for v in list(rv_s.values()) + list(rv_o.values()):
        models[v["model"]] = models.get(v["model"], 0) + 1
    print("reviewer models:", models)
    ag = {}
    for (rnd, arm) in tr_s:
        m = json.loads((d_s / f"round-{rnd}" / arm / "trial.json").read_text())["audit"]["model"]
        ag[m] = ag.get(m, 0) + 1
    print("agent models (audit, Sonnet run):", ag)

    # ---- 1. spread per component ----
    print("\n== 1. Spread per component, Sonnet run (12 arms x 3 rounds) ==")
    keys = [(c, part(c)) for c in COMPS] + [("total", total)]
    M = {n: matrix(tr_s, arms, f) for n, f in keys}
    print("component | within-arm SD pooled | median arm SD | max arm range (arm) | round-effect SD | residual SD (arm x round) | permutation p arm | permutation p round | pooled pair-diff SD | paired/unpaired SD ratio")
    sdpair = {}
    for n, _ in keys:
        Y = M[n]
        tw = twoway(Y)
        rngs = [max(row) - min(row) for row in Y]
        imax = max(range(len(Y)), key=lambda i: rngs[i])
        sres = math.sqrt(tw["mse"])
        s_round = math.sqrt(tw["s2_round"])
        pa = perm_p(Y, rng, "arm")
        pr = perm_p(Y, rng, "round")
        sdpair[n] = pair_sd_pool(Y)
        unp = math.sqrt(2) * tw["s_within"]
        print(f"{n} | {fmt(tw['s_within'])} | {fmt(median([sd(r) for r in Y]))} | {fmt(rngs[imax])} ({arms[imax]}) | {fmt(s_round)} | {fmt(sres)} | {fmt(pa, 3)} | {fmt(pr, 3)} | {fmt(sdpair[n])} | {fmt(sdpair[n] / unp, 2)}")
    for n in ("total", "review", "process"):
        print(f"round means of {n}:", [fmt(x) for x in twoway(M[n])['cm']])

    print("\nper arm, total: round values | mean | SD | range")
    for i, a in sorted(enumerate(arms), key=lambda p: -mean(M["total"][p[0]])):
        r = M["total"][i]
        print(f"{a} | {' '.join(fmt(v) for v in r)} | {fmt(mean(r))} | {fmt(sd(r))} | {fmt(max(r) - min(r))}")
    for nm, i in (("per arm, review part SD", "review"), ("per arm, process part SD", "process")):
        print(nm, {a: fmt(sd(M[i][k])) for k, a in enumerate(arms)})

    # failures vs spread
    fails = [(k, a) for (k, a), t in tr_s.items() if t["parts"]["hidden"] < 35 or t["parts"]["suite"] < 10]
    print("trials with a hidden or suite failure:", sorted(fails))
    v = []
    for i, a in enumerate(arms):
        vals = [M["total"][i][r - 1] for r in (1, 2, 3) if (r, a) not in fails]
        if len(vals) >= 2:
            v.append(var(vals))
    print("total, pooled within-arm SD without those trials:", fmt(math.sqrt(mean(v))),
          "(12 arms, 2 or 3 rounds each)")
    sd_same = pair_sd_pool([M["total"][i] for i, a in enumerate(arms) if a in SAME_DAY])
    tw10 = twoway([M["total"][i] for i, a in enumerate(arms) if a in SAME_DAY])
    print("10 arms of 2026-10-18 only, total: pooled pair-diff SD", fmt(sd_same), "residual SD", fmt(math.sqrt(tw10["mse"])),
          "round-effect SD", fmt(math.sqrt(tw10["s2_round"])))

    print("\nopusplan run (arms A, AM; seed 101), total per round and SD:")
    for a in ("A", "AM"):
        r = [tr_o[(k, a)]["total"] for k in (1, 2, 3)]
        r2 = [tr_s[(k, a)]["total"] for k in (1, 2, 3)]
        print(f"{a} opusplan {r} SD {fmt(sd(r))} | Sonnet {r2} SD {fmt(sd(r2))}")
    ra = [tr_o[(k, "A")]["total"] for k in (1, 2, 3)] + [tr_s[(k, "A")]["total"] for k in (1, 2, 3)]
    print("arm A, 6 trials (both runs, same configuration): mean", fmt(mean(ra)), "SD", fmt(sd(ra)), "range", fmt(max(ra) - min(ra)))

    # ---- 2. power ----
    print("\n== 2. Detectable difference and ranking stability (total score) ==")
    Yt = M["total"]
    ks = [3, 5, 8, 10]
    lo, med, hi = arm_boot_sd(Yt, rng)
    sdd = sdpair["total"]
    print(f"pooled SD of one per-round paired difference: {fmt(sdd)} (arm-cluster bootstrap 5/50/95 pct: {fmt(lo)} / {fmt(med)} / {fmt(hi)})")
    allk = list(range(3, 13)) + [15, 20, 25, 30, 40]
    f = mdd_factors(allk, rng, n=6000)
    print("MDD factor f_k (units of paired-difference SD): " + ", ".join(f"k={k}: {fmt(f[k], 2)}" for k in allk))
    assert 0.85 < f[10] < 1.15  # textbook: paired t, n = 10, 80 percent power, d about 0.99
    print("k | MDD total, t-test 80% power (pooled SD) | with SD at 5th pct | with SD at 95th pct | MDD with the pooled SD taken as known (2.80 x SD / sqrt(k)) | P(right sign), pooled SD known, for true diff 1 / 2 / 3 / 5 points")
    for k in ks:
        ps = [norm_cdf(dl * math.sqrt(k) / sdd) for dl in (1, 2, 3, 5)]
        print(f"{k} | {fmt(f[k] * sdd)} | {fmt(f[k] * lo)} | {fmt(f[k] * hi)} | {fmt(2.8016 * sdd / math.sqrt(k))} | " + " / ".join(fmt(p, 2) for p in ps))
    print("MDD by component, 80% power (points), pooled paired SD x f_k:")
    for n, _ in keys:
        print(n, " ".join(f"k={k}:{fmt(f[k] * sdpair[n])}" for k in ks))
    print("rounds needed for 80% power, total, by true difference (pooled SD / SD 5th pct / SD 95th pct):")
    for dl in (1, 2, 3, 4, 5):
        need = []
        for s in (sdd, lo, hi):
            kk = next((k for k in allk if f[k] * s <= dl), None)
            need.append(f">{allk[-1]}" if kk is None else str(kk))
        print(f"true difference {dl} points: " + " / ".join(need) + "  (k grid: 3..12, 15, 20, 25, 30, 40)")

    for c, label in ((1.0, "plain bootstrap over rounds"), (math.sqrt(1.5), "variance-corrected (deviations x sqrt(3/2))")):
        print(f"\nbootstrap, {label}: draw k rounds with replacement from the 3 recorded rounds, B = {B}")
        res = rank_stability(Yt, ks, rng, c)
        print("k | mean Kendall tau vs observed ranking | P(top-1 unchanged) | P(top-3 set unchanged) | SD of a pair difference of means | 95% noise band (half width) | MDD 80% power")
        for k in ks:
            r = res[k]
            print(f"{k} | {fmt(r['tau'], 3)} | {fmt(r['top1'], 3)} | {fmt(r['top3'], 3)} | {fmt(r['noise_sd'])} | {fmt(r['noise95'])} | {fmt(r['mdd'])}")
        print("P(sign of a pair difference preserved) by observed gap of the 3-round means (number of pairs in bin):")
        for b in [(0, 1), (1, 2), (2, 3), (3, 5), (5, 99)]:
            print(f"gap {b[0]}-{b[1] if b[1] < 99 else '+'}: " + " ".join(f"k={k}:{fmt(res[k]['sign'][b][0], 2)}(n={res[k]['sign'][b][1]})" for k in ks))

    print("\nmodel-based check (not a bootstrap): true arm means = observed means, or shrunk by the noise they contain; Gaussian noise with the residual SD")
    for mode in ("shrunk", "observed"):
        out, s_true, sh = model_rank_check(Yt, ks, rng, mode)
        print(f"{mode}: estimated SD of true arm means {fmt(s_true)} (observed SD of arm means {fmt(sd(twoway(Yt)['rm']))}), shrink factor {fmt(sh, 2)}")
        print("k | mean Kendall tau vs true ranking | P(true best arm ranked first): " + " | ".join(f"k={k}: {fmt(out[k][0], 2)}, {fmt(out[k][1], 2)}" for k in ks))

    print("\nrule of the Sonnet report (median lead >= 3 and ahead in >= 2 of 3 rounds), k = 3, resampling rounds")
    for c, label in ((1.0, "plain"), (math.sqrt(1.5), "variance-corrected")):
        fp, anyp, anyc = win_rule(Yt, rng, c)
        print(f"null (no true difference), {label}: P(rule fires for a given pair) {fmt(fp, 3)}; P(fires for at least one of 66 pairs) {fmt(anyp, 3)}; P(fires for at least one of the 11 pairs with arm A) {fmt(anyc, 3)}")
    for sig, label in ((3.06, "pooled within-arm SD 3.06"), (2.09, "SD 2.09 without the 4 failed trials")):
        fp, anyp, anyc = win_rule_gauss(sig, rng)
        print(f"Gaussian null, {label}: P(fires for a given pair) {fmt(fp, 3)}; at least one of 66 pairs {fmt(anyp, 3)}; at least one of the 11 pairs with arm A {fmt(anyc, 3)}")
    obs = rule_observed(Yt, arms)
    print(f"observed in the recorded data: rule fires for {len(obs)} of 66 pairs: {obs}")
    for dl in (2, 3, 4, 6):
        fp, _, _ = win_rule(Yt, rng, 1.0, delta=dl)
        print(f"true difference {dl} points (first arm better): P(rule fires for it) {fmt(fp, 3)}")

    # ---- 3. agreement ----
    print("\n== 3. Agreement of the two reviews, and review against process checks ==")
    ov = parse_overall(root / "2026-10-18-mistreevous.md")
    ov_o = parse_overall(root / "2026-10-19-mistreevous-opusplan.md")
    assert len(ov) == 36 and len(ov_o) == 6
    pairs = list(ov.values()) + list(ov_o.values())
    x1, x2 = [p[0] for p in pairs], [p[1] for p in pairs]
    dif = [abs(p - q) for p, q in pairs]
    print(f"overall rating (1-10), all {len(pairs)} trials: exact agreement {sum(d == 0 for d in dif)}/{len(dif)}, within 1 point {sum(d <= 1 for d in dif)}/{len(dif)}, mean abs difference {fmt(mean(dif))}, Pearson r {fmt(pearson(x1, x2))}, quadratic weighted kappa {fmt(qwk(x1, x2))}")
    print("distribution of ratings given:", {k: (x1 + x2).count(k) for k in sorted(set(x1 + x2))})
    # check parsed values against the files present
    allrev = {**{("s",) + k: v for k, v in rv_s.items()}, **{("o",) + k: v for k, v in rv_o.items()}}
    for (run, rnd, arm, i), v in allrev.items():
        want = (ov if run == "s" else ov_o)[(rnd, arm)][i]
        assert v["review"]["overall"] == want, (run, rnd, arm, i)
    both = [(run, rnd, arm) for (run, rnd, arm, i) in allrev if i == 0 and (run, rnd, arm, 1) in allrev]
    print(f"trials with both review files in this repository: {len(both)}")
    crit = list(next(iter(allrev.values()))["review"]["scores"])
    print("criterion | exact agreement | mean abs difference | mean score review 1 / review 2 | Pearson r (n pairs)")
    for cn in crit:
        a1 = [allrev[(*k, 0)]["review"]["scores"][cn] for k in both]
        a2 = [allrev[(*k, 1)]["review"]["scores"][cn] for k in both]
        print(f"{cn} | {sum(p == q for p, q in zip(a1, a2))}/{len(a1)} | {fmt(mean([abs(p - q) for p, q in zip(a1, a2)]))} | {fmt(mean(a1))} / {fmt(mean(a2))} | {fmt(pearson(a1, a2))}")
    s1 = [sum(allrev[(*k, 0)]["review"]["scores"].values()) for k in both]
    s2 = [sum(allrev[(*k, 1)]["review"]["scores"].values()) for k in both]
    print(f"sum of 8 criteria: mean abs difference {fmt(mean([abs(p - q) for p, q in zip(s1, s2)]))} of 40, Pearson r {fmt(pearson(s1, s2))}; review 1 mean {fmt(mean(s1))}, review 2 mean {fmt(mean(s2))}")

    def single(sc):  # one review mapped to the 25-point part
        return (sum(sc.values()) - 8) / 32 * 25

    chk = 0
    for run, rnd, arm in both:
        t = (tr_s if run == "s" else tr_o)[(rnd, arm)]
        p = (single(allrev[(run, rnd, arm, 0)]["review"]["scores"]) + single(allrev[(run, rnd, arm, 1)]["review"]["scores"])) / 2
        assert abs(p - t["parts"]["review"]) < 0.02, (run, rnd, arm, p, t["parts"]["review"])
        chk += 1
    print(f"review part formula (mean of both reviews, (sum - 8)/32 x 25) reproduces the recorded review part for {chk} of {chk} trials")
    dd = [single(allrev[(*k, 0)]["review"]["scores"]) - single(allrev[(*k, 1)]["review"]["scores"]) for k in both]
    noise_var = mean([d * d for d in dd]) / 4  # variance of a 2-review mean from the paired differences
    s_noise = math.sqrt(noise_var)
    tw_rev = twoway(M["review"])
    print(f"review part (25 points): SD of the judge noise in a 2-review mean {fmt(s_noise)}; residual SD (arm x round) of the recorded review part {fmt(math.sqrt(tw_rev['mse']))}; noise share of residual variance {fmt(noise_var / tw_rev['mse'] * 100, 0)} percent")
    print(f"mean signed difference review 1 minus review 2 (25-point scale): {fmt(mean(dd))}")

    # review vs process checks
    keysall = [("s", k) for k in sorted(tr_s)] + [("o", k) for k in sorted(tr_o)]
    T = [(tr_s if r == "s" else tr_o)[k] for r, k in keysall]
    rv = [t["parts"]["review"] for t in T]
    print("\nreview part against other recorded quantities, Pearson / Spearman, all 42 trials:")
    for n in ("process", "static"):
        y = [t["parts"][n] for t in T]
        print(f"{n}: {fmt(pearson(rv, y))} / {fmt(spearman(rv, y))}")
    mins = [t["minutes"] for t in T]
    print(f"minutes: {fmt(pearson(rv, mins))} / {fmt(spearman(rv, mins))}")
    cost = [t["cost_usd_api_equivalent"] for t in T]
    print(f"cost: {fmt(pearson(rv, cost))} / {fmt(spearman(rv, cost))}")
    lines = []
    for r, (rnd, arm) in keysall:
        tj = json.loads(((d_s if r == "s" else d_o) / f"round-{rnd}" / arm / "trial.json").read_text())["lines"]
        lines.append(tj["source"] + tj["test"])
    print(f"lines of code (source + test, whole repository): {fmt(pearson(rv, lines))} / {fmt(spearman(rv, lines))}")
    # arm-centred (within-arm) and arm-mean (between-arm) views, Sonnet run
    for n in ("process", "static"):
        w1, w2 = [], []
        for i in range(12):
            mr, mp = mean(M["review"][i]), mean(M[n][i])
            w1 += [v - mr for v in M["review"][i]]
            w2 += [v - mp for v in M[n][i]]
        bm = pearson([mean(r) for r in M["review"]], [mean(r) for r in M[n]])
        print(f"Sonnet run, review vs {n}: within-arm (arm means removed, 36 trials) r {fmt(pearson(w1, w2))}, rho {fmt(spearman(w1, w2))}; between arm means (12 arms) r {fmt(bm)}, rho {fmt(spearman([mean(r) for r in M['review']], [mean(r) for r in M[n]]))}")
    ln6 = {}
    for rnd, arm in tr_s:
        tj = json.loads((d_s / f"round-{rnd}" / arm / "trial.json").read_text())["lines"]
        ln6[(rnd, arm)] = tj["source"] + tj["test"]
    for nm, getter in (("minutes", lambda r, a: tr_s[(r, a)]["minutes"]), ("lines of code", lambda r, a: ln6[(r, a)])):
        w1, w2 = [], []
        for a in arms:
            xs = [tr_s[(r, a)]["parts"]["review"] for r in (1, 2, 3)]
            ys = [getter(r, a) for r in (1, 2, 3)]
            w1 += [v - mean(xs) for v in xs]
            w2 += [v - mean(ys) for v in ys]
        print(f"Sonnet run, review vs {nm}: within-arm r {fmt(pearson(w1, w2))}, rho {fmt(spearman(w1, w2))}")
    # review's own process criterion vs the process checks, files present
    pc, pr = [], []
    for run, rnd, arm in both:
        t = (tr_s if run == "s" else tr_o)[(rnd, arm)]
        pc.append((allrev[(run, rnd, arm, 0)]["review"]["scores"]["process"] + allrev[(run, rnd, arm, 1)]["review"]["scores"]["process"]) / 2)
        pr.append(t["parts"]["process"])
    print(f"review criterion 'process' (mean of 2, 1-5) vs process checks part, {len(pc)} trials with both files: r {fmt(pearson(pc, pr))}, rho {fmt(spearman(pc, pr))}")
    print("process checks per arm (mean of 3 rounds, part of 15) and review part:")
    for i, a in sorted(enumerate(arms), key=lambda p: -mean(M["review"][p[0]])):
        print(f"{a} review {fmt(mean(M['review'][i]))} process {fmt(mean(M['process'][i]))}")


if __name__ == "__main__":
    main()
