#!/usr/bin/env python3
"""Generate the home-page tile artwork as original, seeded SVG files.

Run from the repository root:  python3 scripts/generate_art.py

Each piece is a data/ML-flavoured drawing (attention maps, loss landscapes,
forecast fans, ...) made only from code, so the output is reproducible and
free to use. Replace any file in assets/img/ with your own image to swap a tile.
"""
import math
import random
from pathlib import Path

W, H = 600, 800
PAPER, PAPER2, CREAM = "#f3eee3", "#e8dfcf", "#fbf7ee"
INK, NAVY = "#26211e", "#2f3e5c"
TERRA, BLUE, MUSTARD, SAGE, ROSE = "#e0714f", "#7ea6d6", "#f2c14e", "#a8bf9f", "#e9a79c"
OUT = Path(__file__).resolve().parent.parent / "assets" / "img"


def fmt(value):
    return f"{value:.1f}"


def points(pairs):
    return " ".join(f"{fmt(x)},{fmt(y)}" for x, y in pairs)


def svg(body, background):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'preserveAspectRatio="xMidYMid slice"><rect width="{W}" height="{H}" '
        f'fill="{background}"/>{body}</svg>\n'
    )


def mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def ramp(stops, t):
    t = min(max(t, 0.0), 1.0) * (len(stops) - 1)
    i = min(int(t), len(stops) - 2)
    return mix(stops[i], stops[i + 1], t - i)


def smooth_field(rng, terms=3, scale=1.0):
    """A smooth scalar field in [-1, 1] built from a few random sine waves."""
    waves = [
        (rng.uniform(0.004, 0.011) * scale, rng.uniform(0.004, 0.011) * scale * rng.choice((-1, 1)),
         rng.uniform(0, math.tau), rng.uniform(0.5, 1.0))
        for _ in range(terms)
    ]
    total = sum(w[3] for w in waves)
    return lambda x, y: sum(a * math.sin(fx * x + fy * y + ph) for fx, fy, ph, a in waves) / total


