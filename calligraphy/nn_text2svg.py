"""nn_text2svg — Norwegian handwriting via pretrained Graves RNN + programmatic æøå.

The pretrained model (X-rayLaser/pytorch-handwriting-synthesis-toolkit, trained on
IAM-OnDB) only knows ` ?,.A-Za-z`. This script substitutes æ->ae, ø->o, å->a before
synthesis, then uses the model's attention weights (phi) to locate the base letters
in the stroke sequence: ø gets a slash, å gets a ring, and æ's a+e are squeezed
into a ligature. Diacritic strokes carry a little hand-wobble so they don't stand
out as machine-perfect against the RNN's writing.

Output matches text2svg.py: mm units, polylines, stroke-width 0.3, no background.
Feeds straight into scripts/svg2gcode.py or the web app.

Run with any python — re-execs itself with the toolkit's venv (torch 1.x):
  python3 calligraphy/nn_text2svg.py "Blåbærsyltetøy på brød" --bias 0.8 --trials 5

See docs/research/nn-handwriting-aeoeaa.md for background.
"""
import argparse
import math
import os
import random
import re
import sys
from pathlib import Path

TOOLKIT = Path.home() / "git" / "pytorch-handwriting-synthesis-toolkit"
sys.path.insert(0, str(TOOLKIT))

try:
    import torch  # noqa: E402
except ModuleNotFoundError:  # wrong python — re-exec with the toolkit's venv
    VENV_PY = TOOLKIT / "venv" / "bin" / "python"
    if not VENV_PY.exists():
        sys.exit(f"trenger toolkit-venv: {VENV_PY} finnes ikke "
                 f"(klon X-rayLaser/pytorch-handwriting-synthesis-toolkit til ~/git)")
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])
from handwriting_synthesis.sampling import HandwritingSynthesizer  # noqa: E402
from handwriting_synthesis.utils import split_into_components, get_strokes  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "output"

_rng = random.Random()

# original char -> (substitute string, treatment, is_uppercase)
SUBSTITUTIONS = {
    "æ": ("ae", "ligature", False),
    "Æ": ("Ae", "ligature", True),
    "ø": ("o", "slash", False),
    "Ø": ("O", "slash", True),
    "å": ("a", "ring", False),
    "Å": ("A", "ring", True),
}


def substitute(text, charset):
    """Return (model_text, targets) where targets = [(index_in_model_text, kind, upper)]."""
    out = []
    targets = []
    for ch in text:
        if ch in SUBSTITUTIONS:
            sub, kind, upper = SUBSTITUTIONS[ch]
            targets.append((len(out), kind, upper))
            out.extend(sub)
        elif ch in charset:
            out.append(ch)
        else:
            print(f"warning: '{ch}' not in model charset, dropped", file=sys.stderr)
    return "".join(out), targets


def char_indices(phi, char_index):
    """Timesteps whose stroke points the model attributes to one character."""
    mask = phi.argmax(dim=1) == char_index
    if mask.sum() < 2:  # attention never peaked there; fall back to soft weights
        mask = phi[:, char_index] > phi[:, char_index].max() * 0.5
    return torch.arange(len(mask))[mask].tolist()


def squeeze_ligature(xs, ys, phi, a_index):
    """Pull the letter after `a_index` leftward so 'ae' fuses into an æ ligature.

    Cursive strokes connect the letters, so there is no whitespace gap to
    close — instead aim for a target distance between the letter *centres*
    (the e's left bowl should share the a's right side). Shifts every point
    from the second letter's first timestep onward, with a short ramp over
    the preceding points so the connecting stroke bends instead of jumping.
    """
    e_idx = char_indices(phi, a_index + 1)
    if not e_idx:
        return
    a_cx, _, a_r = char_center_radius(xs, ys, phi, a_index)
    e_cx, _, e_r = char_center_radius(xs, ys, phi, a_index + 1)
    delta = (e_cx - a_cx) - 0.6 * (a_r + e_r)
    if delta <= 0:
        return
    t0 = min(e_idx)
    ramp = 6
    for t in range(max(0, t0 - ramp), len(xs)):
        f = min(1.0, (t - t0 + ramp) / ramp)
        xs[t] -= delta * f


def ring_points(cx, cy, rc, upper=False, n=24):
    """Hand-drawn-ish ring: wobbly radius, random start, slight overshoot.

    rc is the letter-body radius from char_center_radius; the MAD estimate
    runs low on a capital's full height, so its gap ratio compensates.
    """
    r = (0.40 if upper else 0.55) * rc
    cx += _rng.uniform(-0.08, 0.08) * rc
    cy = cy - rc - (1.0 if upper else 0.6) * rc - r  # above the body (screen coords: smaller y = up)
    start = _rng.uniform(0, 2 * math.pi)
    sweep = 2 * math.pi * _rng.uniform(1.02, 1.12)
    w_phase = _rng.uniform(0, 2 * math.pi)
    pts = []
    for i in range(n + 1):
        a = start + sweep * i / n
        ri = r * (1 + 0.07 * math.sin(2 * a + w_phase) + _rng.uniform(-0.02, 0.02))
        pts.append((cx + ri * math.cos(a), cy + ri * math.sin(a)))
    return pts


