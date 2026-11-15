#!/usr/bin/env python3
"""Generate the HackRF Ultra rev 0.1 architecture schematic and PCB carrier.

Symbols are functional contracts. Ball maps and land patterns come from the
cited datasheets at layout time; this generator does not invent them.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

NS = uuid.UUID("6f3c1a90-4e2b-5d77-8c11-0a9b7e4d12c6")
ROOT = Path(__file__).resolve().parents[1] / "hardware"
PRO_TEMPLATE = Path(__file__).resolve().parents[2] / "praline.kicad_pro"
PROJECT = "hackrf-ultra"
ROOT_UUID = str(uuid.uuid5(NS, "root-file"))
_COUNTERS: dict[str, int] = {}


def next_id(prefix: str) -> str:
    _COUNTERS[prefix] = _COUNTERS.get(prefix, 0) + 1
    return f"{prefix}{_COUNTERS[prefix]}"

BOM: list[dict] = []


def uid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def esc(text: str) -> str:
    return str(text).replace("\\", "\\\\").replace('"', '\\"')


class Sch:
    def __init__(self, stem: str, file_uuid: str, paper: str = "A0"):
        self.stem = stem
        self.uuid = file_uuid
        self.paper = paper
        self.libs: dict[str, str] = {}
        self.items: list[str] = []
        self.hier: set[str] = set()
        self.sheet_uuid = file_uuid
        self._n = 0

    def seq(self, prefix: str) -> str:
        self._n += 1
        return next_id(prefix)

    def add_lib(self, lib_id: str, body: str) -> None:
        self.libs.setdefault(lib_id, body)

    def instance_path(self) -> str:
        if self.stem == "hackrf-ultra":
            return f"/{ROOT_UUID}"
        return f"/{ROOT_UUID}/{self.sheet_uuid}"

    def emit(self) -> str:
        libs = "\n".join(self.libs.values())
        body = "\n".join(self.items)
        return (
            "(kicad_sch\n"
            "\t(version 20250114)\n"
            '\t(generator "eeschema")\n'
            '\t(generator_version "9.0")\n'
            f'\t(uuid "{self.uuid}")\n'
            f'\t(paper "{self.paper}")\n'
            "\t(title_block\n"
            '\t\t(title "${TITLE}")\n'
            '\t\t(date "${DATE}")\n'
            '\t\t(rev "${VERSION}")\n'
            '\t\t(company "${COPYRIGHT}")\n'
            '\t\t(comment 1 "${LICENSE}")\n'
            '\t\t(comment 2 "Architecture rev 0.1. Not a fabrication package.")\n'
            "\t)\n"
            "\t(lib_symbols\n"
            f"{libs}\n"
            "\t)\n"
            f"{body}\n"
            "\t(sheet_instances\n"
            '\t\t(path "/"\n'
            '\t\t\t(page "1")\n'
            "\t\t)\n"
            "\t)\n"
            "\t(embedded_fonts no)\n"
            ")\n"
        )


def prop(name: str, value: str, x: float, y: float, hide: bool = False, size: float = 1.27) -> str:
    hide_s = "\n\t\t\t\t(hide yes)" if hide else ""
    return (
        f'\t\t(property "{esc(name)}" "{esc(value)}"\n'
        f"\t\t\t(at {x} {y} 0)\n"
        "\t\t\t(effects\n"
        "\t\t\t\t(font\n"
        f"\t\t\t\t\t(size {size} {size})\n"
        "\t\t\t\t)"
        f"{hide_s}\n"
        "\t\t\t)\n"
        "\t\t)"
    )


def ensure_power(sch: Sch, rail: str) -> None:
    lib = f"power:{rail}"
    if lib in sch.libs:
        return
    if rail == "GND":
        graphic = (
            '\t\t\t(symbol "GND_0_1"\n'
            "\t\t\t\t(polyline\n"
            "\t\t\t\t\t(pts\n"
            "\t\t\t\t\t\t(xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)\n"
            "\t\t\t\t\t)\n"
            "\t\t\t\t\t(stroke (width 0) (type default))\n"
            "\t\t\t\t\t(fill (type none))\n"
            "\t\t\t\t)\n"
            "\t\t\t)"
        )
        pin_ang = 270
        val_at = "0 -3.81"
    elif rail == "PWR_FLAG":
        graphic = (
            '\t\t\t(symbol "PWR_FLAG_0_1"\n'
            "\t\t\t\t(polyline\n"
            "\t\t\t\t\t(pts\n"
            "\t\t\t\t\t\t(xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)\n"
            "\t\t\t\t\t)\n"
            "\t\t\t\t\t(stroke (width 0) (type default))\n"
            "\t\t\t\t\t(fill (type none))\n"
            "\t\t\t\t)\n"
            "\t\t\t)"
        )
        pin_ang = 90
        val_at = "0 3.81"
    else:
        graphic = (
            f'\t\t\t(symbol "{esc(rail)}_0_1"\n'
            "\t\t\t\t(polyline\n"
            "\t\t\t\t\t(pts (xy -1.27 1.27) (xy 1.27 1.27))\n"
            "\t\t\t\t\t(stroke (width 0) (type default))\n"
            "\t\t\t\t\t(fill (type none))\n"
            "\t\t\t\t)\n"
            "\t\t\t\t(polyline\n"
            "\t\t\t\t\t(pts (xy 0 0) (xy 0 1.27))\n"
            "\t\t\t\t\t(stroke (width 0) (type default))\n"
            "\t\t\t\t\t(fill (type none))\n"
            "\t\t\t\t)\n"
            "\t\t\t)"
        )
        pin_ang = 90
        val_at = "0 3.556"
    pin_type = "power_out" if rail == "PWR_FLAG" else "power_in"
    ref = "#FLG" if rail == "PWR_FLAG" else "#PWR"
    sch.add_lib(
        lib,
        "\t\t(symbol \"" + lib + "\"\n"
        "\t\t\t(power)\n"
        "\t\t\t(pin_numbers (hide yes))\n"
        "\t\t\t(pin_names (offset 0) (hide yes))\n"
        "\t\t\t(exclude_from_sim no)\n"
        "\t\t\t(in_bom no)\n"
        "\t\t\t(on_board yes)\n"
        + prop("Reference", ref, 0, -3.81, True)
        + "\n"
        + prop("Value", rail, float(val_at.split()[0]), float(val_at.split()[1]), False)
        + "\n"
        + prop("Footprint", "", 0, 0, True)
        + "\n"
        + prop("Datasheet", "~", 0, 0, True)
        + "\n"
        + prop("Description", f"Power symbol {rail}", 0, 0, True)
        + "\n"
        + graphic
        + "\n"
        + f'\t\t\t(symbol "{esc(rail)}_1_1"\n'
        + f"\t\t\t\t(pin {pin_type} line\n"
        + f"\t\t\t\t\t(at 0 0 {pin_ang})\n"
        + "\t\t\t\t\t(length 0)\n"
        + '\t\t\t\t\t(name "~" (effects (font (size 1.27 1.27))))\n'
        + '\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))\n'
        + "\t\t\t\t)\n"
        + "\t\t\t)\n"
        + "\t\t)",
    )


def ensure_ic(sch: Sch, lib_id: str, value: str, left, right, top, bottom) -> None:
    if lib_id in sch.libs:
        return
    pins = []
    n = max(len(left), len(right), 1)
    h = n * 2.54 + 5.08
    w = 35.56
    body_h = h / 2
    body_w = w / 2

    def add_side(items, x, angle, y0, step):
        for i, (pname, ptype) in enumerate(items):
            y = y0 - i * step
            pins.append(
                f'\t\t\t\t(pin {ptype} line\n'
                f'\t\t\t\t\t(at {x} {y:.2f} {angle})\n'
                f'\t\t\t\t\t(length 2.54)\n'
                f'\t\t\t\t\t(name "{esc(pname)}" (effects (font (size 1.016 1.016))))\n'
                f'\t\t\t\t\t(number "{i+1 if angle==180 else 100+i}" (effects (font (size 0.8 0.8))))\n'
                f'\t\t\t\t)'
            )

    # Pin numbers are functional, not datasheet ball numbers. See symbol description.
    left_y0 = (len(left) - 1) * 2.54 / 2
    right_y0 = (len(right) - 1) * 2.54 / 2
    add_side(left, -body_w - 2.54, 0, left_y0, 2.54)
    # angle 0 means the pin points right; connection is at the left end of a left-side pin.
    # KiCad: pin `at` is the connection point, angle is the direction INTO the symbol? 
    # Standard: angle 180 on the left side, connection point outside, pin points right (into body) when angle is 0?
    # In KiCad, rotation 0 draws the pin pointing to the right, and `at` is the outer connection point.
    # A left-side pin has at=(-body_w, y) and angle 0? No: if the pin points right (angle 0) and at is the TIP,
    # the tip is the connection point on the outside, so left pin tip is at x=-body_w and angle is 0 (points right, body to the right).
    # I set angle 0 for left above incorrectly with x = -body_w-2.54. Let me fix by rebuilding properly below.
    pins.clear()

    def side_pins(items, tip_x, angle, index_base):
        y0 = (len(items) - 1) * 2.54 / 2
        for i, (pname, ptype) in enumerate(items):
            y = y0 - i * 2.54
            pins.append((pname, tip_x, y, angle, ptype, index_base + i))

    # Left pins: tip at -body_w, angle 0 (pin body extends left? Wait)
    # KiCad pin angle is the direction the pin POINTS, from the component toward the wire.
    # Angle 180: pin points left. Tip (connection) is further left. So tip_x = -body_w, angle 180,
    # and the pin is drawn from tip toward the right into the body... 
    # Actual KiCad behavior: the pin starts at `at` (the connection point) and is drawn BACKWARD
    # opposite to its angle, for `length`. Angle 0 points the connection to the right of the body.
    # Convention used by almost every symbol:
    #   left pins: (at -width  y 180) length extends to the right into the body? 
    # Looking at standard: left pin `(at -10.16 0 180)` means connection on the left, pin graphic goes right.
    # YES angle 180, at = left connection point.
    side_pins(left, -body_w, 180, 1)
    side_pins(right, body_w, 0, 101)
    # top: connection above the body, angle 90
    for i, (pname, ptype) in enumerate(top):
        x = -((len(top) - 1) * 2.54) / 2 + i * 2.54
        pins.append((pname, x, body_h, 90, ptype, 201 + i))
    for i, (pname, ptype) in enumerate(bottom):
        x = -((len(bottom) - 1) * 2.54) / 2 + i * 2.54
        pins.append((pname, x, -body_h, 270, ptype, 301 + i))

    pin_txt = []
    for pname, x, y, angle, ptype, num in pins:
        pin_txt.append(
            f'\t\t\t\t(pin {ptype} line\n'
            f'\t\t\t\t\t(at {x:.2f} {y:.2f} {angle})\n'
            f'\t\t\t\t\t(length 2.54)\n'
            f'\t\t\t\t\t(name "{esc(pname)}" (effects (font (size 1.016 1.016))))\n'
            f'\t\t\t\t\t(number "{num}" (effects (font (size 0.8 0.8))))\n'
            f'\t\t\t\t)'
        )
    unit = "\n".join(pin_txt)
    local = lib_id.split(":", 1)[-1]
    sch.add_lib(
        lib_id,
        f'\t\t(symbol "{lib_id}"\n'
        f'\t\t\t(exclude_from_sim no)\n'
        f'\t\t\t(in_bom yes)\n'
        f'\t\t\t(on_board yes)\n'
        + prop("Reference", "U", 0, body_h + 1.5)
        + "\n"
        + prop("Value", value, 0, -body_h - 1.5)
        + "\n"
        + prop("Footprint", "", 0, 0, True)
        + "\n"
        + prop("Datasheet", "~", 0, 0, True)
        + "\n"
        + prop("Description", "Functional symbol. Pin numbers are not datasheet balls.", 0, 0, True)
        + "\n"
        + f'\t\t\t(symbol "{esc(local)}_0_1"\n'
        + f'\t\t\t\t(rectangle (start {-body_w:.2f} {-body_h:.2f}) (end {body_w:.2f} {body_h:.2f})\n'
        + '\t\t\t\t\t(stroke (width 0.254) (type default))\n'
        + '\t\t\t\t\t(fill (type background))\n'
        + '\t\t\t\t)\n'
        + '\t\t\t)\n'
        + f'\t\t\t(symbol "{esc(local)}_1_1"\n'
        + unit
        + '\n\t\t\t)\n'
        + '\t\t)',
    )
    return {
        "w": body_w,
        "h": body_h,
        "pins": {p[0]: (p[1], p[2], p[3]) for p in pins},
    }


def ensure_two_pin(sch: Sch, lib_id: str, value: str, ref: str) -> dict:
    if lib_id not in sch.libs:
        local = lib_id.split(":", 1)[-1]
        sch.add_lib(
            lib_id,
            f'\t\t(symbol "{lib_id}"\n'
            '\t\t\t(pin_numbers (hide yes))\n'
            '\t\t\t(exclude_from_sim no)\n'
            '\t\t\t(in_bom yes)\n'
            '\t\t\t(on_board yes)\n'
            + prop("Reference", ref, 0, 2.54)
            + "\n"
            + prop("Value", value, 0, -2.54)
            + "\n"
            + prop("Footprint", "", 0, 0, True)
            + "\n"
            + prop("Datasheet", "~", 0, 0, True)
            + "\n"
            + prop("Description", value, 0, 0, True)
            + "\n"
            + f'\t\t\t(symbol "{esc(local)}_0_1"\n'
            + '\t\t\t\t(polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
            + '\t\t\t\t(polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.254) (type default)) (fill (type none)))\n'
            + '\t\t\t\t(polyline (pts (xy -1.016 0) (xy 1.016 0)) (stroke (width 0) (type default)) (fill (type none)))\n'
            + '\t\t\t)\n'
            + f'\t\t\t(symbol "{esc(local)}_1_1"\n'
            + '\t\t\t\t(pin passive line (at -5.08 0 180) (length 2.54)\n'
            + '\t\t\t\t\t(name "1" (effects (font (size 1.016 1.016))))\n'
            + '\t\t\t\t\t(number "1" (effects (font (size 1.016 1.016)))))\n'
            + '\t\t\t\t(pin passive line (at 5.08 0 0) (length 2.54)\n'
            + '\t\t\t\t\t(name "2" (effects (font (size 1.016 1.016))))\n'
            + '\t\t\t\t\t(number "2" (effects (font (size 1.016 1.016)))))\n'
            + '\t\t\t)\n'
            + '\t\t)',
        )
    return {"1": (-5.08, 0, 180), "2": (5.08, 0, 0)}


GEOM: dict[str, dict] = {}


def place_symbol(sch: Sch, lib_id: str, ref: str, value: str, x: float, y: float, rot: int = 0,
                 mfr: str = "", mpn: str = "", datasheet: str = "", desc: str = "",
                 footprint: str = "", bom: bool = True) -> str:
    su = uid(f"{sch.stem}:{ref}:{lib_id}")
    path = sch.instance_path()
    extra = []
    for name, val, hide in (
        ("Footprint", footprint, True),
        ("Datasheet", datasheet or "~", True),
        ("Description", desc, True),
        ("Manufacturer", mfr, True),
        ("Part Number", mpn, True),
    ):
        if val:
            extra.append(prop(name, val, x, y, hide))
    pin_stubs = ""
    # pin uuids filled by caller? KiCad accepts symbols without per-pin uuid in older files,
    # but v9 instances in this repo include them. Add a single dummy only if we know pin numbers.
    # We add pin entries for two-pin and IC after placement via geom.
    sch.items.append(
        "\t(symbol\n"
        f'\t\t(lib_id "{lib_id}")\n'
        f'\t\t(at {x:.2f} {y:.2f} {rot})\n'
        "\t\t(unit 1)\n"
        "\t\t(exclude_from_sim no)\n"
        f'\t\t(in_bom {"yes" if bom else "no"})\n'
        "\t\t(on_board yes)\n"
        "\t\t(dnp no)\n"
        f'\t\t(uuid "{su}")\n'
        + prop("Reference", ref, x, y - 2, False, 1.27)
        + "\n"
        + prop("Value", value, x, y + 2, False, 1.27)
        + "\n"
        + "\n".join(extra)
        + "\n"
        + "\t\t(instances\n"
        + f'\t\t\t(project "{PROJECT}"\n'
        + f'\t\t\t\t(path "{path}"\n'
        + f'\t\t\t\t\t(reference "{esc(ref)}")\n'
        + "\t\t\t\t\t(unit 1)\n"
        + "\t\t\t\t)\n"
        + "\t\t\t)\n"
        + "\t\t)\n"
        + "\t)"
    )
    if bom and not ref.startswith("#"):
        BOM.append({
            "Reference": ref,
            "Value": value,
            "Manufacturer": mfr,
            "Part": mpn,
            "Description": desc,
            "Datasheet": datasheet,
            "Sheet": sch.stem,
        })
    return su


def wire(sch: Sch, x1, y1, x2, y2) -> None:
    sch.items.append(
        "\t(wire\n"
        f"\t\t(pts (xy {x1:.2f} {y1:.2f}) (xy {x2:.2f} {y2:.2f}))\n"
        "\t\t(stroke (width 0) (type default))\n"
        f'\t\t(uuid "{uid(sch.seq("w"))}")\n'
        "\t)"
    )


def label(sch: Sch, kind: str, name: str, x: float, y: float, angle: int = 0) -> None:
    tag = {"local": "label", "global": "global_label", "hier": "hierarchical_label"}[kind]
    shape = ""
    if kind == "hier":
        shape = "\n\t\t(shape bidirectional)"
        sch.hier.add(name)
        justify = "left" if angle == 180 else "right" if angle == 0 else "left"
    elif kind == "global":
        shape = "\n\t\t(shape bidirectional)"
        justify = "left"
    else:
        justify = "left" if angle in (0, 90) else "right"
    sch.items.append(
        f'\t({tag} "{esc(name)}"{shape}\n'
        f"\t\t(at {x:.2f} {y:.2f} {angle})\n"
        "\t\t(effects\n"
        "\t\t\t(font (size 1.27 1.27))\n"
        f"\t\t\t(justify {justify})\n"
        "\t\t)\n"
        f'\t\t(uuid "{uid(sch.seq("l"))}")\n'
        "\t)"
    )


def note(sch: Sch, text: str, x: float, y: float, size: float = 1.27) -> None:
    sch.items.append(
        f'\t(text "{esc(text)}"\n'
        f"\t\t(at {x:.2f} {y:.2f} 0)\n"
        "\t\t(effects (font (size {s} {s})))\n".format(s=size)
        + f'\t\t(uuid "{uid(sch.seq("t"))}")\n'
        "\t)"
    )


def place_ic(sch: Sch, ref: str, value: str, x: float, y: float, left, right,
             top=(), bottom=(), **meta) -> dict[str, tuple[float, float]]:
    lib = f"ultra:{value}-{ref}"
    # one symbol per reference so pin lists can differ, but share geometry builder
    geom = ensure_ic(sch, lib, value, left, right, top, bottom)
    # ensure_ic returns None because I botched the return. Recompute geometry the same way.
    n = max(len(left), len(right), 1)
    body_h = (n * 2.54 + 5.08) / 2
    body_w = 35.56 / 2
    pins = {}

    def abs_pin(tip_x, tip_y):
        return x + tip_x, y + tip_y

    y0 = (len(left) - 1) * 2.54 / 2
    for i, (pname, _t) in enumerate(left):
        pins[pname] = abs_pin(-body_w, y0 - i * 2.54)
    y0 = (len(right) - 1) * 2.54 / 2
    for i, (pname, _t) in enumerate(right):
        pins[pname] = abs_pin(body_w, y0 - i * 2.54)
    for i, (pname, _t) in enumerate(top):
        px = -((len(top) - 1) * 2.54) / 2 + i * 2.54
        pins[pname] = abs_pin(px, body_h)
    for i, (pname, _t) in enumerate(bottom):
        px = -((len(bottom) - 1) * 2.54) / 2 + i * 2.54
        pins[pname] = abs_pin(px, -body_h)
    place_symbol(
        sch, lib, ref, value, x, y,
        mfr=meta.get("mfr", ""),
        mpn=meta.get("mpn", ""),
        datasheet=meta.get("datasheet", ""),
        desc=meta.get("desc", ""),
        footprint=meta.get("footprint", "land pattern from datasheet, not yet drawn"),
    )
    return pins


def stub_label(sch: Sch, pin_xy, name: str, direction: str, kind: str = "local") -> None:
    x, y = pin_xy
    if direction == "left":
        x2, y2, ang = x - 12.7, y, 180
    elif direction == "right":
        x2, y2, ang = x + 12.7, y, 0
    elif direction == "up":
        x2, y2, ang = x, y + 7.62, 90
    else:
        x2, y2, ang = x, y - 7.62, 270
    wire(sch, x, y, x2, y2)
    label(sch, kind, name, x2, y2, ang)


def stub_power(sch: Sch, pin_xy, rail: str, direction: str) -> None:
    x, y = pin_xy
    if direction == "up":
        x2, y2 = x, y + 5.08
    elif direction == "down":
        x2, y2 = x, y - 5.08
    elif direction == "left":
        x2, y2 = x - 5.08, y
    else:
        x2, y2 = x + 5.08, y
    wire(sch, x, y, x2, y2)
    ensure_power(sch, rail)
    place_symbol(sch, f"power:{rail}", sch.seq("#PWR"), rail, x2, y2, bom=False)


def stub_gnd(sch: Sch, pin_xy) -> None:
    stub_power(sch, pin_xy, "GND", "down")


def place_flag(sch: Sch, x, y, rail: str) -> None:
    ensure_power(sch, rail)
    ensure_power(sch, "PWR_FLAG")
    place_symbol(sch, f"power:{rail}", sch.seq("#PWR"), rail, x, y, bom=False)
    wire(sch, x, y, x + 7.62, y)
    place_symbol(sch, "power:PWR_FLAG", sch.seq("#FLG"), "PWR_FLAG", x + 7.62, y, bom=False)


def two_pin(sch: Sch, ref_prefix: str, value: str, x, y, net_a, net_b, kind_a="local", kind_b="local", **meta):
    lib = f"ultra:2pin-{value}"
    ensure_two_pin(sch, lib, value, ref_prefix[:1] if ref_prefix[:1] in "RCLFJ" else "R")
    ref = sch.seq(ref_prefix[:1] if ref_prefix[:1].isalpha() else "R")
    # force reference prefix
    ref = ref_prefix if ref_prefix[-1].isdigit() else sch.seq(ref_prefix)
    place_symbol(sch, lib, ref, value, x, y, **{k: meta.get(k, "") for k in ("mfr", "mpn", "datasheet", "desc", "footprint")})
    stub_label(sch, (x - 5.08, y), net_a, "left", kind_a)
    stub_label(sch, (x + 5.08, y), net_b, "right", kind_b)
    return ref


# ---------------------------------------------------------------------------
# Sheets
# ---------------------------------------------------------------------------

ANALOG = [
    "ADC0_P", "ADC0_N", "ADC1_P", "ADC1_N",
    "ADC2_P", "ADC2_N", "ADC3_P", "ADC3_N",
    "DAC0_P", "DAC0_N", "DAC1_P", "DAC1_N",
]
CLOCKS = ["CLK_P", "CLK_N", "SYSREF_P", "SYSREF_N"]
CTRL = ["TXA_EN", "TXB_EN", "TX_ARM", "TXA_FAULT", "TXB_FAULT", "AFE_RESET"]


def build_rf(sch: Sch) -> None:
    note(
        sch,
        "HackRF Ultra RF, two coherent channels. "
        "No RFFC5072, no MAX2831, no image-reject lumped bank from Praline: "
        "the AD9084 samples RF directly, so the old high-IF exists only because the MAX5865 could not. "
        "Safe state: MEMS open, PA gate held off by HMC980 until TX_ARM and TXn_EN are both high. "
        "Functional pin numbers are not datasheet balls.",
        20, 20, 1.6,
    )
    note(
        sch,
        "Channel coverage. HF path (ADGM1004, DC-13 GHz): 9 kHz-10 MHz through ADL5569 only; "
        "10 MHz-6 GHz through ADL9005, ADRF5720 and a 4-way preselector. "
        "MW path (ADRF5048, from 100 MHz): 6-18 GHz through ADL9005, ADRF5720, Nyquist filter, Marki balun. "
        "13-18 GHz is MW-only. Overlap is calibrated in the FPGA, not hard-wired.",
        20, 30, 1.27,
    )

    def channel(tag: str, y: float, adc_hf: str, adc_mw: str, dac: str, tx_en: str, fault: str) -> None:
        note(sch, f"Channel {tag}", 20, y - 8, 2.0)
        # RX connector
        pins = place_ic(
            sch, sch.seq("J"), "292MM", 40, y,
            left=[],
            right=[("SIG", "passive")],
            bottom=[("SHIELD", "passive")],
            mfr="Rosenberger or Southwest Microwave",
            mpn="2.92 mm edge launch, 40 GHz, MPN locked to the 2.2 mm RO3003 launch",
            desc=f"RX channel {tag} connector",
            datasheet="https://www.rosenberger.com/",
        )
        stub_gnd(sch, pins["SHIELD"])
        stub_label(sch, pins["SIG"], f"RX{tag}_J", "right")

        mems = place_ic(
            sch, sch.seq("U"), "ADGM1004", 90, y,
            left=[("RFC", "passive")],
            right=[("RF1", "passive"), ("RF2", "passive"), ("RF3", "passive"), ("RF4", "passive")],
            top=[("VDD", "power_in")],
            bottom=[("SCLK", "input"), ("SDI", "input"), ("CS", "input"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADGM1004BCCZ",
            datasheet="https://www.analog.com/en/products/adgm1004.html",
            desc="MEMS SP4T, DC-13 GHz. Open and unpowered is the safe state. Every RFx pin needs a DC path (100 k to GND).",
        )
        stub_label(sch, mems["RFC"], f"RX{tag}_J", "left")
        stub_power(sch, mems["VDD"], "P3V3_RF", "up")
        stub_gnd(sch, mems["GND"])
        stub_label(sch, mems["SCLK"], "RF_SPI_SCK", "down", "global")
        stub_label(sch, mems["SDI"], "RF_SPI_MOSI", "down", "global")
        stub_label(sch, mems["CS"], f"CS_MEMS_{tag}", "down", "global")
        stub_label(sch, mems["RF1"], f"RX{tag}_HF_DIRECT", "right")
        stub_label(sch, mems["RF2"], f"RX{tag}_HF_LNA", "right")
        stub_label(sch, mems["RF3"], f"RX{tag}_TO_MW", "right")
        stub_label(sch, mems["RF4"], f"RX{tag}_LOOP", "right")

        fda = place_ic(
            sch, sch.seq("U"), "ADL5569", 160, y - 18,
            left=[("VIP", "input"), ("VIN", "input")],
            right=[("VOP", "output"), ("VON", "output")],
            top=[("VCC", "power_in")],
            bottom=[("VCM", "input"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADL5569BCPZ",
            datasheet="https://www.analog.com/en/products/adl5569.html",
            desc="DC-coupled differential amplifier for 9 kHz-6 GHz. Single-ended network is the datasheet circuit, re-simulated on RO3003.",
        )
        stub_label(sch, fda["VIP"], f"RX{tag}_HF_DIRECT", "left")
        stub_label(sch, fda["VIN"], f"RX{tag}_HF_SE_N", "left")
        stub_label(sch, fda["VOP"], f"{adc_hf}_P", "right", "hier")
        stub_label(sch, fda["VON"], f"{adc_hf}_N", "right", "hier")
        stub_power(sch, fda["VCC"], "P5V0_RF", "up")
        stub_label(sch, fda["VCM"], f"VCM_{adc_hf}", "down", "global")
        stub_gnd(sch, fda["GND"])

        lna = place_ic(
            sch, sch.seq("U"), "ADL9005", 160, y + 22,
            left=[("RFIN", "passive")],
            right=[("RFOUT", "passive")],
            top=[("VDD", "power_in")],
            bottom=[("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADL9005ACPZN",
            datasheet="https://www.analog.com/en/products/adl9005.html",
            desc="LNA 0.01-26.5 GHz, NF 2.5 dB typical to 14 GHz. Not used below 10 MHz.",
        )
        stub_label(sch, lna["RFIN"], f"RX{tag}_HF_LNA", "left")
        stub_label(sch, lna["RFOUT"], f"RX{tag}_HF_POST", "right")
        stub_power(sch, lna["VDD"], "P5V0_RF", "up")
        stub_gnd(sch, lna["GND"])

        dsa = place_ic(
            sch, sch.seq("U"), "ADRF5720", 230, y + 22,
            left=[("ATTIN", "passive")],
            right=[("ATTOUT", "passive")],
            top=[("VDD", "power_in"), ("VSS", "power_in")],
            bottom=[("CLK", "input"), ("DATA", "input"), ("LE", "input"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADRF5720BCCZN",
            datasheet="https://www.analog.com/en/products/adrf5720.html",
            desc="6-bit 0.5 dB DSA, 9 kHz-40 GHz. The 9 kHz part, not the ADRF5730.",
        )
        stub_label(sch, dsa["ATTIN"], f"RX{tag}_HF_POST", "left")
        stub_label(sch, dsa["ATTOUT"], f"RX{tag}_HF_FLT", "right")
        stub_power(sch, dsa["VDD"], "P3V3_RF", "up")
        stub_power(sch, dsa["VSS"], "N3V3_RF", "up")
        stub_label(sch, dsa["CLK"], "RF_SPI_SCK", "down", "global")
        stub_label(sch, dsa["DATA"], "RF_SPI_MOSI", "down", "global")
        stub_label(sch, dsa["LE"], f"CS_DSA_HF_{tag}", "down", "global")
        stub_gnd(sch, dsa["GND"])

        flt = place_ic(
            sch, sch.seq("U"), "ADGM1004", 300, y + 10,
            left=[("RFC", "passive")],
            right=[("RF1", "passive"), ("RF2", "passive"), ("RF3", "passive"), ("RF4", "passive")],
            top=[("VDD", "power_in")],
            bottom=[("CS", "input"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADGM1004BCCZ",
            datasheet="https://www.analog.com/en/products/adgm1004.html",
            desc="HF preselector. Throws: 9 kHz-30 MHz, 30-500 MHz, 0.5-2 GHz, 2-6 GHz. Knowles DLI / lumped elliptic, EM-simulated.",
        )
        stub_label(sch, flt["RFC"], f"RX{tag}_HF_FLT", "left")
        stub_power(sch, flt["VDD"], "P3V3_RF", "up")
        stub_label(sch, flt["CS"], f"CS_PRESEL_{tag}", "down", "global")
        stub_gnd(sch, flt["GND"])
        for i, band in enumerate(("9k-30M", "30M-500M", "0.5-2G", "2-6G"), start=1):
            stub_label(sch, flt[f"RF{i}"], f"RX{tag}_PRE_{band}", "right")
            two_pin(
                sch, "FL", f"PRESEL {band}", 360, y + 10 - (i - 2) * 8,
                f"RX{tag}_PRE_{band}", f"RX{tag}_HF_COMBINED",
                desc=f"Channel {tag} preselector {band}. Knowles DLI thin-film or lumped elliptic on RO3003. Response is a layout deliverable.",
                mfr="Knowles DLI or equivalent thin-film",
                mpn="custom, passband " + band,
            )

        # tie combined node toward FDA through a switch note: the FDA direct pin is the <10 MHz path.
        # The preselector output joins the FDA VIN/VIP via the SE network. Label it.
        two_pin(
            sch, "C", "100 nF", 400, y + 28,
            f"RX{tag}_HF_COMBINED", f"RX{tag}_HF_DIRECT",
            desc="HF combine into the FDA. The resistor pad around ADL5569 is the datasheet single-ended network.",
            mfr="Murata",
            mpn="C0G, voltage and exact value re-simulated",
        )

        # Microwave path
        sw = place_ic(
            sch, sch.seq("U"), "ADRF5048", 230, y + 55,
            left=[("RFC", "passive")],
            right=[("RF1", "passive"), ("RF2", "passive"), ("RF3", "passive"), ("RF4", "passive")],
            top=[("VDD", "power_in"), ("VSS", "power_in")],
            bottom=[("CTRL", "input"), ("EN", "input"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="ADRF5048BCCZN",
            datasheet="https://www.analog.com/en/products/adrf5048.html",
            desc="Silicon SP4T, 100 MHz-45 GHz, nonreflective. MW path only.",
        )
        stub_label(sch, sw["RFC"], f"RX{tag}_TO_MW", "left")
        stub_power(sch, sw["VDD"], "P3V3_RF", "up")
        stub_power(sch, sw["VSS"], "N3V3_RF", "up")
        stub_label(sch, sw["CTRL"], f"MW_CTRL_{tag}", "down", "global")
        stub_label(sch, sw["EN"], f"MW_EN_{tag}", "down", "global")
        stub_gnd(sch, sw["GND"])
        stub_label(sch, sw["RF1"], f"RX{tag}_MW_6_10", "right")
        stub_label(sch, sw["RF2"], f"RX{tag}_MW_10_14", "right")
        stub_label(sch, sw["RF3"], f"RX{tag}_MW_14_18", "right")
        stub_label(sch, sw["RF4"], f"RX{tag}_MW_THRU", "right")

        lna2 = place_ic(
            sch, sch.seq("U"), "ADL9005", 300, y + 70,
            left=[("RFIN", "passive")],
            right=[("RFOUT", "passive")],
            top=[("VDD", "power_in")],
            bottom=[("GND", "power_in")],
            mfr="Analog Devices", mpn="ADL9005ACPZN",
            datasheet="https://www.analog.com/en/products/adl9005.html",
            desc="Second LNA, MW path, after the Nyquist filter so a strong out-of-zone blocker is already down.",
        )
        # Filters sit between switch and this LNA. Represent the common output.
        for net, band, yy in (
            (f"RX{tag}_MW_6_10", "LPF 6-10 GHz 1st Nyquist", y + 48),
            (f"RX{tag}_MW_10_14", "BPF 10-14 GHz 2nd Nyquist", y + 56),
            (f"RX{tag}_MW_14_18", "BPF 14-18 GHz 2nd Nyquist", y + 64),
            (f"RX{tag}_MW_THRU", "0R lab through, software interlock", y + 72),
        ):
            two_pin(sch, "FL", band, 270, yy, net, f"RX{tag}_MW_LNA_IN",
                    desc=band + ". EM-simulated on the RO3003 coupon. Not a guessed LC from Praline.",
                    mfr="Knowles DLI", mpn="custom")
        stub_label(sch, lna2["RFIN"], f"RX{tag}_MW_LNA_IN", "left")
        stub_label(sch, lna2["RFOUT"], f"RX{tag}_MW_DSA_IN", "right")
        stub_power(sch, lna2["VDD"], "P5V0_RF", "up")
        stub_gnd(sch, lna2["GND"])

        dsa2 = place_ic(
            sch, sch.seq("U"), "ADRF5720", 370, y + 70,
            left=[("ATTIN", "passive")],
            right=[("ATTOUT", "passive")],
            top=[("VDD", "power_in"), ("VSS", "power_in")],
            bottom=[("LE", "input"), ("GND", "power_in")],
            mfr="Analog Devices", mpn="ADRF5720BCCZN",
            datasheet="https://www.analog.com/en/products/adrf5720.html",
            desc="MW DSA.",
        )
        stub_label(sch, dsa2["ATTIN"], f"RX{tag}_MW_DSA_IN", "left")
        stub_label(sch, dsa2["ATTOUT"], f"RX{tag}_MW_BAL_IN", "right")
        stub_power(sch, dsa2["VDD"], "P3V3_RF", "up")
        stub_power(sch, dsa2["VSS"], "N3V3_RF", "up")
        stub_label(sch, dsa2["LE"], f"CS_DSA_MW_{tag}", "down", "global")
        stub_gnd(sch, dsa2["GND"])

        bal = place_ic(
            sch, sch.seq("T"), "BALUN_18G", 440, y + 70,
            left=[("IN", "passive")],
            right=[("OUTP", "passive"), ("OUTN", "passive")],
            bottom=[("GND", "passive")],
            mfr="Marki Microwave",
            mpn="wideband balun from the AD9084 UG-2300 input network, re-simulated on 127 um RO3003",
            datasheet="https://www.analog.com/en/products/ad9084.html",
            desc="Differential launch into the AD9084 MW ADC. Exact dash number is the one whose S-parameters match UG-2300 after the stackup changes.",
        )
        stub_label(sch, bal["IN"], f"RX{tag}_MW_BAL_IN", "left")
        stub_label(sch, bal["OUTP"], f"{adc_mw}_P", "right", "hier")
        stub_label(sch, bal["OUTN"], f"{adc_mw}_N", "right", "hier")
        stub_gnd(sch, bal["GND"])

        # Limiter on the MW/HF LNA input, before the LNA, shunt PIN.
        lim = place_ic(
            sch, sch.seq("D"), "MADL-011023", 90, y + 40,
            left=[("A", "passive")],
            right=[("K", "passive")],
            mfr="MACOM",
            mpn="MADL-011023-14150T",
            desc="Two-stage shunt PIN limiter. Survival target +30 dBm CW, proved on a coupon, not claimed as measured here. First element after the MEMS on the LNA throws.",
        )
        stub_label(sch, lim["A"], f"RX{tag}_HF_LNA", "left")
        stub_gnd(sch, lim["K"])

        # TX
        pa = place_ic(
            sch, sch.seq("U"), "HMC998A", 520, y + 20,
            left=[("RFIN", "passive"), ("VGG", "input")],
            right=[("RFOUT", "passive")],
            top=[("VDD", "power_in")],
            bottom=[("GND", "power_in")],
            mfr="Analog Devices",
            mpn="HMC998APM5E",
            datasheet="https://www.analog.com/en/products/hmc998apm5e.html",
            desc="Distributed PA, DC-22 GHz, P1dB +32 dBm, 15 V, 500 mA. Depletion pHEMT: drain only after negative gate, and only through HMC980.",
        )
        bias = place_ic(
            sch, sch.seq("U"), "HMC980", 520, y + 55,
            left=[("EN", "input"), ("VDD", "power_in")],
            right=[("VGATE", "output"), ("VDRAIN", "power_out"), ("ALM", "output")],
            bottom=[("ISENSE", "passive"), ("GND", "power_in")],
            mfr="Analog Devices",
            mpn="HMC980LP4E",
            datasheet="https://www.analog.com/en/products/hmc980.html",
            desc="Active bias controller. Internal negative generator, sequences gate before drain, holds 500 mA. EN is pulled down.",
        )
        stub_power(sch, bias["VDD"], "P15V_PA", "left")
        stub_label(sch, bias["EN"], f"PA_EN_{tag}", "left")
        stub_label(sch, bias["VGATE"], f"PA_VGG_{tag}", "right")
        stub_label(sch, bias["VDRAIN"], f"PA_VDD_{tag}", "right")
        stub_label(sch, bias["ALM"], fault, "right", "hier")
        stub_gnd(sch, bias["GND"])
        stub_label(sch, bias["ISENSE"], f"PA_SENSE_{tag}", "down")
        stub_label(sch, pa["VGG"], f"PA_VGG_{tag}", "left")
        stub_label(sch, pa["VDD"], f"PA_VDD_{tag}", "up")
        stub_gnd(sch, pa["GND"])
        stub_label(sch, pa["RFIN"], f"TX{tag}_PA_IN", "left")
        stub_label(sch, pa["RFOUT"], f"TX{tag}_PA_OUT", "right")

        # arming AND: TX_ARM, TXn_EN, bias-not-fault
        gate = place_ic(
            sch, sch.seq("U"), "74LVC1G08", 430, y + 55,
            left=[("A", "input"), ("B", "input")],
            right=[("Y", "output")],
            top=[("VCC", "power_in")],
            bottom=[("GND", "power_in")],
            mfr="Nexperia",
            mpn="74LVC1G08GW",
            desc="Fail-safe arming. Both inputs pulled down. HMC980 still refuses to apply drain until its own supply and gate generator are up. This gate does not decode the RF path.",
        )
        stub_label(sch, gate["A"], "TX_ARM", "left", "hier")
        stub_label(sch, gate["B"], tx_en, "left", "hier")
        stub_label(sch, gate["Y"], f"PA_EN_{tag}", "right")
        stub_power(sch, gate["VCC"], "P3V3", "up")
        stub_gnd(sch, gate["GND"])
        two_pin(sch, "R", "100 k", 400, y + 48, "TX_ARM", "GND", kind_b="local",
                desc="Pulldown. Open key or unprogrammed FPGA cannot arm the PA.", mfr="Panasonic", mpn="ERA-2AEB104X")

        jtx = place_ic(
            sch, sch.seq("J"), "292MM", 620, y + 20,
            left=[("SIG", "passive")],
            right=[],
            bottom=[("SHIELD", "passive")],
            mfr="Rosenberger or Southwest Microwave",
            mpn="2.92 mm edge launch, 40 GHz",
            desc=f"TX channel {tag}",
        )
        stub_label(sch, jtx["SIG"], f"TX{tag}_CONN", "left")
        stub_gnd(sch, jtx["SHIELD"])

        cpl = place_ic(
            sch, sch.seq("U"), "COUPLER_20DB", 570, y + 20,
            left=[("IN", "passive")],
            right=[("OUT", "passive"), ("CPL", "passive")],
            bottom=[("ISO", "passive")],
            mfr="Marki Microwave",
            mpn="20 dB directional coupler, DC-26.5 GHz, ordering code locked at layout",
            desc="Samples TX into the RX MEMS loopback throw. Isolated port is 50 ohm. Default MEMS state does not select loopback.",
        )
        stub_label(sch, cpl["IN"], f"TX{tag}_PA_OUT", "left")
        stub_label(sch, cpl["OUT"], f"TX{tag}_CONN", "right")
        stub_label(sch, cpl["CPL"], f"RX{tag}_LOOP", "right")
        stub_label(sch, cpl["ISO"], f"TX{tag}_ISO", "down")
        two_pin(sch, "R", "50", 570, y + 40, f"TX{tag}_ISO", "GND",
                desc="Coupler isolated-port termination, 50 ohm, RF rated.", mfr="Vishay", mpn="FC0402E50R0BTBST1")

        # DAC into a balun then the PA. DSA in front of the PA for level control.
        tdsa = place_ic(
            sch, sch.seq("U"), "ADRF5720", 400, y + 20,
            left=[("ATTIN", "passive")],
            right=[("ATTOUT", "passive")],
            top=[("VDD", "power_in"), ("VSS", "power_in")],
            bottom=[("LE", "input"), ("GND", "power_in")],
            mfr="Analog Devices", mpn="ADRF5720BCCZN",
            datasheet="https://www.analog.com/en/products/adrf5720.html",
            desc="TX level control ahead of the PA.",
        )
        stub_label(sch, tdsa["ATTIN"], f"TX{tag}_BAL_OUT", "left")
        stub_label(sch, tdsa["ATTOUT"], f"TX{tag}_PA_IN", "right")
        stub_power(sch, tdsa["VDD"], "P3V3_RF", "up")
        stub_power(sch, tdsa["VSS"], "N3V3_RF", "up")
        stub_label(sch, tdsa["LE"], f"CS_DSA_TX_{tag}", "down", "global")
        stub_gnd(sch, tdsa["GND"])

        tbal = place_ic(
            sch, sch.seq("T"), "BALUN_18G", 330, y + 20,
            left=[("INP", "passive"), ("INN", "passive")],
            right=[("OUT", "passive")],
            bottom=[("GND", "passive")],
            mfr="Marki Microwave",
            mpn="same family as the RX balun, UG-2300 DAC network re-simulated",
            desc="DAC differential to single-ended.",
        )
        stub_label(sch, tbal["INP"], f"{dac}_P", "left", "hier")
        stub_label(sch, tbal["INN"], f"{dac}_N", "left", "hier")
        stub_label(sch, tbal["OUT"], f"TX{tag}_BAL_OUT", "right")
        stub_gnd(sch, tbal["GND"])

    channel("A", 80, "ADC0", "ADC1", "DAC0", "TXA_EN", "TXA_FAULT")
    channel("B", 280, "ADC2", "ADC3", "DAC1", "TXB_EN", "TXB_FAULT")
    note(
        sch,
        "Limiter coupon and 18 GHz launch are layout gates. Do not fabricate from this sheet. "
        "A single-port half-duplex SMA is intentionally absent: 41 dB switch isolation at 18 GHz cannot separate a +30 dBm TX from the RX. "
        "One antenna needs an external circulator or coupler. J_RX and J_TX are both 2.92 mm.",
        20, 430, 1.27,
    )


def build_converter(sch: Sch) -> None:
    note(
        sch,
        "AD9084 Apollo MxFE, Rev D. 4x 12-bit ADC to 20 GSPS, 4x 16-bit DAC to 28 GSPS, analog bandwidth to 18 GHz. "
        "This board uses 2T2R: ADC0/ADC2 are the DC-coupled HF inputs, ADC1/ADC3 the balun MW inputs, DAC0/DAC1 the two TX channels. "
        "DAC2 is the internal cal tone, DAC3 is terminated. JESD204C lanes are global nets JESD_ADC_P0..15 / N and JESD_DAC_P0..15 / N. "
        "48 physical lanes exist on the BGA; 16 each direction are routed, the rest are parked per UG-2300. "
        "Sub-rail currents below are the datasheet's low-rate illustration and are NOT the 20 GSPS budget. Budget 40 W for the MxFE and follow UG-2300 for decoupling and sequence.",
        20, 18, 1.4,
    )
    left = [(n, "passive") for n in ANALOG] + [(n, "input") for n in CLOCKS]
    right = [("SCLK", "input"), ("SDIO", "bidirectional"), ("CS", "input"),
             ("RESET", "input"), ("IRQ", "output"), ("TRIG", "input")]
    top = [
        ("AVDD1P0_ADC", "power_in"),
        ("AVDD1P0_ADCBK", "power_in"),
        ("AVDD1P0_DAC", "power_in"),
        ("AVDD1P0_DAC_DIG", "power_in"),
        ("AVDD1P0_CK", "power_in"),
        ("AVDD1P8", "power_in"),
        ("AVDD_SERDES", "power_in"),
    ]
    bottom = [("GND", "power_in"), ("VCM0", "output"), ("VCM1", "output")]
    pins = place_ic(
        sch, sch.seq("U"), "AD9084", 180, 140,
        left=left, right=right, top=top, bottom=bottom,
        mfr="Analog Devices",
        mpn="AD9084-BBIZ",
        datasheet="https://www.analog.com/en/products/ad9084.html",
        desc="Apollo MxFE, 24 mm x 26 mm, 899-ball BGA, 0.80 mm. Land pattern from Rev D, not from this symbol.",
        footprint="BGA-899 24x26 mm 0.80 mm, datasheet Rev D",
    )
    for n in ANALOG:
        stub_label(sch, pins[n], n, "left", "hier")
    for n in CLOCKS:
        stub_label(sch, pins[n], n, "left", "hier")
    stub_label(sch, pins["SCLK"], "AFE_SPI_SCK", "right", "global")
    stub_label(sch, pins["SDIO"], "AFE_SPI_SDIO", "right", "global")
    stub_label(sch, pins["CS"], "AFE_SPI_CS", "right", "global")
    stub_label(sch, pins["RESET"], "AFE_RESET", "right", "hier")
    stub_label(sch, pins["IRQ"], "AFE_IRQ", "right", "global")
    stub_label(sch, pins["TRIG"], "TRIG", "right", "global")
    # Rails are ferrite-isolated. Do not pour them together.
    rail_of = {
        "AVDD1P0_ADC": "P1V0_ADC",
        "AVDD1P0_ADCBK": "P1V0_ADCBK",
        "AVDD1P0_DAC": "P1V0_DAC",
        "AVDD1P0_DAC_DIG": "P1V0_DACDIG",
        "AVDD1P0_CK": "P1V0_CK",
        "AVDD1P8": "P1V8_AFE",
        "AVDD_SERDES": "P0V9_SERDES",
    }
    for pname, rail in rail_of.items():
        stub_power(sch, pins[pname], rail, "up")
    stub_gnd(sch, pins["GND"])
    stub_label(sch, pins["VCM0"], "VCM_ADC0", "down", "global")
    stub_label(sch, pins["VCM1"], "VCM_ADC2", "down", "global")

    note(
        sch,
        "Clock input is direct RF, AC-coupled, 8-20 GHz, about +5 dBm, 100 ohm differential on die (AD9084 Rev D Table 7). "
        "The on-chip PLL is bypassed for the lowest jitter. SYSREF is Subclass 1 from the LMK5C33216.",
        20, 250, 1.27,
    )
    # JESD lane markers as a compact row of globals, generated from a tiny symbol with 4 pins repeated.
    y = 280
    for direction, prefix, count in (("ADC", "JESD_ADC", 16), ("DAC", "JESD_DAC", 16)):
        for i in range(count):
            yy = y + (i % 16) * 3.5
            xx = 40 if direction == "ADC" else 220
            label(sch, "global", f"{prefix}_P{i}", xx, yy, 0)
            label(sch, "global", f"{prefix}_N{i}", xx + 40, yy, 0)
        y += 70
    note(
        sch,
        "JESD204C global nets JESD_ADC_P0..15 and JESD_ADC_N0..15 leave the AD9084 STX pins toward the Versal GTM. "
        "JESD_DAC_P/N0..15 are the SRX pins. Lane-to-ball assignment is a constraint file written against Rev D and the Versal package, "
        "after the channel-loss simulation. Line rate up to 28.21 Gbit/s NRZ. Unused STX/SRX lanes are terminated per UG-2300.",
        20, 430, 1.27,
    )
    note(
        sch,
        "Power domains stay split by ferrite or by their own regulator, per Rev D Table 3. "
        "AVDD1P0_CK is post-regulated by an LT3045. AVDD1P0_ADCBK is the multi-amp rail and is a Silent Switcher module, not an LDO. "
        "SERDES voltage is whatever Rev D Table 3 specifies for the JESD supply; the net name P0V9_SERDES is the contract, the number is confirmed from that table before the PCB is taped out.",
        20, 450, 1.27,
    )


def build_clock(sch: Sch) -> None:
    note(
        sch,
        "One root oscillator. No Si5351, and no 74HC4051 in the clock path: that mux is a spur and jitter source on Praline and it does not survive a 12-bit, 20 GSPS converter. "
        "OCXO to LMK5C33216 to ADF4382A to LMX1214 to the AD9084 CLK pins. 10 MHz input disciplines the LMK. PPS is a separate SMA, not a mode of the clock SMA.",
        20, 18, 1.4,
    )
    ocxo = place_ic(
        sch, sch.seq("U"), "OCXO_100M", 50, 70,
        left=[("VCC", "power_in")],
        right=[("RF", "output")],
        bottom=[("GND", "power_in"), ("VC", "input")],
        mfr="Wenzel Associates",
        mpn="Sprinter 100.000 MHz sine, +13 dBm, 12 V. Ordering code bought against the phase-noise mask in the architecture note.",
        desc="Close-in phase noise is a quartz OCXO specification, not a MEMS part. Mask: -130 dBc/Hz at 100 Hz, -160 dBc/Hz at 10 kHz, floor at or below -175 dBc/Hz.",
    )
    stub_power(sch, ocxo["VCC"], "P12V_OCXO", "left")
    stub_gnd(sch, ocxo["GND"])
    stub_label(sch, ocxo["RF"], "OCXO_100M", "right")
    stub_label(sch, ocxo["VC"], "OCXO_VC", "down")

    lmk = place_ic(
        sch, sch.seq("U"), "LMK5C33216", 140, 90,
        left=[("XO_P", "input"), ("REF_P", "input"), ("REF_N", "input")],
        right=[("OUT0_P", "output"), ("OUT0_N", "output"), ("OUT1_P", "output"),
               ("OUT1_N", "output"), ("SYSREF_P", "output"), ("SYSREF_N", "output"),
               ("CLK10", "output"), ("PPS", "output")],
        top=[("VCC", "power_in")],
        bottom=[("SDA", "bidirectional"), ("SCL", "input"), ("GND", "power_in")],
        mfr="Texas Instruments",
        mpn="LMK5C33216",
        datasheet="https://www.ti.com/product/LMK5C33216",
        desc="BAW jitter cleaner and JESD clock. 40 fs class at 491.52 MHz from the BAW APLL, independent of the reference once locked. EEPROM boot.",
    )
    stub_label(sch, lmk["XO_P"], "OCXO_100M", "left")
    stub_label(sch, lmk["REF_P"], "CLKIN_10M", "left")
    stub_label(sch, lmk["REF_N"], "CLKIN_10M_N", "left")
    stub_power(sch, lmk["VCC"], "P3V3_CLK", "up")
    stub_gnd(sch, lmk["GND"])
    stub_label(sch, lmk["SDA"], "CLK_I2C_SDA", "down", "global")
    stub_label(sch, lmk["SCL"], "CLK_I2C_SCL", "down", "global")
    stub_label(sch, lmk["OUT0_P"], "REF_ADF_P", "right")
    stub_label(sch, lmk["OUT0_N"], "REF_ADF_N", "right")
    stub_label(sch, lmk["OUT1_P"], "FPGA_REFCLK_P", "right", "global")
    stub_label(sch, lmk["OUT1_N"], "FPGA_REFCLK_N", "right", "global")
    stub_label(sch, lmk["SYSREF_P"], "SYSREF_P", "right", "hier")
    stub_label(sch, lmk["SYSREF_N"], "SYSREF_N", "right", "hier")
    stub_label(sch, lmk["CLK10"], "CLKOUT_10M", "right")
    stub_label(sch, lmk["PPS"], "PPS", "right")

    adf = place_ic(
        sch, sch.seq("U"), "ADF4382A", 250, 70,
        left=[("REFP", "input"), ("REFN", "input")],
        right=[("RFOUTP", "output"), ("RFOUTN", "output")],
        top=[("V5", "power_in"), ("V3", "power_in")],
        bottom=[("CS", "input"), ("SCLK", "input"), ("SDIO", "bidirectional"), ("GND", "power_in")],
        mfr="Analog Devices",
        mpn="ADF4382A",
        datasheet="https://www.analog.com/en/products/adf4382a.html",
        desc="Fundamental VCO 11.5-21 GHz, 20 fs integrated jitter at 20 GHz. Directly clocks the AD9084 (clock input range 8-20 GHz). No doubler in the path.",
    )
    stub_label(sch, adf["REFP"], "REF_ADF_P", "left")
    stub_label(sch, adf["REFN"], "REF_ADF_N", "left")
    stub_label(sch, adf["RFOUTP"], "CLK_RAW_P", "right")
    stub_label(sch, adf["RFOUTN"], "CLK_RAW_N", "right")
    stub_power(sch, adf["V5"], "P5V_PLL", "up")
    stub_power(sch, adf["V3"], "P3V3_PLL", "up")
    stub_label(sch, adf["CS"], "CLK_SPI_CS_ADF", "down", "global")
    stub_label(sch, adf["SCLK"], "CLK_SPI_SCK", "down", "global")
    stub_label(sch, adf["SDIO"], "CLK_SPI_SDIO", "down", "global")
    stub_gnd(sch, adf["GND"])

    buf = place_ic(
        sch, sch.seq("U"), "LMX1214", 360, 70,
        left=[("CLKINP", "input"), ("CLKINN", "input")],
        right=[("OUT0P", "output"), ("OUT0N", "output"), ("OUT1P", "output"), ("OUT1N", "output")],
        top=[("VCC", "power_in")],
        bottom=[("CS", "input"), ("GND", "power_in")],
        mfr="Texas Instruments",
        mpn="LMX1214",
        datasheet="https://www.ti.com/product/LMX1214",
        desc="300 MHz-18 GHz buffer/divider, about 5 fs additive jitter in band. OUT0 is the AD9084 clock. OUT1 is a test port, DNP SMA.",
    )
    stub_label(sch, buf["CLKINP"], "CLK_RAW_P", "left")
    stub_label(sch, buf["CLKINN"], "CLK_RAW_N", "left")
    stub_label(sch, buf["OUT0P"], "CLK_P", "right", "hier")
    stub_label(sch, buf["OUT0N"], "CLK_N", "right", "hier")
    stub_label(sch, buf["OUT1P"], "CLK_TEST_P", "right")
    stub_label(sch, buf["OUT1N"], "CLK_TEST_N", "right")
    stub_power(sch, buf["VCC"], "P2V5_CLK", "up")
    stub_label(sch, buf["CS"], "CLK_SPI_CS_LMX", "down", "global")
    stub_gnd(sch, buf["GND"])

    for name, net, x in (("CLKIN", "CLKIN_10M", 40), ("CLKOUT", "CLKOUT_10M", 200), ("PPS", "PPS", 250)):
        pins = place_ic(
            sch, sch.seq("J"), "SMA", x, 160,
            left=[("SIG", "passive")], bottom=[("SHIELD", "passive")], right=[],
            mfr="Amphenol or Rosenberger",
            mpn="SMA edge launch, 50 ohm, 18 GHz is unnecessary here; use a precision SMA",
            desc=f"{name} connector. 10 MHz CMOS/sine, AC-coupled, series 33 ohm on the output, TVS on the input.",
        )
        stub_label(sch, pins["SIG"], net, "left")
        stub_gnd(sch, pins["SHIELD"])
    note(
        sch,
        "CLKIN accepts 10 MHz, 50 ohm, 0 to +10 dBm, AC coupled, with a 3.3 V TVS after the coupling cap. "
        "It disciplines the LMK; it is not muxed onto the converter clock. "
        "CLKOUT is 10 MHz from an LMK LVCMOS output through a 33 ohm series resistor. "
        "PPS is bidirectional under FPGA control and is the trigger, replacing Praline's P1/P2 analog-mux trigger.",
        20, 190, 1.27,
    )


def build_fpga(sch: Sch) -> None:
    note(
        sch,
        "AMD Versal Premium XCVP1802. GTM must cover 16 RX plus 16 TX JESD204C lanes at 28.21 Gbit/s NRZ and 8 lanes at 112 Gbit/s PAM4 for two QSFP-DD cages. "
        "Package and speed grade come from the channel-loss report. VP1802 is the part used on the VPK180, so the lane count is not a guess; a smaller Premium is only substituted if its GTM table still covers this contract. "
        "The iCE40UP5K is not continued: 5280 LUT4 cannot absorb a JESD204C link, a DDC, or a packetizer. "
        "No LPC4330. The Versal PS (A72) runs the instrument; the FX20 is only the USB device port.",
        20, 18, 1.4,
    )
    pins = place_ic(
        sch, sch.seq("U"), "XCVP1802", 200, 120,
        left=[("REFCLK_P", "input"), ("REFCLK_N", "input"), ("SYSREF_P", "input"), ("SYSREF_N", "input"),
              ("AFE_SPI_SCK", "output"), ("AFE_SPI_SDIO", "bidirectional"), ("AFE_SPI_CS", "output"),
              ("AFE_RESET", "output")]
        + [(f"GTM_ADC_P{i}", "input") for i in range(4)]
        + [(f"GTM_DAC_P{i}", "output") for i in range(4)],
        right=[("USB_LVDS_CLK_P", "output"), ("USB_LVDS_CLK_N", "output"),
               ("FX_CLK", "bidirectional"), ("QSFPDD_TX_P0", "output"), ("QSFPDD_RX_P0", "input"),
               ("TXA_EN", "output"), ("TXB_EN", "output"), ("TX_ARM_FB", "input")],
        top=[("VCCINT", "power_in"), ("VCC_GTM", "power_in"), ("VCCAUX", "power_in"), ("VCCO_DDR", "power_in")],
        bottom=[("GND", "power_in"), ("TCK", "input"), ("TDI", "input"), ("TDO", "output"), ("TMS", "input")],
        mfr="AMD",
        mpn="XCVP1802, GTM package rated for 28.21 Gbit/s NRZ and 112 Gbit/s PAM4",
        datasheet="https://www.amd.com/en/products/adaptive-socs-and-fpgas/versal.html",
        desc="Functional contract only. Full bank assignment is the XDC, written after the package ball map is frozen. Outline on the PCB is 50 mm until the chosen package drawing replaces it.",
    )
    stub_label(sch, pins["REFCLK_P"], "FPGA_REFCLK_P", "left", "global")
    stub_label(sch, pins["REFCLK_N"], "FPGA_REFCLK_N", "left", "global")
    stub_label(sch, pins["SYSREF_P"], "SYSREF_P", "left", "hier")
    stub_label(sch, pins["SYSREF_N"], "SYSREF_N", "left", "hier")
    stub_label(sch, pins["AFE_SPI_SCK"], "AFE_SPI_SCK", "left", "global")
    stub_label(sch, pins["AFE_SPI_SDIO"], "AFE_SPI_SDIO", "left", "global")
    stub_label(sch, pins["AFE_SPI_CS"], "AFE_SPI_CS", "left", "global")
    stub_label(sch, pins["AFE_RESET"], "AFE_RESET", "left", "hier")
    for i in range(4):
        # Representative lanes shown on the symbol; all 16 exist as global labels below.
        stub_label(sch, pins[f"GTM_ADC_P{i}"], f"JESD_ADC_P{i}", "left", "global")
        stub_label(sch, pins[f"GTM_DAC_P{i}"], f"JESD_DAC_P{i}", "left", "global")
    stub_label(sch, pins["USB_LVDS_CLK_P"], "LVDS_CLK_P", "right", "global")
    stub_label(sch, pins["USB_LVDS_CLK_N"], "LVDS_CLK_N", "right", "global")
    stub_label(sch, pins["FX_CLK"], "FX_CLK", "right", "global")
    stub_label(sch, pins["QSFPDD_TX_P0"], "QSFP_TX_P0", "right", "global")
    stub_label(sch, pins["QSFPDD_RX_P0"], "QSFP_RX_P0", "right", "global")
    stub_label(sch, pins["TXA_EN"], "TXA_EN", "right", "hier")
    stub_label(sch, pins["TXB_EN"], "TXB_EN", "right", "hier")
    stub_label(sch, pins["TX_ARM_FB"], "TX_ARM", "right", "hier")
    stub_power(sch, pins["VCCINT"], "P0V80_VCCINT", "up")
    stub_power(sch, pins["VCC_GTM"], "P0V88_GTM", "up")
    stub_power(sch, pins["VCCAUX"], "P1V5_AUX", "up")
    stub_power(sch, pins["VCCO_DDR"], "P1V1_DDR", "up")
    stub_gnd(sch, pins["GND"])
    for jtag in ("TCK", "TDI", "TDO", "TMS"):
        stub_label(sch, pins[jtag], jtag, "down", "global")

    y = 250
    for i in range(16):
        label(sch, "global", f"JESD_ADC_N{i}", 30, y + i * 3.2, 0)
        label(sch, "global", f"JESD_DAC_N{i}", 90, y + i * 3.2, 0)
        label(sch, "global", f"LVDS_P{i}", 150, y + i * 3.2, 0)
        label(sch, "global", f"LVDS_N{i}", 200, y + i * 3.2, 0)
        label(sch, "global", f"FX_D{i}", 250, y + i * 3.2, 0)
    for i in range(16, 32):
        label(sch, "global", f"FX_D{i}", 310, 250 + (i - 16) * 3.2, 0)
    note(
        sch,
        "LVDS_P/N0..15 and LVDS_CLK are the FX20 GPIF III receive bus: FPGA to host only, 1.25 Gbit/s per lane, 16 lanes. "
        "FX_D0..31 plus FX_CLK is the LVCMOS bus. FX20 transmits toward the FPGA at 80 MHz DDR on that bus, about 5 Gbit/s, which is the USB TX-sample ceiling. "
        "Wideband TX uses the QSFP-DD, not USB. "
        "QSFP_TX_Pn / QSFP_RX_Pn and QSFP2_TX_Pn / QSFP2_RX_Pn for n=0..3 are the two 400GbE ports, 112 Gbit/s PAM4.",
        20, 320, 1.27,
    )
    ddr = place_ic(
        sch, sch.seq("U"), "DDR5", 420, 80,
        left=[("DQ", "bidirectional"), ("DQS", "bidirectional"), ("CK", "input"), ("CA", "input")],
        top=[("VDD", "power_in"), ("VDDQ", "power_in")],
        bottom=[("GND", "power_in")],
        right=[],
        mfr="Micron",
        mpn="DDR5-5600 component, 8 GB total across the PS and PL controllers, x16 devices",
        desc="Capture buffer and PS memory. Address map in the architecture note. VTT termination on the controller side per Micron TN.",
    )
    stub_power(sch, ddr["VDD"], "P1V1_DDR", "up")
    stub_power(sch, ddr["VDDQ"], "P1V1_DDR", "up")
    stub_gnd(sch, ddr["GND"])
    stub_label(sch, ddr["DQ"], "DDR_DQ", "left")
    stub_label(sch, ddr["DQS"], "DDR_DQS", "left")
    stub_label(sch, ddr["CK"], "DDR_CK", "left")
    stub_label(sch, ddr["CA"], "DDR_CA", "left")

    flash = place_ic(
        sch, sch.seq("U"), "MT35XU02G", 420, 140,
        left=[("CS", "input"), ("CLK", "input"), ("IO0", "bidirectional")],
        right=[("IO1", "bidirectional"), ("IO2", "bidirectional"), ("IO3", "bidirectional"),
               ("IO4", "bidirectional"), ("IO5", "bidirectional"), ("IO6", "bidirectional"), ("IO7", "bidirectional")],
        top=[("VCC", "power_in")],
        bottom=[("GND", "power_in"), ("RESET", "input")],
        mfr="Micron",
        mpn="MT35XU02GCBA1G12-0AUT",
        desc="2 Gbit octal SPI NOR for the Versal boot image. Reset strapped so an unprogrammed rail does not float the bus.",
    )
    stub_power(sch, flash["VCC"], "P1V8", "up")
    stub_gnd(sch, flash["GND"])
    stub_label(sch, flash["CS"], "OSPI_CS", "left", "global")
    stub_label(sch, flash["CLK"], "OSPI_CLK", "left", "global")
    for i in range(8):
        side = "left" if i == 0 else "right"
        stub_label(sch, flash[f"IO{i}"], f"OSPI_IO{i}", side, "global")
    stub_label(sch, flash["RESET"], "OSPI_RESET", "down", "global")

    sd = place_ic(
        sch, sch.seq("J"), "MICROSD", 420, 200,
        left=[("CLK", "input"), ("CMD", "bidirectional"), ("DAT0", "bidirectional")],
        right=[("DAT1", "bidirectional"), ("DAT2", "bidirectional"), ("DAT3", "bidirectional"), ("CD", "output")],
        top=[("VCC", "power_in")],
        bottom=[("GND", "power_in")],
        mfr="Molex",
        mpn="microSD push-push, 3.3 V",
        desc="Field boot image. 3.3 V, series resistors, ESD on the connector side.",
    )
    stub_power(sch, sd["VCC"], "P3V3", "up")
    stub_gnd(sch, sd["GND"])
    for p in ("CLK", "CMD", "DAT0", "DAT1", "DAT2", "DAT3", "CD"):
        stub_label(sch, sd[p], f"SD_{p}", "left" if p in ("CLK", "CMD", "DAT0") else "right", "global")

    note(
        sch,
        "JTAG is a 2x7 1.27 mm AMD header on TCK/TDI/TDO/TMS plus SRST, with the standard Versal pinout. "
        "Sequencing of VCCINT, VCC_GTM, VCCAUX and VCCO is the ADM1266 state machine taken from the Versal power-on diagram for this device, not a free invention.",
        20, 360, 1.27,
    )


def build_host(sch: Sch) -> None:
    note(
        sch,
        "Two host ports. USB-C is a 20 Gbit/s device (FX20), the way a HackRF is a peripheral. "
        "QSFP-DD is 400GbE, because a 10 GHz instantaneous bandwidth at 12-bit complex is about 240 Gbit/s and does not fit in USB. "
        "FX20 LVDS is FPGA-to-host only. Host-to-FPGA samples on USB use the 32-bit LVCMOS bus at about 5 Gbit/s.",
        20, 18, 1.4,
    )
    usb = place_ic(
        sch, sch.seq("J"), "USB_C", 40, 70,
        right=[("TX1P", "passive"), ("TX1N", "passive"), ("RX1P", "passive"), ("RX1N", "passive"),
               ("TX2P", "passive"), ("TX2N", "passive"), ("RX2P", "passive"), ("RX2N", "passive"),
               ("CC1", "passive"), ("CC2", "passive"), ("VBUS", "power_in")],
        bottom=[("SHIELD", "passive"), ("GND", "power_in")],
        left=[],
        mfr="Amphenol",
        mpn="USB Type-C 24-pin, mid-mount, 20 Gbit/s capable shell",
        desc="USB 3.2 Gen 2x2 receptacle. SuperSpeed pairs are 90 ohm. Shield bonded to chassis at one point.",
    )
    for p in ("TX1P", "TX1N", "RX1P", "RX1N", "TX2P", "TX2N", "RX2P", "RX2N", "CC1", "CC2"):
        stub_label(sch, usb[p], f"USBC_{p}", "right")
    stub_label(sch, usb["VBUS"], "VBUS_CONNECTOR", "right")
    stub_gnd(sch, usb["GND"])
    stub_gnd(sch, usb["SHIELD"])

    fx = place_ic(
        sch, sch.seq("U"), "CYUSB4024", 150, 90,
        left=[("USB_TX1P", "bidirectional"), ("USB_TX1N", "bidirectional"),
              ("USB_RX1P", "bidirectional"), ("USB_RX1N", "bidirectional"),
              ("USB_TX2P", "bidirectional"), ("USB_TX2N", "bidirectional"),
              ("USB_RX2P", "bidirectional"), ("USB_RX2N", "bidirectional")],
        right=[("LVDS_CLK_P", "input"), ("LVDS_CLK_N", "input")]
        + [(f"LVDS_P{i}", "input") for i in range(4)],
        top=[("VDD", "power_in"), ("VDDIO", "power_in")],
        bottom=[("GND", "power_in"), ("FX_CLK", "bidirectional")],
        mfr="Infineon",
        mpn="CYUSB4024, 16-lane LVDS variant, ordering code from datasheet 002-33684 Rev J",
        datasheet="https://www.infineon.com/products/universal-serial-bus/usb-3-2-peripheral-controllers/ez-usb-fx20-usb-20-gbps-peripheral-controller",
        desc="EZ-USB FX20, USB 3.2 Gen 2x2 device, 169-ball. Orientation and lane polarity are corrected inside the PHY. Payload about 17.6 Gbit/s.",
    )
    pairs = [("USB_TX1P", "USBC_TX1P"), ("USB_TX1N", "USBC_TX1N"),
             ("USB_RX1P", "USBC_RX1P"), ("USB_RX1N", "USBC_RX1N"),
             ("USB_TX2P", "USBC_TX2P"), ("USB_TX2N", "USBC_TX2N"),
             ("USB_RX2P", "USBC_RX2P"), ("USB_RX2N", "USBC_RX2N")]
    for pin, net in pairs:
        stub_label(sch, fx[pin], net, "left")
    stub_label(sch, fx["LVDS_CLK_P"], "LVDS_CLK_P", "right", "global")
    stub_label(sch, fx["LVDS_CLK_N"], "LVDS_CLK_N", "right", "global")
    for i in range(4):
        stub_label(sch, fx[f"LVDS_P{i}"], f"LVDS_P{i}", "right", "global")
    stub_label(sch, fx["FX_CLK"], "FX_CLK", "down", "global")
    stub_power(sch, fx["VDD"], "P1V8", "up")
    stub_power(sch, fx["VDDIO"], "P3V3", "up")
    stub_gnd(sch, fx["GND"])

    pd = place_ic(
        sch, sch.seq("U"), "TPS26750", 150, 200,
        left=[("CC1", "bidirectional"), ("CC2", "bidirectional")],
        right=[("I2C_SDA", "bidirectional"), ("I2C_SCL", "output"), ("FAULT", "output")],
        top=[("VBUS_SENSE", "power_in"), ("VIN", "power_in")],
        bottom=[("GND", "power_in")],
        mfr="Texas Instruments",
        mpn="TPS26750",
        datasheet="https://www.ti.com/product/TPS26750",
        desc="USB-PD 3.1 EPR sink and source controller. Negotiates up to 48 V / 5 A. Dead-battery Rd is internal. The 48 V power path is NOT the internal 5 V switch.",
    )
    stub_label(sch, pd["CC1"], "USBC_CC1", "left")
    stub_label(sch, pd["CC2"], "USBC_CC2", "left")
    stub_label(sch, pd["VBUS_SENSE"], "VBUS_SENSE", "up")
    stub_power(sch, pd["VIN"], "P3V3_ALWAYS", "up")
    stub_gnd(sch, pd["GND"])
    stub_label(sch, pd["I2C_SDA"], "PD_SDA", "right", "global")
    stub_label(sch, pd["I2C_SCL"], "PD_SCL", "right", "global")
    stub_label(sch, pd["FAULT"], "PD_FAULT", "right", "global")

    prot = place_ic(
        sch, sch.seq("U"), "TPD4S480", 40, 200,
        left=[("VBUS_IN", "power_in"), ("CC1", "passive"), ("CC2", "passive")],
        right=[("VBUS_OUT", "power_out"), ("GATE", "output")],
        bottom=[("GND", "power_in")],
        top=[],
        mfr="Texas Instruments",
        mpn="TPD4S480",
        datasheet="https://www.ti.com/product/TPD4S480",
        desc="48 V EPR protection and CC short-to-VBUS. Gate drive for the external sink FET. Follow TI TIDT407; do not connect raw 48 V to the TPS26750 VBUS pin.",
    )
    stub_label(sch, prot["VBUS_IN"], "VBUS_CONNECTOR", "left")
    stub_label(sch, prot["CC1"], "USBC_CC1", "left")
    stub_label(sch, prot["CC2"], "USBC_CC2", "left")
    stub_label(sch, prot["VBUS_OUT"], "VBUS_SENSE", "right")
    stub_label(sch, prot["GATE"], "SINK_GATE", "right")
    stub_gnd(sch, prot["GND"])

    fet = place_ic(
        sch, sch.seq("Q"), "BSC040N10", 250, 200,
        left=[("G", "input")],
        right=[("D", "passive"), ("S", "passive")],
        bottom=[], top=[],
        mfr="Infineon",
        mpn="BSC040N10NS5",
        desc="100 V sink MOSFET in the EPR path. Gate network, back-to-back arrangement and inrush are the TIDT407 circuit.",
    )
    stub_label(sch, fet["G"], "SINK_GATE", "left")
    stub_label(sch, fet["D"], "VBUS_CONNECTOR", "right")
    stub_label(sch, fet["S"], "P48V_USB", "right", "global")

    qsfp = place_ic(
        sch, sch.seq("J"), "QSFP_DD", 360, 80,
        left=[("TX_P0", "input"), ("RX_P0", "output")] + [(f"MODSEL", "input")],
        right=[],
        top=[("VCC", "power_in")],
        bottom=[("GND", "power_in"), ("INT", "output"), ("RESET", "input")],
        mfr="Amphenol",
        mpn="QSFP-DD cage and connector, 400G",
        desc="400GbE. Four 112 Gbit/s PAM4 lanes each way, driven by Versal GTM. Heatsink is part of the cage. ModPrsL, IntL, ResetL per SFF-8636 / CMIS.",
    )
    stub_label(sch, qsfp["TX_P0"], "QSFP_TX_P0", "left", "global")
    stub_label(sch, qsfp["RX_P0"], "QSFP_RX_P0", "left", "global")
    stub_label(sch, qsfp["MODSEL"], "QSFP_MODSEL", "left", "global")
    stub_power(sch, qsfp["VCC"], "P3V3", "up")
    stub_gnd(sch, qsfp["GND"])
    stub_label(sch, qsfp["INT"], "QSFP_INT", "down", "global")
    stub_label(sch, qsfp["RESET"], "QSFP_RESET", "down", "global")
    qsfp2 = place_ic(
        sch, sch.seq("J"), "QSFP_DD", 360, 140,
        left=[("TX_P0", "input"), ("RX_P0", "output"), ("MODSEL", "input")],
        right=[],
        top=[("VCC", "power_in")],
        bottom=[("GND", "power_in"), ("INT", "output"), ("RESET", "input")],
        mfr="Amphenol",
        mpn="QSFP-DD cage and connector, 400G, second port",
        desc="Second 400GbE port. Both channels at 10 GHz IBW do not fit in one 400G link.",
    )
    stub_label(sch, qsfp2["TX_P0"], "QSFP2_TX_P0", "left", "global")
    stub_label(sch, qsfp2["RX_P0"], "QSFP2_RX_P0", "left", "global")
    stub_label(sch, qsfp2["MODSEL"], "QSFP2_MODSEL", "left", "global")
    stub_power(sch, qsfp2["VCC"], "P3V3", "up")
    stub_gnd(sch, qsfp2["GND"])
    stub_label(sch, qsfp2["INT"], "QSFP2_INT", "down", "global")
    stub_label(sch, qsfp2["RESET"], "QSFP2_RESET", "down", "global")
    note(
        sch,
        "Lanes QSFP_TX_P1..3, QSFP_TX_N0..3, QSFP_RX_P1..3, QSFP_RX_N0..3 and the same names with a QSFP2_ prefix are global nets. "
        "A retimer footprint (Broadcom 400G class) is placed and left unstuffed unless the channel simulation misses the eye. "
        "Short route, Megtron 8 stripline, backdrill, no nickel on these pairs (EPIG).",
        20, 250, 1.27,
    )


def build_power(sch: Sch) -> None:
    note(
        sch,
        "Praline is a 5 V, sub-5 W USB board with a TPS62410 and 100 mA XC6206 LDOs. That budget cannot feed an OCXO, a 15 V PA, a 20 GSPS converter or a Versal. "
        "Input is USB-PD EPR 48 V at 5 A (240 W) OR a locking 48 V barrel. Typical draw is budgeted at 150 W, peak 200 W. "
        "Silent Switcher modules for the big rails, LT3045 only where the current is under 500 mA and the noise matters (clock, PLL, converter clock domain).",
        20, 16, 1.35,
    )
    rails = [
        ("U1", "LT8672", "Ideal-diode OR of P48V_USB and the barrel", "Analog Devices", "LT8672",
         [("INA", "power_in"), ("INB", "power_in")], [("OUT", "power_out")], "P48V"),
        ("U2", "LTM4700", "FPGA VCCINT, 100 A class module, 0.80 V", "Analog Devices", "LTM4700",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P0V80_VCCINT"),
        ("U3", "LTM4657", "GTM rail 0.88 V", "Analog Devices", "LTM4657",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P0V88_GTM"),
        ("U4", "LTM4658", "AFE 1.0 V bulk, then ferrites per domain", "Analog Devices", "LTM4658",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P1V0_BULK"),
        ("U5", "LT3045", "AD9084 clock domain, from the 1.0 V bulk", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P1V0_CK"),
        ("U6", "LTM8074", "1.8 V", "Analog Devices", "LTM8074",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P1V8"),
        ("U7", "LTM8074", "3.3 V", "Analog Devices", "LTM8074",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P3V3"),
        ("U8", "LTM8074", "5 V", "Analog Devices", "LTM8074",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P5V0"),
        ("U9", "LT8642S", "12 V OCXO, Silent Switcher", "Analog Devices", "LT8642S",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P12V_OCXO"),
        ("U10", "LT8642S", "15 V PA bulk, into HMC980 only", "Analog Devices", "LT8642S",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P15V_PA"),
        ("U11", "ADP5070", "Inverting pre-regulator for the RF switches", "Analog Devices", "ADP5070",
         [("VIN", "power_in")], [("VNEG", "power_out")], "N5V_RAW"),
        ("U12", "LT3094", "-3.3 V ultralow noise, 500 mA", "Analog Devices", "LT3094",
         [("VIN", "power_in")], [("VOUT", "power_out")], "N3V3_RF"),
        ("U13", "LT3045", "3.3 V clock", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P3V3_CLK"),
        ("U14", "LT3045", "5 V PLL", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P5V_PLL"),
        ("U15", "LT3045", "3.3 V PLL", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P3V3_PLL"),
        ("U16", "LT3045", "2.5 V LMX1214", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P2V5_CLK"),
        ("U17", "LT3045", "1.5 V Versal aux, if the current fits, else an LTM", "Analog Devices", "LT3045",
         [("VIN", "power_in")], [("VOUT", "power_out")], "P1V5_AUX"),
    ]
    y = 40
    for _ref, value, desc, mfr, mpn, left, right, rail in rails:
        pins = place_ic(
            sch, sch.seq("U"), value, 80 if y < 280 else 280, 40 + ((y - 40) % 240),
            left=left, right=right, bottom=[("GND", "power_in"), ("EN", "input")], top=[],
            mfr=mfr, mpn=mpn, desc=desc,
            datasheet=f"https://www.analog.com/en/products/{mpn.lower()}.html",
        )
        for pname, _ in left:
            src = "P48V" if value != "LT8672" else ("P48V_USB" if pname == "INA" else "P48V_BARREL")
            if value == "LT3045" and rail == "P1V0_CK":
                src = "P1V0_BULK"
            elif value == "LT3094":
                src = "N5V_RAW"
            elif value == "LT8672":
                src = "P48V_USB" if pname == "INA" else "P48V_BARREL"
            else:
                src = "P48V" if rail not in ("P3V3_CLK", "P5V_PLL", "P3V3_PLL", "P2V5_CLK") else "P5V0"
            if value == "LT3045" and rail == "P1V5_AUX":
                src = "P3V3"
            stub_label(sch, pins[pname], src, "left", "global")
        for pname, _ in right:
            stub_label(sch, pins[pname], rail, "right", "global")
            place_flag(sch, pins[pname][0] + 20, pins[pname][1] - 6, rail)
        stub_gnd(sch, pins["GND"])
        stub_label(sch, pins["EN"], f"EN_{rail}", "down", "global")
        y += 28

    barrel = place_ic(
        sch, sch.seq("J"), "BARREL_48V", 20, 300,
        right=[("VIN", "power_out")], bottom=[("GND", "power_in")], left=[],
        mfr="Switchcraft",
        mpn="locking 48 V barrel, center positive",
        desc="Alternate input so the instrument runs without a 240 W PD source. OR-ed by the LT8672.",
    )
    stub_label(sch, barrel["VIN"], "P48V_BARREL", "right", "global")
    stub_gnd(sch, barrel["GND"])

    note(
        sch,
        "Ferrite splits of P1V0_BULK: P1V0_ADC, P1V0_ADCBK, P1V0_DAC, P1V0_DACDIG. "
        "P5V0_RF and P3V3_RF are ferrite-isolated from P5V0 and P3V3. "
        "P3V3_ALWAYS is a small LDO off the TPS26750 dead-battery path so the PD controller boots before 48 V exists. "
        "EN_* nets are ADM1266 outputs. Nothing self-starts except the PD controller.",
        20, 360, 1.27,
    )
    # ferrite symbols as two-pins for the domain splits
    splits = [
        ("P1V0_BULK", "P1V0_ADC"),
        ("P1V0_BULK", "P1V0_ADCBK"),
        ("P1V0_BULK", "P1V0_DAC"),
        ("P1V0_BULK", "P1V0_DACDIG"),
        ("P5V0", "P5V0_RF"),
        ("P3V3", "P3V3_RF"),
        ("P1V8", "P1V8_AFE"),
    ]
    for i, (a, b) in enumerate(splits):
        two_pin(
            sch, "FB", "ferrite", 420, 40 + i * 10, a, b,
            kind_a="global", kind_b="global",
            desc=f"Domain split {a} to {b}. Current rating sized to the downstream datasheet, not a 0603 signal bead.",
            mfr="TDK", mpn="current-rated, impedance at the switching frequency specified in the power note",
        )
        place_flag(sch, 470, 34 + i * 10, b)


def build_supervisor(sch: Sch) -> None:
    note(
        sch,
        "ADM1266 sequences every rail in the order the Versal and the AD9084 demand, logs faults, and is the only device allowed to release EN_* . "
        "The TX key is a physical break in TX_ARM, pulled down on the far side. "
        "LEDs report power, link and an actually-armed PA. They are single color, same lesson as Praline: the color is not the meaning.",
        20, 18, 1.4,
    )
    seq = place_ic(
        sch, sch.seq("U"), "ADM1266", 80, 80,
        left=[("VX1", "input"), ("VX2", "input"), ("VX3", "input"), ("VX4", "input")],
        right=[("PDO1", "output"), ("PDO2", "output"), ("FAULT", "output")],
        top=[("VCC", "power_in")],
        bottom=[("GND", "power_in"), ("SDA", "bidirectional"), ("SCL", "input")],
        mfr="Analog Devices",
        mpn="ADM1266",
        datasheet="https://www.analog.com/en/products/adm1266.html",
        desc="Super sequencer with EEPROM fault log. The state machine is transcribed from the Versal power diagram and UG-2300, then verified on the bench before the PA fuse is fitted.",
    )
    stub_power(sch, seq["VCC"], "P3V3_ALWAYS", "up")
    stub_gnd(sch, seq["GND"])
    stub_label(sch, seq["SDA"], "SEQ_SDA", "down", "global")
    stub_label(sch, seq["SCL"], "SEQ_SCL", "down", "global")
    for i, net in enumerate(("P48V", "P3V3", "P0V80_VCCINT", "P1V0_BULK")):
        stub_label(sch, seq[f"VX{i+1}"], f"MON_{net}", "left", "global")
    stub_label(sch, seq["PDO1"], "EN_P0V80_VCCINT", "right", "global")
    stub_label(sch, seq["PDO2"], "EN_P1V0_BULK", "right", "global")
    stub_label(sch, seq["FAULT"], "SEQ_FAULT", "right", "global")

    key = place_ic(
        sch, sch.seq("SW"), "KEY_TX", 220, 70,
        left=[("A", "passive")], right=[("B", "passive")], top=[], bottom=[],
        mfr="C&K",
        mpn="key-operated switch, break-before-make",
        desc="Physical transmit arm. Open leaves TX_ARM pulled down. There is no software path around this switch.",
    )
    stub_label(sch, key["A"], "TX_ARM_SRC", "left")
    stub_label(sch, key["B"], "TX_ARM", "right", "hier")

    src = place_ic(
        sch, sch.seq("U"), "TX_ARM_LDO", 220, 110,
        left=[("VIN", "power_in")], right=[("VOUT", "power_out")], bottom=[("GND", "power_in")], top=[],
        mfr="Analog Devices", mpn="LT3045",
        desc="Tiny always-defined source for the arm line, current-limited by a series 10 k so a shorted key cannot drag the rail down.",
    )
    stub_power(sch, src["VIN"], "P3V3_ALWAYS", "left")
    stub_label(sch, src["VOUT"], "TX_ARM_SRC", "right")
    stub_gnd(sch, src["GND"])

    ina = place_ic(
        sch, sch.seq("U"), "INA228", 220, 160,
        left=[("INP", "input"), ("INN", "input")],
        right=[("ALERT", "output"), ("SDA", "bidirectional"), ("SCL", "input")],
        top=[("VCC", "power_in")], bottom=[("GND", "power_in")],
        mfr="Texas Instruments", mpn="INA228",
        datasheet="https://www.ti.com/product/INA228",
        desc="85 V, 20-bit power monitor on the 48 V input and, with a second device, on each PA drain.",
    )
    stub_label(sch, ina["INP"], "P48V", "left", "global")
    stub_label(sch, ina["INN"], "P48V_LOAD", "left", "global")
    stub_label(sch, ina["ALERT"], "INA_ALERT", "right", "global")
    stub_label(sch, ina["SDA"], "SEQ_SDA", "right", "global")
    stub_label(sch, ina["SCL"], "SEQ_SCL", "right", "global")
    stub_power(sch, ina["VCC"], "P3V3", "up")
    stub_gnd(sch, ina["GND"])

    note(
        sch,
        "LEDs, each one color, series resistor sized for 2 mA: PWR from P3V3-good, AFE from AD9084 IRQ-not, FPGA from done, USB from FX20, LINK from QSFP ModPrsL and link-up, TX only when PA_EN_A or PA_EN_B is high, FAULT from SEQ_FAULT. "
        "TX lit means the drain switch is armed, not merely that software set a bit.",
        20, 210, 1.27,
    )
    for i, (name, net) in enumerate((
        ("PWR", "MON_P3V3"),
        ("AFE", "AFE_IRQ"),
        ("FPGA", "FPGA_DONE"),
        ("USB", "USB_ENUM"),
        ("LINK", "QSFP_INT"),
        ("TX", "PA_EN_A"),
        ("FAULT", "SEQ_FAULT"),
    )):
        two_pin(sch, "D", name, 40 + i * 30, 240, net, "GND",
                kind_a="global",
                desc=f"LED {name}", mfr="Lite-On", mpn="single color, 0603")


def build_root(sch: Sch, sheets: list[dict]) -> None:
    note(
        sch,
        "HackRF Ultra 0.1 architecture. Hierarchical pins carry the analog, clock and arming nets. "
        "JESD lanes, LVDS, SPI chip-selects and power enables are global labels of the form shown on the child sheets. "
        "This is not a fabrication package.",
        20, 12, 1.8,
    )
    # Place sheets. Pin coordinates are absolute.
    for sh in sheets:
        x, y, w, h = sh["x"], sh["y"], sh["w"], sh["h"]
        pin_txt = []
        left = [p for p in sh["pins"] if p[2] == "left"]
        right = [p for p in sh["pins"] if p[2] == "right"]
        for i, (name, etype, side) in enumerate(left):
            py = y + 8 + i * 5.08
            pin_txt.append(
                f'\t\t(pin "{esc(name)}" {etype}\n'
                f'\t\t\t(at {x:.2f} {py:.2f} 180)\n'
                f'\t\t\t(uuid "{uid(sh["file"]+name)}")\n'
                '\t\t\t(effects (font (size 1.27 1.27)) (justify left))\n'
                '\t\t)'
            )
            sh.setdefault("pin_xy", {})[name] = (x, py)
        for i, (name, etype, side) in enumerate(right):
            py = y + 8 + i * 5.08
            pin_txt.append(
                f'\t\t(pin "{esc(name)}" {etype}\n'
                f'\t\t\t(at {x+w:.2f} {py:.2f} 0)\n'
                f'\t\t\t(uuid "{uid(sh["file"]+name+"R")}")\n'
                '\t\t\t(effects (font (size 1.27 1.27)) (justify right))\n'
                '\t\t)'
            )
            sh.setdefault("pin_xy", {})[name] = (x + w, py)
        sch.items.append(
            "\t(sheet\n"
            f"\t\t(at {x:.2f} {y:.2f})\n"
            f"\t\t(size {w:.2f} {h:.2f})\n"
            "\t\t(exclude_from_sim no)\n"
            "\t\t(in_bom yes)\n"
            "\t\t(on_board yes)\n"
            "\t\t(dnp no)\n"
            "\t\t(fields_autoplaced yes)\n"
            "\t\t(stroke (width 0.1524) (type solid))\n"
            "\t\t(fill (color 0 0 0 0.0000))\n"
            f'\t\t(uuid "{sh["uuid"]}")\n'
            + prop("Sheetname", sh["name"], x, y - 1.2).replace("\t\t(property", "\t\t(property", 1)
            + "\n"
            + prop("Sheetfile", sh["file"], x, y + h + 1.2)
            + "\n"
            + "\n".join(pin_txt)
            + "\n"
            + "\t\t(instances\n"
            + f'\t\t\t(project "{PROJECT}"\n'
            + f'\t\t\t\t(path "/{ROOT_UUID}"\n'
            + '\t\t\t\t\t(page "2")\n'
            + "\t\t\t\t)\n"
            + "\t\t\t)\n"
            + "\t\t)\n"
            + "\t)"
        )
    # Connect matching pin names with wires when both exist.
    index: dict[str, list] = {}
    for sh in sheets:
        for name, xy in sh.get("pin_xy", {}).items():
            index.setdefault(name, []).append(xy)
    for name, points in index.items():
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            wire(sch, x1, y1, x2, y2)
    note(
        sch,
        "Power rails are global power symbols, drawn on the power sheet with a PWR_FLAG at each regulator. "
        "They are not sheet pins.",
        20, 520, 1.27,
    )


def build_pcb() -> str:
    # 14 copper layers. KiCad legacy ids: F=0, B=2, In1=4, In2=6, ...
    layers = [(0, "F.Cu", "signal"), (2, "B.Cu", "signal")]
    for i in range(1, 13):
        kind = "power" if i in (4, 5, 6, 10) else "signal"
        if i in (1, 2, 4, 8, 9, 12):
            kind = "power" if i != 1 else "power"
        # L2, L4, L8, L9, L12 are grounds or power. Mark inner reference planes as power.
        if i in (1, 4, 8, 9, 11):
            kind = "power"
        else:
            kind = "signal"
        layers.append((2 + 2 * i, f"In{i}.Cu", kind))
    # fix: id formula. In1 should be 4 = 2+2*1. Yes 2+2*i.
    user_layers = [
        (1, "F.Mask", "user"),
        (3, "B.Mask", "user"),
        (5, "F.SilkS", "user", "F.Silkscreen"),
        (7, "B.SilkS", "user", "B.Silkscreen"),
        (13, "F.Paste", "user"),
        (15, "B.Paste", "user"),
        (19, "Cmts.User", "user", "User.Comments"),
        (25, "Edge.Cuts", "user"),
        (27, "Margin", "user"),
        (31, "F.CrtYd", "user", "F.Courtyard"),
        (29, "B.CrtYd", "user", "B.Courtyard"),
        (35, "F.Fab", "user"),
        (33, "B.Fab", "user"),
    ]
    layer_txt = []
    for item in layers:
        layer_txt.append(f'\t\t({item[0]} "{item[1]}" {item[2]})')
    for item in user_layers:
        if len(item) == 4:
            layer_txt.append(f'\t\t({item[0]} "{item[1]}" {item[2]} "{item[3]}")')
        else:
            layer_txt.append(f'\t\t({item[0]} "{item[1]}" {item[2]})')

    def cu(name, t):
        return (
            f'\t\t\t(layer "{name}"\n'
            f'\t\t\t\t(type "copper")\n'
            f'\t\t\t\t(thickness {t})\n'
            f'\t\t\t)'
        )

    def diel(n, thick, mat, er, df):
        return (
            f'\t\t\t(layer "dielectric {n}"\n'
            f'\t\t\t\t(type "core")\n'
            f'\t\t\t\t(thickness {thick})\n'
            f'\t\t\t\t(material "{mat}")\n'
            f'\t\t\t\t(epsilon_r {er})\n'
            f'\t\t\t\t(loss_tangent {df})\n'
            f'\t\t\t)'
        )

    # Physical order top to bottom. 0.5 oz = 0.017 mm HVLP.
    cu_t = 0.017
    names = ["F.Cu"] + [f"In{i}.Cu" for i in range(1, 13)] + ["B.Cu"]
    # dielectrics between the 14 coppers: 13 dielectrics
    # 1 RO3003 0.127, then alternating Megtron prepreg 0.10 and core 0.20, last adjusted.
    diels = [("RO3003", 0.127, 3.00, 0.0010)]
    for i in range(12):
        if i % 2 == 0:
            diels.append(("Megtron 8 prepreg", 0.100, 3.10, 0.0014))
        else:
            diels.append(("Megtron 8 core", 0.200, 3.10, 0.0014))
    stack_parts = []
    stack_parts.append(
        '\t\t\t(layer "F.SilkS" (type "Top Silk Screen") (color "White"))\n'
        '\t\t\t(layer "F.Paste" (type "Top Solder Paste"))\n'
        '\t\t\t(layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.015) (material "LPI"))'
    )
    for i, name in enumerate(names):
        stack_parts.append(cu(name, cu_t))
        if i < len(diels):
            mat, th, er, df = diels[i]
            kind = "core"
            stack_parts.append(
                f'\t\t\t(layer "dielectric {i+1}"\n'
                f'\t\t\t\t(type "{kind}")\n'
                f'\t\t\t\t(thickness {th})\n'
                f'\t\t\t\t(material "{mat}")\n'
                f'\t\t\t\t(epsilon_r {er})\n'
                f'\t\t\t\t(loss_tangent {df})\n'
                f'\t\t\t)'
            )
    stack_parts.append(
        '\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.015) (material "LPI"))\n'
        '\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))\n'
        '\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))\n'
        '\t\t\t(copper_finish "EPIG")\n'
        '\t\t\t(dielectric_constraints yes)'
    )

    def gr_line(x1, y1, x2, y2, layer, width=0.15):
        return (
            "\t(gr_line\n"
            f"\t\t(start {x1} {y1}) (end {x2} {y2})\n"
            f"\t\t(stroke (width {width}) (type solid))\n"
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid(f"gr{x1}{y1}{x2}{y2}{layer}")}")\n'
            "\t)"
        )

    def rect(x1, y1, x2, y2, layer, width=0.15):
        return "\n".join([
            gr_line(x1, y1, x2, y1, layer, width),
            gr_line(x2, y1, x2, y2, layer, width),
            gr_line(x2, y2, x1, y2, layer, width),
            gr_line(x1, y2, x1, y1, layer, width),
        ])

    def text(s, x, y, layer="Cmts.User", size=1.5):
        return (
            f'\t(gr_text "{esc(s)}"\n'
            f"\t\t(at {x} {y} 0)\n"
            f'\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid("gt"+s+str(x)+str(y))}")\n'
            "\t\t(effects (font (size {s} {s}) (thickness 0.15)))\n".format(s=size)
            + "\t)"
        )

    graphics = []
    # Outline 280 x 190, origin 0,0. 1 mm corner is omitted; square is fine for the carrier.
    graphics.append(rect(0, 0, 280, 190, "Edge.Cuts", 0.1))
    graphics.append(text("HACKRF ULTRA  0.1.0-arch   NICHT FERTIGEN", 20, 8, "F.SilkS", 2.0))
    graphics.append(text("14L  RO3003 + Megtron 8  EPIG  VIPPO  backdrill  IPC-6018 class 3", 20, 14, "F.SilkS", 1.2))
    # Zones
    zones = [
        (8, 20, 70, 100, "RX A  cavity"),
        (8, 105, 70, 180, "TX A  cavity"),
        (210, 20, 272, 100, "RX B  cavity"),
        (210, 105, 272, 180, "TX B  cavity"),
        (78, 125, 145, 182, "Clock cavity  OCXO LMK ADF LMX"),
        (100, 40, 175, 115, "AD9084 + Versal  top side"),
        (180, 150, 250, 182, "2x QSFP-DD"),
        (80, 20, 180, 38, "Regulators, bottom preferred"),
    ]
    for x1, y1, x2, y2, label_s in zones:
        graphics.append(rect(x1, y1, x2, y2, "Cmts.User", 0.2))
        graphics.append(text(label_s, x1 + 2, y1 + 4, "Cmts.User", 1.2))

    def hole(x, y):
        return (
            '\t(footprint "ultra:MountingHole_M3"\n'
            '\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{uid(f"mh{x}{y}")}")\n'
            f'\t\t(at {x} {y})\n'
            + prop("Reference", "H", x, y).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Value", "M3", x, y, True).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Footprint", "ultra:MountingHole_M3", 0, 0, True).replace("\t\t(", "\t\t\t(")
            + "\n"
            + '\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
            + f'\t\t(pad "" np_thru_hole circle (at 0 0) (size 3.2 3.2) (drill 3.2) (layers "*.Cu" "*.Mask") (uuid "{uid("pad"+str(x)+str(y))}"))\n'
            + '\t\t(fp_circle (center 0 0) (end 4.5 0) (stroke (width 0.15) (type default)) (fill none) (layer "Cmts.User"))\n'
            + "\t)"
        )

    holes = [(6, 6), (274, 6), (6, 184), (274, 184), (140, 6), (140, 184)]
    # Package courtyards, no copper lands.
    def courtyard(ref, x, y, w, h, label_s):
        return (
            f'\t(footprint "ultra:Courtyard_{ref}"\n'
            '\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{uid("cy"+ref)}")\n'
            f'\t\t(at {x} {y})\n'
            + prop("Reference", ref, 0, -h / 2 - 2).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Value", label_s, 0, 0, False).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Footprint", "", 0, 0, True).replace("\t\t(", "\t\t\t(")
            + "\n"
            + '\t\t(attr exclude_from_pos_files exclude_from_bom)\n'
            + f'\t\t(fp_rect (start {-w/2:.2f} {-h/2:.2f}) (end {w/2:.2f} {h/2:.2f})\n'
            + '\t\t\t(stroke (width 0.15) (type default)) (fill none) (layer "F.Fab"))\n'
            + f'\t\t(fp_text user "{esc(label_s)}" (at 0 0 0) (layer "F.Fab")\n'
            + '\t\t\t(effects (font (size 1.0 1.0) (thickness 0.15)))\n'
            + f'\t\t\t(uuid "{uid("ft"+ref)}"))\n'
            + "\t)"
        )

    courtyards = [
        ("U_AFE", 140, 80, 26, 24, "AD9084 24x26 outline only"),
        ("U_FPGA", 145, 70, 50, 50, "XCVP1202 outline only"),
        ("U_OCXO", 100, 155, 25, 25, "OCXO"),
    ]
    # The FPGA and AFE overlap if both at those coords. Place them apart.
    courtyards = [
        ("U_AFE", 120, 78, 26, 24, "AD9084 outline, no lands"),
        ("U_FPGA", 175, 78, 50, 50, "XCVP1802 outline, no lands"),
        ("U_OCXO", 105, 155, 26, 22, "100 MHz OCXO"),
    ]

    fid = []
    for i, (x, y) in enumerate(((12, 16), (268, 16), (12, 174))):
        fid.append(
            f'\t(footprint "ultra:Fiducial"\n'
            f'\t\t(layer "F.Cu")\n'
            f'\t\t(uuid "{uid("fid"+str(i))}")\n'
            f'\t\t(at {x} {y})\n'
            + prop("Reference", f"FID{i}", x, y - 2).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Value", "Fiducial", 0, 0, True).replace("\t\t(", "\t\t\t(")
            + "\n"
            + prop("Footprint", "", 0, 0, True).replace("\t\t(", "\t\t\t(")
            + "\n"
            + '\t\t(attr exclude_from_bom)\n'
            + f'\t\t(pad "1" smd circle (at 0 0) (size 1 1) (layers "F.Cu" "F.Mask") (solder_mask_margin 0.5) (uuid "{uid("fidp"+str(i))}"))\n'
            + "\t)"
        )

    body = "\n".join(graphics + [hole(x, y) for x, y in holes] + [courtyard(*c) for c in courtyards] + fid)
    return (
        "(kicad_pcb\n"
        "\t(version 20241229)\n"
        '\t(generator "pcbnew")\n'
        '\t(generator_version "9.0")\n'
        "\t(general (thickness 2.2) (legacy_teardrops no))\n"
        '\t(paper "A3")\n'
        "\t(title_block\n"
        '\t\t(title "${TITLE}")\n'
        '\t\t(date "${DATE}")\n'
        '\t\t(rev "${VERSION}")\n'
        '\t\t(company "${COPYRIGHT}")\n'
        '\t\t(comment 1 "Architecture carrier. No copper pours, no BGA lands, do not fabricate.")\n'
        "\t)\n"
        "\t(layers\n"
        + "\n".join(layer_txt)
        + "\n\t)\n"
        "\t(setup\n"
        "\t\t(stackup\n"
        + "\n".join(stack_parts)
        + "\n\t\t)\n"
        "\t\t(pad_to_mask_clearance 0.05)\n"
        "\t\t(allow_blind_buried_vias yes)\n"
        "\t\t(allow_microvias yes)\n"
        "\t\t(tenting front back)\n"
        "\t)\n"
        + body
        + "\n)\n"
    )


def build_pro(sheet_meta: list[dict]) -> None:
    data = json.loads(PRO_TEMPLATE.read_text())
    data["board"]["design_settings"]["rules"]["min_clearance"] = 0.075
    data["board"]["design_settings"]["rules"]["min_track_width"] = 0.075
    data["board"]["design_settings"]["rules"]["min_via_diameter"] = 0.30
    data["board"]["design_settings"]["rules"]["min_via_drill"] = 0.15
    data["board"]["design_settings"]["rules"]["min_microvia_diameter"] = 0.15
    data["board"]["design_settings"]["rules"]["min_microvia_drill"] = 0.075
    data["board"]["design_settings"]["rules"]["min_hole_clearance"] = 0.15
    data["board"]["design_settings"]["rules"]["min_copper_edge_clearance"] = 0.30
    data["board"]["design_settings"]["drc_exclusions"] = []
    data["board"]["design_settings"]["track_widths"] = [0.075, 0.10, 0.12, 0.15, 0.20, 0.26, 0.40, 0.60, 1.00]
    data["text_variables"] = {
        "COPYRIGHT": "Copyright 2026 HackRF Ultra contributors",
        "DATE": "2026-11-15",
        "LICENSE": "CERN-OHL-P v2. Analysis of HackRF Pro remains copyright Great Scott Gadgets.",
        "TITLE": "HackRF Ultra",
        "VERSION": "0.1.0-arch",
    }
    data["sheets"] = [[ROOT_UUID, "Root"]] + [[s["uuid"], s["name"]] for s in sheet_meta]
    classes = [
        {
            "name": "Default",
            "clearance": 0.075,
            "track_width": 0.10,
            "via_diameter": 0.40,
            "via_drill": 0.15,
            "diff_pair_width": 0.12,
            "diff_pair_gap": 0.15,
            "diff_pair_via_gap": 0.25,
            "microvia_diameter": 0.15,
            "microvia_drill": 0.075,
            "wire_width": 6,
            "bus_width": 12,
            "line_style": 0,
            "priority": 2147483647,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        },
        {
            "name": "RF_50",
            "clearance": 0.25,
            "track_width": 0.26,
            "via_diameter": 0.40,
            "via_drill": 0.15,
            "diff_pair_width": 0.20,
            "diff_pair_gap": 0.15,
            "diff_pair_via_gap": 0.30,
            "microvia_diameter": 0.15,
            "microvia_drill": 0.075,
            "priority": 1,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        },
        {
            "name": "JESD_100",
            "clearance": 0.20,
            "track_width": 0.12,
            "via_diameter": 0.40,
            "via_drill": 0.15,
            "diff_pair_width": 0.12,
            "diff_pair_gap": 0.15,
            "diff_pair_via_gap": 0.30,
            "microvia_diameter": 0.15,
            "microvia_drill": 0.075,
            "priority": 2,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        },
        {
            "name": "GT_112",
            "clearance": 0.22,
            "track_width": 0.10,
            "via_diameter": 0.40,
            "via_drill": 0.15,
            "diff_pair_width": 0.10,
            "diff_pair_gap": 0.14,
            "diff_pair_via_gap": 0.35,
            "microvia_diameter": 0.15,
            "microvia_drill": 0.075,
            "priority": 3,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        },
        {
            "name": "USB_90",
            "clearance": 0.15,
            "track_width": 0.10,
            "via_diameter": 0.40,
            "via_drill": 0.15,
            "diff_pair_width": 0.11,
            "diff_pair_gap": 0.14,
            "diff_pair_via_gap": 0.25,
            "microvia_diameter": 0.15,
            "microvia_drill": 0.075,
            "priority": 4,
            "pcb_color": "rgba(0, 0, 0, 0.000)",
            "schematic_color": "rgba(0, 0, 0, 0.000)",
        },
    ]
    data["net_settings"]["classes"] = classes
    data["net_settings"]["netclass_patterns"] = [
        {"netclass": "RF_50", "pattern": "RX*"},
        {"netclass": "RF_50", "pattern": "TX*"},
        {"netclass": "JESD_100", "pattern": "JESD_*"},
        {"netclass": "GT_112", "pattern": "QSFP*"},
        {"netclass": "USB_90", "pattern": "USBC_TX*"},
        {"netclass": "USB_90", "pattern": "USBC_RX*"},
        {"netclass": "USB_90", "pattern": "LVDS_*"},
    ]
    data["meta"]["filename"] = "hackrf-ultra.kicad_pro"
    (ROOT / "hackrf-ultra.kicad_pro").write_text(json.dumps(data, indent=2) + "\n")


def check(sch: Sch, expected_hier: set[str]) -> None:
    missing = expected_hier - sch.hier
    if missing:
        raise SystemExit(f"{sch.stem} missing hierarchical labels: {sorted(missing)}")
    text = sch.emit()
    if text.count("(") != text.count(")"):
        raise SystemExit(f"{sch.stem} paren mismatch {text.count('(')} vs {text.count(')')}")


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    specs = [
        ("rf_frontend", "RF", build_rf, "A0",
         [(n, "bidirectional", "right") for n in ANALOG]
         + [(n, "input", "left") for n in ("TXA_EN", "TXB_EN", "TX_ARM")]
         + [(n, "output", "right") for n in ("TXA_FAULT", "TXB_FAULT")]),
        ("converter", "Converter", build_converter, "A1",
         [(n, "bidirectional", "left") for n in ANALOG]
         + [(n, "input", "left") for n in CLOCKS]
         + [("AFE_RESET", "input", "right")]),
        ("clock", "Clock", build_clock, "A2",
         [(n, "output", "right") for n in CLOCKS]),
        ("fpga", "FPGA", build_fpga, "A1",
         [("SYSREF_P", "input", "left"), ("SYSREF_N", "input", "left"),
          ("AFE_RESET", "output", "left"),
          ("TXA_EN", "output", "right"), ("TXB_EN", "output", "right"),
          ("TX_ARM", "input", "right")]),
        ("host", "Host", build_host, "A2", []),
        ("power", "Power", build_power, "A1", []),
        ("supervisor", "Supervisor", build_supervisor, "A3",
         [("TX_ARM", "output", "right")]),
    ]
    # Sheet placement on the root. Heights must fit the pin counts.
    positions = {
        "rf_frontend": (15, 25, 160, 200),
        "converter": (200, 25, 150, 160),
        "clock": (370, 25, 140, 80),
        "fpga": (200, 210, 170, 120),
        "host": (390, 210, 150, 80),
        "power": (15, 250, 160, 80),
        "supervisor": (15, 350, 160, 50),
    }
    sheet_meta = []
    for stem, name, builder, paper, pins in specs:
        file_uuid = str(uuid.uuid5(NS, "sheet-" + stem))
        sch = Sch(stem, file_uuid, paper)
        sch.sheet_uuid = file_uuid
        builder(sch)
        expected = {p[0] for p in pins}
        check(sch, expected)
        (ROOT / f"{stem}.kicad_sch").write_text(sch.emit())
        x, y, w, h = positions[stem]
        # Grow sheet height so pins fit.
        need = 10 + max(
            sum(1 for p in pins if p[2] == "left"),
            sum(1 for p in pins if p[2] == "right"),
            1,
        ) * 5.08
        h = max(h, need)
        sheet_meta.append({
            "name": name,
            "file": f"{stem}.kicad_sch",
            "uuid": file_uuid,
            "x": x, "y": y, "w": w, "h": h,
            "pins": pins,
        })

    root = Sch("hackrf-ultra", ROOT_UUID, "A1")
    build_root(root, sheet_meta)
    text = root.emit()
    if text.count("(") != text.count(")"):
        raise SystemExit("root paren mismatch")
    (ROOT / "hackrf-ultra.kicad_sch").write_text(text)
    pcb = build_pcb()
    if pcb.count("(") != pcb.count(")"):
        raise SystemExit(f"pcb paren mismatch {pcb.count('(')} {pcb.count(')')}")
    (ROOT / "hackrf-ultra.kicad_pcb").write_text(pcb)
    build_pro(sheet_meta)

    # BOM
    lines = ["Reference,Value,Manufacturer,Part,Description,Datasheet,Sheet"]
    seen = set()
    for row in BOM:
        key = (row["Reference"], row["Sheet"], row["Value"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(",".join('"' + str(row[k]).replace('"', "'") + '"' for k in
                              ("Reference", "Value", "Manufacturer", "Part", "Description", "Datasheet", "Sheet")))
    bom_path = ROOT.parent / "docs" / "BOM.csv"
    bom_path.parent.mkdir(parents=True, exist_ok=True)
    bom_path.write_text("\n".join(lines) + "\n")
    print(f"sheets {len(sheet_meta)} bom {len(seen)} pcb bytes { (ROOT/'hackrf-ultra.kicad_pcb').stat().st_size}")


if __name__ == "__main__":
    main()