def smooth_path(pairs, move=True):
    """Catmull-Rom spline through the points, written as cubic Beziers."""
    start = pairs[0]
    d = [("M" if move else "L") + f"{fmt(start[0])},{fmt(start[1])}"]
    for i in range(len(pairs) - 1):
        p0, p1, p2, p3 = pairs[max(i - 1, 0)], pairs[i], pairs[i + 1], pairs[min(i + 2, len(pairs) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append(f"C{fmt(c1[0])},{fmt(c1[1])} {fmt(c2[0])},{fmt(c2[1])} {fmt(p2[0])},{fmt(p2[1])}")
    return "".join(d)


def attention(rng):
    cols, rows, size = 12, 16, 50
    spikes = {(rng.randrange(4, rows), rng.randrange(cols)) for _ in range(10)}
    cells = []
    for r in range(rows):
        for c in range(cols):
            key = c * rows / cols
            if key > r + 0.5:
                value = 0.03 * rng.random()
            else:
                value = (math.exp(-((r - key) ** 2) / 18) * 0.8 + (0.55 if c == 0 else 0)
                         + (0.7 if (r, c) in spikes else 0) + rng.random() * 0.08)
            cells.append((r, c, value))
    peak = max(v for _, _, v in cells)
    rects = "".join(
        f'<rect x="{c * size + 1}" y="{r * size + 1}" width="{size - 2}" height="{size - 2}" '
        f'fill="{ramp([PAPER, ROSE, TERRA, INK], v / peak)}"/>'
        for r, c, v in cells
    )
    return svg(rects, PAPER)


def contours(rng):
    wells = [(rng.uniform(150, 450), rng.uniform(220, 580)) for _ in range(3)]
    body = []
    for w, (cx, cy) in enumerate(wells):
        ph = [rng.uniform(0, math.tau) for _ in range(3)]
        for k in range(1, 9):
            ring = []
            for i in range(73):
                t = i * math.tau / 72
                r = 24 * k * (1 + 0.10 * math.sin(2 * t + ph[0]) + 0.06 * math.sin(3 * t + ph[1])
                              + 0.04 * math.sin(5 * t + ph[2]))
                ring.append((cx + r * math.cos(t), cy + r * math.sin(t)))
            body.append(f'<polyline points="{points(ring)}" fill="none" '
                        f'stroke="{TERRA if w == 0 else INK}" stroke-width="1.6" opacity="{0.9 - k * 0.07:.2f}"/>')
    x, y = 60.0, 90.0
    target = min(wells, key=lambda well: math.hypot(well[0] - x, well[1] - y))
    path = [(x, y)]
    for _ in range(36):
        x += (target[0] - x) * 0.09 + rng.uniform(-9, 9)
        y += (target[1] - y) * 0.09 + rng.uniform(-9, 9)
        path.append((x, y))
    body.append(f'<polyline points="{points(path)}" fill="none" stroke="{NAVY}" stroke-width="3"/>')
    body += [f'<circle cx="{fmt(px)}" cy="{fmt(py)}" r="5" fill="{MUSTARD}" stroke="{NAVY}" stroke-width="2"/>'
             for px, py in path[::4]]
    return svg("".join(body), PAPER)


def flowfield(rng):
    field = smooth_field(rng, 3, 1.4)
    body = []
    for _ in range(520):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        path = [(x, y)]
        for _ in range(10):
            angle = field(x, y) * math.pi * 1.2
            x, y = x + math.cos(angle) * 9, y + math.sin(angle) * 9
            path.append((x, y))
        body.append(f'<polyline points="{points(path)}" fill="none" stroke="{rng.choice((BLUE, BLUE, INK, ROSE))}" '
                    f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    return svg("".join(body), PAPER)


def clusters(rng):
    centers = [(160, 210), (440, 250), (190, 570), (430, 590)]
    colors = (MUSTARD, ROSE, SAGE, BLUE)
    body = []
    for (cx, cy), color in zip(centers, colors):
        for _ in range(110):
            body.append(f'<circle cx="{fmt(cx + rng.gauss(0, 48))}" cy="{fmt(cy + rng.gauss(0, 58))}" '
                        f'r="{fmt(rng.uniform(2.5, 6))}" fill="{color}" opacity="0.9"/>')
    return svg("".join(body), NAVY)


def network(rng):
    sizes = [4, 7, 8, 6, 3]
    layers = []
    for i, n in enumerate(sizes):
        gap = min(80, 520 / n)
        layers.append([(70 + i * 115, 400 + (j - (n - 1) / 2) * gap) for j in range(n)])
    body = []
    for left, right in zip(layers, layers[1:]):
        for ax, ay in left:
            for bx, by in right:
                body.append(f'<line x1="{fmt(ax)}" y1="{fmt(ay)}" x2="{fmt(bx)}" y2="{fmt(by)}" '
                            f'stroke="{INK}" stroke-width="1" opacity="{rng.uniform(0.05, 0.5):.2f}"/>')
    for layer in layers:
        for x, y in layer:
            body.append(f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="10" fill="{mix(PAPER, TERRA, rng.random())}" '
                        f'stroke="{INK}" stroke-width="1.6"/>')
    return svg("".join(body), PAPER)


def confusion(rng):
    n, size, x0, y0 = 6, 80, 60, 60
    body, recalls = [], []
    for r in range(n):
        row = [rng.random() * 0.25 for _ in range(n)]
        row[r] = 0.9 + rng.random() * 0.5
        total = sum(row)
        row = [v / total for v in row]
        recalls.append(row[r])
        for c, v in enumerate(row):
            body.append(f'<rect x="{x0 + c * size + 1}" y="{y0 + r * size + 1}" width="{size - 2}" '
                        f'height="{size - 2}" fill="{ramp([PAPER, BLUE, NAVY], v * 1.1)}"/>')
    for i, recall in enumerate(recalls):
        height = recall * 170
        body.append(f'<rect x="{x0 + i * size + 12}" y="{fmt(740 - height)}" width="{size - 24}" '
                    f'height="{fmt(height)}" fill="{TERRA}"/>')
    return svg("".join(body), CREAM)


def forecast(rng):
    n, split = 60, 32
    xs = [40 + i * 520 / (n - 1) for i in range(n)]
    trend = [430 - 1.8 * i + 38 * math.sin(i / 4.5) for i in range(n)]
    history = [(xs[i], trend[i] + rng.uniform(-9, 9)) for i in range(split)]
    start = history[-1]
    center = [start] + [(xs[i], trend[i]) for i in range(split, n)]
    body = [f'<line x1="40" y1="{100 * k}" x2="560" y2="{100 * k}" stroke="{INK}" opacity="0.08"/>'
            for k in range(1, 8)]
    for k, opacity in ((3, 0.16), (2, 0.22), (1, 0.32)):
        upper = [(x, y - k * (3 + 1.6 * i)) for i, (x, y) in enumerate(center)]
        lower = [(x, y + k * (3 + 1.6 * i)) for i, (x, y) in enumerate(center)]
        body.append(f'<polygon points="{points(upper + lower[::-1])}" fill="{TERRA}" opacity="{opacity}"/>')
    body.append(f'<line x1="{fmt(start[0])}" y1="60" x2="{fmt(start[0])}" y2="740" stroke="{INK}" '
                f'opacity="0.4" stroke-dasharray="6 6"/>')
    body.append(f'<polyline points="{points(center)}" fill="none" stroke="{TERRA}" stroke-width="3"/>')
    body.append(f'<polyline points="{points(history)}" fill="none" stroke="{INK}" stroke-width="2.5" '
                f'stroke-linejoin="round"/>')
    return svg("".join(body), PAPER)


def radial(rng):
    cx, cy, bars = 300, 400, 96
    field = smooth_field(rng, 3)
    body = [f'<circle cx="{cx}" cy="{cy}" r="72" fill="none" stroke="{PAPER}" stroke-width="1.5" opacity="0.5"/>']
    for i in range(bars):
        angle = i * math.tau / bars
        length = 30 + 150 * (0.5 + 0.5 * field(i * 9, i * 5)) * (0.6 + 0.4 * rng.random())
        color = (BLUE, ROSE, MUSTARD)[i * 3 // bars]
        x1, y1 = cx + 80 * math.cos(angle), cy + 80 * math.sin(angle)
        x2, y2 = cx + (80 + length) * math.cos(angle), cy + (80 + length) * math.sin(angle)
        body.append(f'<line x1="{fmt(x1)}" y1="{fmt(y1)}" x2="{fmt(x2)}" y2="{fmt(y2)}" stroke="{color}" '
                    f'stroke-width="5" stroke-linecap="round"/>')
    return svg("".join(body), INK)


def halftone(rng):
    field = smooth_field(rng, 4, 1.8)
    step = 25
    dots = [f'<circle cx="{x}" cy="{y}" r="{fmt(1 + 10 * (0.5 + 0.5 * field(x, y)))}" fill="{INK}"/>'
            for y in range(step // 2, H, step) for x in range(step // 2, W, step)]
    return svg("".join(dots), MUSTARD)


def ridgeline(rng):
    peaks = [(rng.uniform(150, 450), rng.uniform(40, 120)) for _ in range(3)]
    body = []
    for i in range(30):
        y0 = 110 + i * 20.5
        shifted = [(c + rng.uniform(-30, 30), s) for c, s in peaks]
        series = [(x, y0 - sum(60 * math.exp(-((x - c) ** 2) / (2 * s * s)) for c, s in shifted)
                   * (0.55 + 0.45 * rng.random())) for x in range(40, 561, 8)]
        d = f"M40,{fmt(y0)} L" + " L".join(f"{fmt(x)},{fmt(y)}" for x, y in series) + f" L560,{fmt(y0)} Z"
        body.append(f'<path d="{d}" fill="{PAPER}" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>')
    return svg("".join(body), PAPER)


def truchet(rng):
    size, r = 50, 25
    body = []
    for row in range(16):
        for col in range(12):
            if rng.random() < 0.5:
                arcs = (f"M{r},0 A{r},{r} 0 0 1 0,{r}", f"M{size - r},{size} A{r},{r} 0 0 1 {size},{size - r}")
            else:
                arcs = (f"M{size - r},0 A{r},{r} 0 0 0 {size},{r}", f"M0,{size - r} A{r},{r} 0 0 1 {r},{size}")
            body.append(f'<g transform="translate({col * size},{row * size})" fill="none" stroke-width="13">'
                        f'<path d="{arcs[0]}" stroke="{INK}"/><path d="{arcs[1]}" stroke="{TERRA}"/></g>')
    return svg("".join(body), PAPER2)


def blobs(rng):
    circles = [f'<circle cx="{fmt(rng.uniform(0, W))}" cy="{fmt(rng.uniform(0, H))}" r="{fmt(rng.uniform(40, 150))}" '
               f'fill="{rng.choice((BLUE, ROSE, MUSTARD))}" opacity="0.55"/>' for _ in range(36)]
    return svg(f'<g style="mix-blend-mode:multiply">{"".join(circles)}</g>', PAPER)


def stream(rng):
    layers, n = 5, 10
    xs = [-20 + i * 640 / (n - 1) for i in range(n)]
    values = [[30 + 70 * rng.random() for _ in range(n)] for _ in range(layers)]
    totals = [sum(v[i] for v in values) for i in range(n)]
    scale = 560 / max(totals)
    cumulative = [400 - totals[i] * scale / 2 for i in range(n)]
    body = []
    for color, layer in zip((NAVY, BLUE, SAGE, MUSTARD, ROSE), values):
        top = list(zip(xs, cumulative))
        cumulative = [cumulative[i] + layer[i] * scale for i in range(n)]
        bottom = list(zip(xs, cumulative))
        body.append(f'<path d="{smooth_path(top)}{smooth_path(bottom[::-1], move=False)}Z" fill="{color}"/>')
    return svg("".join(body), PAPER)


def multiples(rng):
    cell_w, cell_h, gap = 170, 165, 20
    body = []
    for row in range(4):
        for col in range(3):
            x, y = 25 + col * (cell_w + gap), 40 + row * (cell_h + gap)
            series = [(x + 12 + i * (cell_w - 24) / 9, y + cell_h * (0.2 + 0.6 * rng.random())) for i in range(10)]
            color = rng.choice((TERRA, BLUE, NAVY))
            body.append(f'<rect x="{x}" y="{y}" width="{cell_w}" height="{cell_h}" fill="{CREAM}" stroke="{INK}" '
                        f'stroke-opacity="0.25"/><path d="{smooth_path(series)}" fill="none" stroke="{color}" '
                        f'stroke-width="3"/><circle cx="{fmt(series[-1][0])}" cy="{fmt(series[-1][1])}" r="5" '
                        f'fill="{color}"/>')
    return svg("".join(body), PAPER2)


def losses(rng):
    body = []
    for i in range(18):
        amplitude, tau, floor = rng.uniform(1.8, 3.2), rng.uniform(14, 48), rng.uniform(0.05, 0.5)
        series = [(40 + t * 520 / 120,
                   700 - (amplitude * math.exp(-t / tau) + floor
                          + rng.gauss(0, 0.035 * (1 + 2 * math.exp(-t / 20)))) * 190) for t in range(121)]
        body.append(f'<polyline points="{points(series)}" fill="none" stroke="{(BLUE, ROSE, MUSTARD, SAGE)[i % 4]}" '
                    f'stroke-width="2" opacity="0.85" stroke-linejoin="round"/>')
    return svg("".join(body), INK)


def spiral(rng):
    colors = (TERRA, MUSTARD, BLUE)
    body = []
    for arm, color in enumerate(colors):
        for _ in range(230):
            t = rng.random()
            theta = arm * math.tau / 3 + 4.2 * t + rng.gauss(0, 0.18) * (0.3 + t)
            r = 20 + 250 * t
            body.append(f'<circle cx="{fmt(300 + r * math.cos(theta))}" cy="{fmt(400 + 1.25 * r * math.sin(theta))}" '
                        f'r="{fmt(rng.uniform(2, 4.2))}" fill="{color}" opacity="0.9"/>')
    return svg("".join(body), NAVY)


PIECES = [attention, contours, flowfield, clusters, network, confusion, forecast, radial,
          halftone, ridgeline, truchet, blobs, stream, multiples, losses, spiral]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for number, piece in enumerate(PIECES, start=1):
        target = OUT / f"tile-{number:02d}.svg"
        target.write_text(piece(random.Random(1000 + number)), encoding="utf8")
        print(f"wrote {target.relative_to(OUT.parent.parent)} ({piece.__name__})")


if __name__ == "__main__":
    main()
