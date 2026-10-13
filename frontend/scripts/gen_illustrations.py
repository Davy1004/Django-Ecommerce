#!/usr/bin/env python3
"""Generates the flat product illustrations in frontend/public/products/*.svg.

Original artwork drawn in code (no stock photos, no licences). Run from repo root:
    python3 frontend/scripts/gen_illustrations.py
The file name must equal the product slug so the storefront can find it.
"""
import pathlib
import xml.dom.minidom

OUT = pathlib.Path(__file__).resolve().parents[1] / "public" / "products"

# category -> (gradient top, gradient bottom, blob)
THEME = {
    "electronics": ("#dbeafe", "#bfdbfe", "#eff6ff"),
    "books": ("#dcfce7", "#bbf7d0", "#f0fdf4"),
    "home": ("#fef3c7", "#fde68a", "#fffbeb"),
    "fashion": ("#fce7f3", "#fbcfe8", "#fdf2f8"),
    "fitness": ("#ffedd5", "#fed7aa", "#fff7ed"),
    "stationery": ("#ede9fe", "#ddd6fe", "#f5f3ff"),
}


def R(x, y, w, h, rx=0, fill="#fff", extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" {extra}/>'


def C(x, y, r, fill="#fff", extra=""):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" {extra}/>'


def E(x, y, rx, ry, fill="#fff", extra=""):
    return f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" {extra}/>'


def P(d, fill="none", extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def L(x1, y1, x2, y2, stroke="#fff", w=6, extra=""):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" {extra}/>'


def book(cover, band, deco, spine="#0003"):
    return (R(190, 120, 220, 330, 10, cover) + R(190, 120, 22, 330, 10, spine)
            + R(232, 170, 150, 14, 7, "#fff", 'opacity=".9"') + R(232, 196, 110, 14, 7, "#fff", 'opacity=".7"')
            + band + deco)


def cup(x, y, body, rim="#fff"):
    return (P(f"M{x} {y} h110 v20 a55 70 0 0 1 -110 0 z", body)
            + E(x + 55, y, 55, 14, rim, 'opacity=".95"') + E(x + 55, y + 2, 46, 9, "#0002")
            + P(f"M{x + 108} {y + 25} q42 4 0 56", "none", f'stroke="{body}" stroke-width="14" stroke-linecap="round"'))


M = {}  # slug -> (category, svg body)

# ---------------- electronics ----------------
M["wireless-earbuds"] = ("electronics",
    R(195, 290, 210, 150, 55, "#f4f4f6", 'stroke="#d4d4dc" stroke-width="4"') + R(195, 270, 210, 70, 35, "#e6e6ee", 'stroke="#d4d4dc" stroke-width="4"')
    + C(300, 372, 7, "#22c55e") + L(215, 340, 385, 340, "#d4d4dc", 4)
    + E(245, 195, 30, 38, "#fff", 'stroke="#cfcfd8" stroke-width="4"') + R(258, 215, 15, 66, 7.5, "#fff", 'stroke="#cfcfd8" stroke-width="4"')
    + E(355, 195, 30, 38, "#fff", 'stroke="#cfcfd8" stroke-width="4"') + R(327, 215, 15, 66, 7.5, "#fff", 'stroke="#cfcfd8" stroke-width="4"')
    + C(245, 190, 9, "#cbd5e1") + C(355, 190, 9, "#cbd5e1"))
M["smart-watch"] = ("electronics",
    R(255, 110, 90, 380, 34, "#334155") + R(215, 215, 170, 190, 50, "#111827") + R(228, 228, 144, 164, 40, "#0b1220")
    + C(300, 310, 58, "none", 'stroke="#38bdf8" stroke-width="7"') + C(300, 310, 42, "none", 'stroke="#f472b6" stroke-width="7" stroke-dasharray="120 300"')
    + L(300, 310, 300, 272, "#fff", 6) + L(300, 310, 326, 322, "#fff", 6) + R(385, 290, 14, 40, 6, "#475569")
    + C(285, 255, 5, "#facc15") + R(250, 350, 100, 8, 4, "#38bdf8", 'opacity=".6"'))
M["power-bank-20000mah"] = ("electronics",
    R(215, 130, 170, 320, 32, "#1e293b") + R(215, 130, 170, 320, 32, "none", 'stroke="#334155" stroke-width="4"')
    + R(240, 160, 120, 90, 14, "#0f172a") + C(262, 205, 7, "#22c55e") + C(288, 205, 7, "#22c55e") + C(314, 205, 7, "#22c55e") + C(340, 205, 7, "#475569")
    + R(245, 290, 110, 10, 5, "#38bdf8") + R(245, 316, 70, 10, 5, "#64748b") + R(250, 400, 30, 16, 4, "#94a3b8") + R(290, 400, 30, 16, 4, "#94a3b8")
    + P("M335 450 q40 60 110 30", "none", 'stroke="#38bdf8" stroke-width="10" stroke-linecap="round"'))
M["bluetooth-speaker"] = ("electronics",
    R(160, 210, 280, 230, 60, "#334155") + R(160, 210, 280, 230, 60, "none", 'stroke="#1e293b" stroke-width="5"')
    + "".join(C(200 + i * 25, 255 + j * 25, 5, "#64748b") for i in range(9) for j in (0, 6))
    + C(300, 335, 62, "#1e293b") + C(300, 335, 44, "#0f172a") + C(300, 335, 16, "#38bdf8")
    + C(232, 335, 12, "#1e293b") + C(368, 335, 12, "#1e293b") + R(270, 190, 60, 22, 11, "#f472b6"))
M["mechanical-keyboard"] = ("electronics",
    R(90, 240, 420, 200, 26, "#1f2937") + R(90, 240, 420, 200, 26, "none", 'stroke="#111827" stroke-width="5"')
    + "".join(R(112 + c * 37, 262 + r * 36, 31, 28, 7, "#e5e7eb" if (r + c) % 5 else "#f472b6") for r in range(4) for c in range(10))
    + R(150, 406, 220, 22, 8, "#e5e7eb") + R(380, 406, 100, 22, 8, "#38bdf8"))
M["laptop-stand"] = ("electronics",
    P("M205 150 h190 a10 10 0 0 1 10 10 v140 h-210 v-140 a10 10 0 0 1 10 -10z", "#1e293b") + R(217, 162, 166, 126, 6, "#7dd3fc")
    + P("M230 270 l40 -50 30 30 25 -40 40 60z", "#38bdf8") + C(345, 195, 12, "#fde68a")
    + P("M170 300 h260 l30 40 h-320z", "#cbd5e1") + P("M215 340 l-30 110 M385 340 l30 110", "none", 'stroke="#94a3b8" stroke-width="14" stroke-linecap="round"')
    + P("M215 340 h170 l-20 40 h-130z", "#94a3b8"))

# ---------------- books ----------------
M["clean-code"] = ("books", book("#16a34a", C(300, 330, 52, "#bbf7d0") + P("M275 330 l18 18 32 -38", "none", 'stroke="#15803d" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"'), R(232, 400, 150, 10, 5, "#bbf7d0")))
M["designing-data-intensive-applications"] = ("books", book("#2563eb",
    L(255, 320, 345, 320, "#bfdbfe", 5) + L(255, 320, 300, 385, "#bfdbfe", 5) + L(345, 320, 300, 385, "#bfdbfe", 5)
    + C(255, 320, 16, "#fff") + C(345, 320, 16, "#fff") + C(300, 385, 16, "#fde68a"), ""))
M["introduction-to-algorithms"] = ("books", R(180, 110, 240, 350, 10, "#7f1d1d") + R(180, 110, 24, 350, 10, "#0004") + R(180, 110, 240, 350, 10, "none", 'stroke="#450a0a" stroke-width="4"')
    + R(226, 160, 160, 14, 7, "#fecaca") + R(226, 186, 120, 14, 7, "#fecaca", 'opacity=".7"')
    + L(305, 280, 265, 340, "#fca5a5", 5) + L(305, 280, 345, 340, "#fca5a5", 5) + L(265, 340, 245, 395, "#fca5a5", 5) + L(265, 340, 285, 395, "#fca5a5", 5)
    + C(305, 280, 16, "#fff") + C(265, 340, 14, "#fff") + C(345, 340, 14, "#fff") + C(245, 395, 12, "#fde68a") + C(285, 395, 12, "#fff"))
M["the-pragmatic-programmer"] = ("books", book("#ea580c",
    C(300, 335, 50, "none", 'stroke="#fed7aa" stroke-width="14" stroke-dasharray="22 12"') + C(300, 335, 24, "#fff7ed"), R(232, 410, 150, 10, 5, "#fed7aa")))

# ---------------- home ----------------
M["ceramic-mug-set"] = ("home", cup(160, 300, "#f97316") + cup(300, 345, "#0ea5e9") + E(300, 465, 150, 14, "#0000", ""))
M["led-desk-lamp"] = ("home",
    E(300, 80, 0, 0, "none") + P("M230 140 L370 140 L400 235 L200 235z", "#fde68a", 'opacity=".35"') + P("M255 150 h90 l25 70 h-140z", "#1e293b")
    + P("M300 220 L300 330 L370 400", "none", 'stroke="#475569" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"')
    + C(300, 330, 10, "#94a3b8") + C(370, 400, 10, "#94a3b8") + E(370, 452, 80, 20, "#334155") + R(290, 215, 20, 12, 3, "#fde047"))
M["indoor-plant-pot"] = ("home",
    P("M230 360 h140 l-20 100 h-100z", "#c2410c") + R(220, 345, 160, 30, 8, "#ea580c")
    + P("M300 345 C 260 280 220 270 190 200 C 250 210 295 250 300 345z", "#16a34a") + P("M300 345 C 340 270 390 260 420 180 C 350 195 305 250 300 345z", "#22c55e")
    + P("M300 345 C 285 260 300 190 300 120 C 330 190 320 270 300 345z", "#15803d"))
M["scented-candle"] = ("home",
    R(220, 270, 160, 180, 26, "#fb7185") + R(220, 270, 160, 40, 20, "#fda4af") + R(250, 330, 100, 70, 10, "#fff1f2") + R(266, 345, 68, 8, 4, "#fb7185") + R(266, 365, 44, 8, 4, "#fda4af")
    + L(300, 270, 300, 238, "#334155", 6) + P("M300 150 C 335 190 335 225 300 238 C 265 225 265 190 300 150z", "#f59e0b") + P("M300 190 C 316 205 314 224 300 232 C 286 224 284 205 300 190z", "#fef08a"))

# ---------------- fashion ----------------
M["canvas-backpack"] = ("fashion",
    P("M230 170 a70 60 0 0 1 140 0", "none", 'stroke="#9d174d" stroke-width="16" stroke-linecap="round"')
    + P("M210 190 h180 a30 30 0 0 1 30 30 v200 a30 30 0 0 1 -30 30 h-180 a30 30 0 0 1 -30 -30 v-200 a30 30 0 0 1 30 -30z", "#be185d")
    + R(225, 330, 150, 90, 18, "#9d174d") + R(250, 300, 100, 14, 7, "#fbcfe8") + R(235, 225, 130, 70, 16, "#db2777") + R(285, 255, 30, 18, 4, "#fbcfe8")
    + L(262, 350, 338, 350, "#fbcfe8", 5))
M["running-sneakers"] = ("fashion",
    P("M120 380 C 120 330 150 330 190 320 L 230 230 C 250 200 280 215 300 245 C 330 290 400 290 460 330 C 485 345 485 380 485 400 H 120z", "#ef4444")
    + P("M120 400 H485 V425 a15 15 0 0 1 -15 15 H135 a15 15 0 0 1 -15 -15z", "#f8fafc")
    + P("M240 255 l40 40 M262 240 l38 38 M284 232 l32 32", "none", 'stroke="#fff" stroke-width="8" stroke-linecap="round"')
    + P("M320 345 q60 -10 140 20", "none", 'stroke="#fff" stroke-width="10" stroke-linecap="round"') + P("M170 385 h130", "none", 'stroke="#fecaca" stroke-width="8" stroke-linecap="round"'))
M["aviator-sunglasses"] = ("fashion",
    P("M120 255 H480", "none", 'stroke="#92400e" stroke-width="12" stroke-linecap="round"')
    + P("M135 262 C 135 340 230 380 270 300 C 285 270 275 262 135 262z", "#1e293b", 'stroke="#d97706" stroke-width="10" stroke-linejoin="round"')
    + P("M465 262 C 465 340 370 380 330 300 C 315 270 325 262 465 262z", "#1e293b", 'stroke="#d97706" stroke-width="10" stroke-linejoin="round"')
    + P("M278 268 q22 -22 44 0", "none", 'stroke="#d97706" stroke-width="10" stroke-linecap="round"')
    + P("M170 285 q25 40 60 20", "none", 'stroke="#fff" stroke-width="7" stroke-linecap="round" opacity=".5"')
    + P("M135 258 L100 235 M465 258 L500 235", "none", 'stroke="#d97706" stroke-width="12" stroke-linecap="round"'))
M["classic-cap"] = ("fashion",
    P("M160 340 C 160 220 230 170 310 170 C 390 170 440 240 440 340z", "#2563eb") + P("M310 170 V340", "none", 'stroke="#1d4ed8" stroke-width="5"')
    + P("M240 190 V340 M380 195 V340", "none", 'stroke="#1d4ed8" stroke-width="5"') + C(310, 170, 12, "#1e3a8a")
    + P("M150 340 H450 C 500 340 540 370 540 385 C 440 415 250 395 150 355z", "#1d4ed8") + P("M220 270 h60 v36 h-60z", "#fbbf24", "opacity=\".0\"") + C(305, 258, 22, "#fde68a"))

# ---------------- fitness ----------------
M["yoga-mat"] = ("fitness",
    R(130, 240, 330, 190, 20, "#14b8a6") + R(130, 240, 330, 190, 20, "none", 'stroke="#0f766e" stroke-width="4"')
    + E(460, 335, 55, 95, "#0d9488") + E(460, 335, 40, 72, "#14b8a6") + E(460, 335, 24, 46, "#0d9488") + E(460, 335, 9, 18, "#99f6e4")
    + L(160, 280, 400, 280, "#5eead4", 5) + L(160, 335, 400, 335, "#5eead4", 5) + L(160, 390, 400, 390, "#5eead4", 5)
    + R(190, 195, 150, 22, 11, "#f97316"))
M["hex-dumbbell-pair"] = ("fitness",
    R(165, 300, 270, 28, 14, "#94a3b8") + R(130, 255, 60, 118, 14, "#1f2937") + R(95, 270, 42, 88, 12, "#374151")
    + R(410, 255, 60, 118, 14, "#1f2937") + R(463, 270, 42, 88, 12, "#374151") + R(230, 296, 140, 36, 6, "#64748b")
    + L(250, 305, 250, 325, "#cbd5e1", 3) + L(270, 305, 270, 325, "#cbd5e1", 3) + L(290, 305, 290, 325, "#cbd5e1", 3)
    + L(310, 305, 310, 325, "#cbd5e1", 3) + L(330, 305, 330, 325, "#cbd5e1", 3) + L(350, 305, 350, 325, "#cbd5e1", 3))
M["steel-water-bottle"] = ("fitness",
    R(262, 110, 76, 50, 12, "#0f172a") + R(250, 150, 100, 28, 10, "#1e293b") + P("M250 178 h100 C 380 215 385 250 385 280 V430 a35 35 0 0 1 -35 35 H250 a35 35 0 0 1 -35 -35 V280 C 215 250 220 215 250 178z", "#0ea5e9")
    + R(215, 310, 170, 70, 0, "#0284c7") + C(300, 345, 20, "#e0f2fe") + P("M235 215 q-6 70 0 200", "none", 'stroke="#fff" stroke-width="9" stroke-linecap="round" opacity=".45"'))

# ---------------- stationery ----------------
M["hardcover-notebook"] = ("stationery",
    R(195, 120, 220, 330, 14, "#6d28d9") + R(195, 120, 26, 330, 14, "#0004") + R(375, 120, 14, 330, 0, "#a78bfa") + R(375, 120, 14, 330, 0, "#f59e0b", 'opacity=".9"')
    + R(250, 190, 100, 70, 8, "#ddd6fe") + L(268, 215, 332, 215, "#6d28d9", 5) + L(268, 235, 316, 235, "#6d28d9", 5) + P("M345 430 v50 l14 -12 14 12 v-50z", "#f43f5e"))
M["fountain-pen"] = ("stationery",
    '<g transform="rotate(-38 300 300)">' + R(110, 270, 280, 60, 30, "#1e1b4b") + R(380, 276, 60, 48, 8, "#fbbf24") + R(150, 270, 18, 60, 4, "#fbbf24")
    + P("M440 276 L520 300 L440 324z", "#fcd34d") + P("M440 300 L520 300", "none", 'stroke="#92400e" stroke-width="4"') + R(125, 285, 100, 10, 5, "#6366f1", 'opacity=".7"') + '</g>'
    + P("M395 470 q40 25 90 -5", "none", 'stroke="#4338ca" stroke-width="7" stroke-linecap="round" opacity=".6"'))
M["desk-organiser"] = ("stationery",
    R(150, 330, 300, 120, 18, "#a78bfa") + R(150, 330, 300, 30, 15, "#c4b5fd") + R(150, 390, 150, 60, 0, "#8b5cf6") + R(300, 360, 150, 90, 0, "#7c3aed")
    + L(205, 330, 190, 190, "#f43f5e", 14) + L(235, 330, 245, 170, "#0ea5e9", 14) + L(262, 330, 292, 200, "#fbbf24", 14)
    + R(335, 235, 90, 100, 8, "#fde68a") + L(350, 262, 410, 262, "#a16207", 4) + L(350, 280, 400, 280, "#a16207", 4))


def render(slug, cat, body):
    a, b, blob = THEME[cat]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img">'
           f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>'
           f'<rect width="600" height="600" fill="url(#g)"/>'
           f'<circle cx="470" cy="120" r="150" fill="{blob}" opacity=".55"/><circle cx="90" cy="520" r="120" fill="{blob}" opacity=".45"/>'
           f'<ellipse cx="300" cy="478" rx="170" ry="16" fill="#000" opacity=".11"/>'
           f'{body}</svg>')
    xml.dom.minidom.parseString(svg)  # fail loudly on malformed output
    return svg


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, (cat, body) in M.items():
        (OUT / f"{slug}.svg").write_text(render(slug, cat, body))
    print(f"wrote {len(M)} illustrations to {OUT}")


if __name__ == "__main__":
    main()
