#!/usr/bin/env python3
"""
fig_timeline_m3.py -- M3 figure: where the byte-count saving goes.

Shows the three busiest inter-domain pairs before and after deduplication at
the headline configuration, to scale in link occupancy, so that three facts
are visible at once: the bottleneck MIGRATES from pair (2,0) to pair (1,0);
the DPU deduplication cost is small and overlapped; and the max-link byte
saving (26.3%) overstates the measured completion-time saving (17.5%).

Data provenance (all verified, do not edit without re-verifying):
  lambda / unique      : dump_lambda_gpd8.py, seed 0, gpd=8, 32 GPUs
  cycles               : ablation_gpd8_results.csv (C0 953146, C3c 786443)
  six-seed mean        : ablation_gpd8_multiseed_results.csv (+10.29%)
  COMP duration        : verify_fig5_timeline.py (dpu_duration_micros -> 47 us)

Palette is fig_style's locked series palette. NAIVE_AMBER is deliberately NOT
used here: amber denotes naive placement in Fig 6/9 and must not be reused.
"""
import os
import matplotlib.pyplot as plt
import fig_style
from fig_style import CARTS_BLUE, C4_GRAY, NEG_RED

TOKEN_BYTES = 2048
LINK_BPUS = 5000.0
COMP_US = 47.0
CYC_C0, CYC_C3 = 953146.0, 786443.0
MEAN_6SEED = 10.29

PAIRS = [("(2,0)", 632, 461), ("(1,0)", 628, 466), ("(3,0)", 618, 458)]
EXP_MAXLINK_PCT = 26.27
EXP_CYCLE_PCT = 17.49
FIGW, FIGH = 7.0, 2.55


def t_us(copies):
    return copies * TOKEN_BYTES / LINK_BPUS


def main():
    raw_max = max(p[1] for p in PAIRS)
    ded_max = max(p[2] for p in PAIRS)
    maxlink_pct = 100.0 * (raw_max - ded_max) / raw_max
    cyc_pct = 100.0 * (CYC_C0 - CYC_C3) / CYC_C0
    assert abs(maxlink_pct - EXP_MAXLINK_PCT) < 0.01, maxlink_pct
    assert abs(cyc_pct - EXP_CYCLE_PCT) < 0.01, cyc_pct
    assert PAIRS[0][1] == raw_max, "pair 0 must be the C0 bottleneck"
    assert PAIRS[1][2] == ded_max, "pair 1 must be the CARTS bottleneck"
    assert PAIRS[0][2] < ded_max, "bottleneck must migrate"

    fig_style.apply()
    fig, ax = plt.subplots(figsize=(FIGW, FIGH))
    ax.grid(False)
    ax.xaxis.grid(True, linewidth=0.4, alpha=0.35)
    ax.set_axisbelow(True)

    ys, labels = [], []
    h = 0.62
    for i, (name, raw, ded) in enumerate(PAIRS):
        y = 5.6 - i * 0.8
        ys.append(y)
        labels.append(name)
        ax.barh(y, t_us(raw), height=h, color=C4_GRAY, alpha=0.72,
                edgecolor="none", zorder=2)
    for i, (name, raw, ded) in enumerate(PAIRS):
        y = 2.4 - i * 0.8
        ys.append(y)
        labels.append(name)
        ax.barh(y, t_us(ded), height=h, color=CARTS_BLUE, alpha=0.9,
                edgecolor="none", zorder=2)

    ax.barh(3.35, COMP_US, height=0.36, color=CARTS_BLUE, alpha=0.9,
            hatch="////", edgecolor="white", linewidth=0.0, zorder=2)
    ax.text(COMP_US + 4, 3.35, "DPU dedup %.0f µs, overlaps transfer" % COMP_US,
            va="center", ha="left", fontsize=7.5, color="#444444")

    for y, (name, raw, ded), val in ((5.6, PAIRS[0], PAIRS[0][1]),
                                     (1.6, PAIRS[1], PAIRS[1][2])):
        ax.barh(y, t_us(val), height=h, color="none",
                edgecolor=NEG_RED, linewidth=1.2, zorder=3)
    ax.text(t_us(PAIRS[0][1]) / 2, 5.6, "bottleneck", va="center",
            ha="center", fontsize=7.5, color="white", zorder=4)
    ax.text(t_us(PAIRS[1][2]) / 2, 1.6, "new bottleneck", va="center",
            ha="center", fontsize=7.5, color="white", zorder=4)

    for i, (name, raw, ded) in enumerate(PAIRS):
        ax.text(t_us(raw) + 3, 5.6 - i * 0.8, "%d" % raw, va="center",
                fontsize=7.5, color="#444444")
        ax.text(t_us(ded) + 3, 2.4 - i * 0.8, "%d" % ded, va="center",
                fontsize=7.5, color="#444444")

    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.text(-0.128, 0.80, "baseline", transform=ax.transAxes, rotation=90,
            va="center", ha="center", fontsize=8.5)
    ax.text(-0.128, 0.26, "CARTS", transform=ax.transAxes, rotation=90,
            va="center", ha="center", fontsize=8.5)
    ax.set_xlabel("link occupancy of the pair (µs, at 5\u2009GB/s)")
    ax.set_xlim(0, 305)
    ax.set_ylim(-0.3, 6.3)

    x_raw, x_ded = t_us(raw_max), t_us(ded_max)
    x_cyc = x_raw * (1.0 - cyc_pct / 100.0)
    ax.annotate("", xy=(x_raw, 0.55), xytext=(x_ded, 0.55),
                arrowprops=dict(arrowstyle="<->", color="#444444", lw=0.8))
    ax.text(x_ded - 4, 0.55, "max link load  -%.1f%%" % maxlink_pct,
            va="center", ha="right", fontsize=7.5, color="#444444")
    ax.annotate("", xy=(x_raw, -0.05), xytext=(x_cyc, -0.05),
                arrowprops=dict(arrowstyle="<->", color=CARTS_BLUE, lw=0.9))
    ax.text(x_cyc - 4, -0.05,
            "measured makespan  -%.1f%%  (%.1f%% mean, 6 seeds)"
            % (cyc_pct, MEAN_6SEED),
            va="center", ha="right", fontsize=7.5, color=CARTS_BLUE)
    for x in (x_raw, x_ded, x_cyc):
        ax.axvline(x, ymin=0.02, ymax=0.55, color="#999999", lw=0.5,
                   ls=(0, (2, 2)), zorder=1)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "fig_timeline_m3.pdf")
    fig.savefig(out)
    fig.savefig(out.replace(".pdf", ".png"), dpi=200)
    plt.close(fig)
    print("max link  %d -> %d   (-%.2f%%)" % (raw_max, ded_max, maxlink_pct))
    print("cycles    %d -> %d   (-%.2f%%)" % (CYC_C0, CYC_C3, cyc_pct))
    print("times us  raw %.1f / %.1f / %.1f   dedup %.1f / %.1f / %.1f"
          % tuple([t_us(p[1]) for p in PAIRS] + [t_us(p[2]) for p in PAIRS]))
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
