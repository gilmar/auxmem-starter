#!/usr/bin/env python3
"""Generate the Koinome logo (closed-loop grayscale Ben Day study).

Writes SVG (and PNG when ImageMagick is available) to docs/images/.
Uses only the Python standard library for SVG generation.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = REPO_ROOT / "docs" / "images"
SVG_PATH = OUTPUT_DIR / "koinome-logo.svg"
PNG_PATH = OUTPUT_DIR / "koinome-logo.png"

WIDTH = HEIGHT = 1400
CENTER_X = CENTER_Y = 700
MAJOR_RADIUS = 2.15
TUBE_RADIUS = 0.92
PROJECTION_SCALE = 205
CYCLES = 3
DOT_COUNT = 744

# Light-gray, mid-gray, and black printing plates. Small registration offsets and
# unequal coverage create a monochrome Ben Day / newsprint character.
PLATES = (
    ("#D2D2CE", -5.5, 2.0, 1.00),
    ("#858583", 4.0, -3.5, 0.86),
    ("#111111", 1.0, 4.0, 0.58),
)


def scale_function(u: float) -> float:
    """Periodic scale: contracts inward and returns exactly to its start."""
    return 0.28 + 0.72 * ((1.0 + math.cos(2.0 * math.pi * u)) / 2.0)


def build_nodes() -> list[tuple[float, float, float, float]]:
    raw: list[tuple[float, float, float, float, float]] = []

    for index in range(DOT_COUNT):
        # u=1 would duplicate u=0 on this closed orbit.
        u = index / DOT_COUNT
        t = CYCLES * 2.0 * math.pi * u + 0.045
        scale = scale_function(u)

        x = (MAJOR_RADIUS + TUBE_RADIUS * math.cos(5.0 * t)) * math.cos(2.0 * t)
        y = (MAJOR_RADIUS + TUBE_RADIUS * math.cos(5.0 * t)) * math.sin(2.0 * t)
        z = TUBE_RADIUS * math.sin(5.0 * t)

        dx = -5.0 * TUBE_RADIUS * math.sin(5.0 * t) * math.cos(2.0 * t) - 2.0 * (
            MAJOR_RADIUS + TUBE_RADIUS * math.cos(5.0 * t)
        ) * math.sin(2.0 * t)
        dy = -5.0 * TUBE_RADIUS * math.sin(5.0 * t) * math.sin(2.0 * t) + 2.0 * (
            MAJOR_RADIUS + TUBE_RADIUS * math.cos(5.0 * t)
        ) * math.cos(2.0 * t)

        raw.append(
            (
                CENTER_X + PROJECTION_SCALE * scale * x,
                CENTER_Y + PROJECTION_SCALE * scale * y,
                math.hypot(dx, dy),
                z,
                scale,
            )
        )

    speeds = [node[2] for node in raw]
    minimum_speed, maximum_speed = min(speeds), max(speeds)

    nodes: list[tuple[float, float, float, float]] = []
    for x, y, speed, z, scale in raw:
        velocity = ((speed - minimum_speed) / (maximum_speed - minimum_speed)) ** 0.82
        depth = (z + TUBE_RADIUS) / (2.0 * TUBE_RADIUS)
        radius = (4.0 + 12.0 * velocity) * (0.74 + 0.42 * depth) * (0.55 + 0.45 * scale)
        nodes.append((x, y, radius, z))

    # Back-to-front painter's order supports the spatial reading at crossings.
    return sorted(nodes, key=lambda node: node[3])


def make_svg(nodes: list[tuple[float, float, float, float]]) -> str:
    layers: list[str] = []
    for color, offset_x, offset_y, radius_scale in PLATES:
        circles = "".join(
            (
                f'<circle cx="{x + offset_x:.2f}" cy="{y + offset_y:.2f}" '
                f'r="{radius * radius_scale:.2f}"/>'
            )
            for x, y, radius, _ in nodes
        )
        layers.append(f'<g fill="{color}" style="mix-blend-mode:multiply">{circles}</g>')

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}">\n'
        f'<rect width="100%" height="100%" fill="#FFFFFF"/>\n'
        f'{"".join(layers)}\n'
        f"</svg>"
    )


def render_png(svg_path: Path, png_path: Path) -> bool:
    magick = shutil.which("magick")
    if not magick:
        return False
    subprocess.run(
        [magick, "-background", "white", str(svg_path), str(png_path)],
        check=True,
    )
    return True


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    svg_path = SVG_PATH
    svg_path.write_text(make_svg(build_nodes()), encoding="utf-8")
    print(f"wrote {svg_path.relative_to(REPO_ROOT)}")

    if render_png(svg_path, PNG_PATH):
        print(f"wrote {PNG_PATH.relative_to(REPO_ROOT)}")
    else:
        print("ImageMagick not found; SVG only (install magick to emit PNG).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