def char_center_radius(xs, ys, phi, char_index):
    """Median centre + MAD radius — robust to attention smearing onto tall neighbours."""
    idx = char_indices(phi, char_index)
    px = sorted(xs[i] for i in idx)
    py = sorted(ys[i] for i in idx)
    cx, cy = px[len(px) // 2], py[len(py) // 2]
    dev = sorted([abs(xs[i] - cx) for i in idx] + [abs(ys[i] - cy) for i in idx])
    r = 1.4 * dev[len(dev) // 2]  # median |offset| of a circle ≈ 0.7 r
    return cx, cy, r


def slash_points(cx, cy, r):
    """Hand-drawn-ish slash through the o: slightly bowed, jittered endpoints."""
    dx, dy = 0.8 * r, 1.35 * r  # lower-left to upper-right, just past the bowl
    j = 0.12 * r
    p0 = (cx - dx + _rng.uniform(-j, j), cy + dy + _rng.uniform(-j, j))
    p1 = (cx + dx + _rng.uniform(-j, j), cy - dy + _rng.uniform(-j, j))
    bow = _rng.uniform(-0.06, 0.06) * math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    nx, ny = -(p1[1] - p0[1]), p1[0] - p0[0]
    nlen = math.hypot(nx, ny)
    pts = []
    for t in (0.0, 0.35, 0.7, 1.0):
        bx = bow * math.sin(math.pi * t)
        pts.append((p0[0] + (p1[0] - p0[0]) * t + nx / nlen * bx,
                    p0[1] + (p1[1] - p0[1]) * t + ny / nlen * bx))
    return pts


def synthesize(text, checkpoint, bias, seed=None):
    if seed is not None:
        torch.manual_seed(seed)
        _rng.seed(seed)
    device = torch.device("cpu")
    synth = HandwritingSynthesizer.load(str(checkpoint), device, bias)
    model_text, targets = substitute(text, synth.tokenizer.charset)
    c = synth._encode_text(model_text + " ")  # sentinel, as in visualize_attention
    for attempt in range(5):
        with torch.no_grad():
            seq, phi = synth.model.sample_means_with_attention(
                context=c, steps=synth.num_steps, stochastic=True
            )
        # every non-space char should win the attention argmax at some point;
        # a char that never does was likely skipped by the sampler
        peaks = set(phi.argmax(dim=1).tolist())
        skipped = [ch for i, ch in enumerate(model_text) if ch != " " and i not in peaks]
        if not skipped:
            break
        print(f"attention skipped {skipped}, resampling ({attempt + 1}/5)", file=sys.stderr)
    seq = synth._undo_normalization(seq.cpu())
    xs, ys, eos = split_into_components(seq)
    phi = phi.cpu()

    # ligature squeezes mutate xs, so run them (in temporal order) before
    # measuring diacritic bboxes or building stroke polylines
    for char_index, kind, _ in targets:
        if kind == "ligature":
            squeeze_ligature(xs, ys, phi, char_index)

    polylines = [list(s) for s in get_strokes(xs, ys, torch.as_tensor(eos))]
    for char_index, kind, upper in targets:
        if kind == "ring":
            polylines.append(ring_points(*char_center_radius(xs, ys, phi, char_index), upper))
        elif kind == "slash":
            polylines.append(slash_points(*char_center_radius(xs, ys, phi, char_index)))
    return polylines


def to_svg(polylines, height_mm, margin_mm=2.0):
    all_pts = [p for line in polylines for p in line]
    x0 = min(p[0] for p in all_pts)
    y0 = min(p[1] for p in all_pts)
    y1 = max(p[1] for p in all_pts)
    scale = height_mm / (y1 - y0)

    def fmt(v):
        return f"{v:.2f}".rstrip("0").rstrip(".")

    mm = [
        [((p[0] - x0) * scale + margin_mm, (p[1] - y0) * scale + margin_mm) for p in line]
        for line in polylines
    ]
    w = max(p[0] for line in mm for p in line) + margin_mm
    h = height_mm + 2 * margin_mm
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{fmt(w)}mm" height="{fmt(h)}mm" viewBox="0 0 {fmt(w)} {fmt(h)}">',
        '<g fill="none" stroke="black" stroke-width="0.3" '
        'stroke-linecap="round" stroke-linejoin="round">',
    ]
    for line in mm:
        pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in line)
        lines.append(f'<polyline points="{pts}"/>')
    lines.append("</g>")
    lines.append("</svg>")
    return "\n".join(lines)


def slugify(text):
    return re.sub(r"[^0-9a-zA-Z]+", "-", text).strip("-").lower()[:40] or "nn"


def main():
    p = argparse.ArgumentParser(prog="nn_text2svg", description=__doc__.split("\n")[0])
    p.add_argument("text", help="line of text (æøå supported)")
    p.add_argument("-o", "--output", help="output SVG path (default calligraphy/output/nn-<slug>.svg)")
    p.add_argument("-b", "--bias", type=float, default=0.8, help="sampling bias; higher = cleaner (default 0.8)")
    p.add_argument("--height", type=float, default=15.0, help="ink height in mm (default 15)")
    p.add_argument("--seed", type=int, default=None, help="torch seed for reproducible samples")
    p.add_argument("--trials", type=int, default=1, help="number of samples to generate (pick the best by eye)")
    p.add_argument("--checkpoint", default=str(TOOLKIT / "checkpoints" / "Epoch_56"))
    args = p.parse_args()

    base = Path(args.output) if args.output else OUTPUT_DIR / f"nn-{slugify(args.text)}.svg"
    base.parent.mkdir(parents=True, exist_ok=True)
    for k in range(args.trials):
        seed = args.seed + k if args.seed is not None else None
        polylines = synthesize(args.text, args.checkpoint, args.bias, seed)
        out = base if args.trials == 1 else base.with_stem(f"{base.stem}_{k + 1}")
        out.write_text(to_svg(polylines, args.height), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
