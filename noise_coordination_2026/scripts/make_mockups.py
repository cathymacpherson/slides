"""Builds the slide 4 mock-ups (sensors vs pose estimation) from mockup_markers.json.

Marker positions are edited with tools/marker-editor.html.

Usage: python3 scripts/make_mockups.py [markers.json]
Writes ../assets/mocap-sensors-mockup.svg and ../assets/pose-markers-mockup.svg.
"""
import base64
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent.parent / "assets"
PAD = 40

POSE_EDGES = [
    ("ear", "eye1"), ("eye1", "nose"), ("eye2", "nose"), ("nose", "neck"),
    ("neck", "shoulder1"), ("neck", "shoulder2"), ("neck", "hip"),
    ("shoulder1", "elbow1"), ("elbow1", "wrist1"), ("shoulder2", "elbow2"), ("elbow2", "wrist2"),
    ("hip", "hip1"), ("hip", "hip2"),
    ("hip1", "knee1"), ("knee1", "ankle1"), ("ankle1", "toe1"),
    ("hip2", "knee2"), ("knee2", "ankle2"), ("ankle2", "toe2"),
]

VICON_DEFS = (
    '<radialGradient id="vm" cx="0.36" cy="0.32" r="0.72"><stop offset="0" stop-color="#ffffff"/>'
    '<stop offset="0.4" stop-color="#e3e6ea"/><stop offset="1" stop-color="#8d949c"/></radialGradient>'
)


def document(width, height, png, body, defs=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="{-PAD} {-PAD} {width + 2 * PAD} {height + 2 * PAD}">'
        f"<defs>{defs}</defs>"
        f'<image width="{width}" height="{height}" xlink:href="data:image/png;base64,{png}"/>{body}</svg>'
    )


def pose_overlay(person):
    joints = person["pose"]
    lines = "".join(
        f'<line x1="{joints[a][0]}" y1="{joints[a][1]}" x2="{joints[b][0]}" y2="{joints[b][1]}"/>'
        for a, b in POSE_EDGES
    )
    dots = "".join(f'<circle cx="{x}" cy="{y}" r="17"/>' for x, y in joints.values())
    return f'<g stroke="#232323" stroke-width="9" stroke-linecap="round">{lines}</g><g fill="#c00000">{dots}</g>'


def head_strap(strap):
    (lx, ly), (rx_, ry_), (tx, ty) = strap["left"], strap["right"], strap["top"]
    cx, cy = (lx + rx_) / 2, (ly + ry_) / 2
    rx = math.dist((lx, ly), (rx_, ry_)) / 2
    ry = strap["depth"]
    tilt = math.degrees(math.atan2(ry_ - ly, rx_ - lx))
    return (
        f'<g transform="rotate({tilt:.1f} {cx:.0f} {cy:.0f})">'
        f'<path d="M{cx - rx:.0f},{cy:.0f} A{rx:.0f},{ry} 0 0 0 {cx + rx:.0f},{cy:.0f}" fill="none" '
        f'stroke="#26292d" stroke-width="30" stroke-linecap="round"/>'
        f'<rect x="{cx - 38:.0f}" y="{cy + ry - 30:.0f}" width="76" height="44" rx="10" fill="#33373c" stroke="#15171a" stroke-width="4"/>'
        f'<circle cx="{cx + 22:.0f}" cy="{cy + ry - 16:.0f}" r="6" fill="#ff3b30"/></g>'
        f'<path d="M{cx:.0f},{cy - 4:.0f} L{tx},{ty}" stroke="#26292d" stroke-width="20" stroke-linecap="round"/>'
    )


def watch(w):
    x, y, t = w["x"], w["y"], w["angle"]
    return (
        f'<g transform="rotate({t} {x} {y})">'
        # strap: wraps across the wrist either side of the face, with a buckle and holes
        f'<rect x="{x - 62}" y="{y - 21}" width="124" height="42" rx="16" fill="#3b4148" stroke="#1d2024" stroke-width="3"/>'
        f'<rect x="{x - 56}" y="{y - 25}" width="14" height="50" rx="4" fill="none" stroke="#b9c0c7" stroke-width="5"/>'
        + "".join(f'<circle cx="{x + d}" cy="{y}" r="4" fill="#1d2024"/>' for d in (38, 48))
        + f'<rect x="{x - 30}" y="{y - 27}" width="60" height="54" rx="14" fill="#1a1c1f" stroke="#55606b" stroke-width="4"/>'
        f'<rect x="{x - 20}" y="{y - 17}" width="40" height="34" rx="8" fill="#2f6f8f"/>'
        f'<path d="M{x - 11},{y + 3} l7,-9 l7,6 l8,-10" fill="none" stroke="#9fe3ff" stroke-width="4" '
        f'stroke-linecap="round" stroke-linejoin="round"/></g>'
    )


def vicon(x, y, r):
    return (
        f'<ellipse cx="{x}" cy="{y + r * 0.55:.0f}" rx="{r * 0.95:.0f}" ry="{r * 0.42:.0f}" fill="#1d1f22"/>'
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#vm)" stroke="#5f666e" stroke-width="2.5"/>'
    )


def sensors_overlay(person):
    return head_strap(person["headStrap"]) + watch(person["watch"]) + "".join(vicon(*m) for m in person["vicon"])


def main():
    markers = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "mockup_markers.json").read_text())
    width, height = markers["image"]["width"], markers["image"]["height"]
    png = base64.b64encode((ASSETS / "people-conversation.png").read_bytes()).decode()
    people = markers["people"].values()

    pose = document(width, height, png, "".join(pose_overlay(p) for p in people))
    sensors = document(width, height, png, "".join(sensors_overlay(p) for p in people), VICON_DEFS)
    (ASSETS / "pose-markers-mockup.svg").write_text(pose)
    (ASSETS / "mocap-sensors-mockup.svg").write_text(sensors)
    print("Wrote pose-markers-mockup.svg and mocap-sensors-mockup.svg")


if __name__ == "__main__":
    main()
