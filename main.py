#!/usr/bin/env python3
"""news-image-20261124 -- Tuesday 24 November 2026 in one picture.

Pure Python 3.13 standard library. Draws a 1024x1024 PNG front page
summarising the day's world news (researched from reputable sources,
recorded in NEWS.md) and writes it to /output/entry.png.

No network at run time. Output is deterministic: fixed layout, fixed
palette, fixed zlib settings, so two runs write byte-identical files.
"""
import os
import struct
import zlib

W = H = 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)   # warm newsprint
INK = (26, 26, 26)        # near-black text
RED = (179, 38, 30)       # masthead / kicker red
GREY = (96, 92, 82)       # secondary text
BAND = (233, 227, 213)    # region strip background
RULE = (200, 192, 176)    # hairlines

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows, each a 5-bit mask (bit 4 = leftmost pixel).
F = {
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '.': (0, 0, 0, 0, 0, 0b01100, 0b01100),
    ',': (0, 0, 0, 0, 0b01100, 0b00100, 0b01000),
    ':': (0, 0b01100, 0b01100, 0, 0b01100, 0b01100, 0),
    ';': (0, 0b01100, 0b01100, 0, 0b01100, 0b00100, 0b01000),
    "'": (0b00100, 0b00100, 0b01000, 0, 0, 0, 0),
    '"': (0b01010, 0b01010, 0, 0, 0, 0, 0),
    '-': (0, 0, 0, 0b01110, 0, 0, 0),
    '(': (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '&': (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    '%': (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '+': (0, 0b00100, 0b00100, 0b01110, 0b00100, 0b00100, 0),
    '!': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0, 0b00100),
    '?': (0b01110, 0b10001, 0b00001, 0b00110, 0b00100, 0, 0b00100),
    '*': (0, 0b00100, 0b10101, 0b01110, 0b10101, 0b00100, 0),
    '=': (0, 0, 0b11111, 0, 0b11111, 0, 0),
    '_': (0, 0, 0, 0, 0, 0, 0b11111),
}


def glyph(ch):
    return F.get(ch, F['?'])


def char_w(scale):
    return 6 * scale


def text_w(text, scale):
    return len(text) * char_w(scale) - scale


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def draw_text(self, text, x, y, scale, color):
        cx = x
        r, g, b = color
        for ch in text:
            rows = glyph(ch)
            for ry in range(7):
                mask = rows[ry]
                if not mask:
                    continue
                for rx in range(5):
                    if mask & (1 << (4 - rx)):
                        px0, py0 = cx + rx * scale, y + ry * scale
                        for dy in range(scale):
                            base = ((py0 + dy) * self.w + px0) * 3
                            for dx in range(scale):
                                i = base + dx * 3
                                self.px[i] = r
                                self.px[i + 1] = g
                                self.px[i + 2] = b
            cx += char_w(scale)
        return cx

    def text_center(self, text, cx, y, scale, color):
        self.draw_text(text, cx - text_w(text, scale) // 2, y, scale, color)


def wrap(text, scale, max_w):
    """Greedy word wrap; returns list of lines, each fitting max_w px."""
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------------ content
LEAD_KICKER = "LEAD  -  CLIMATE  -  ANTALYA, TURKEY"
LEAD_HEAD = "COP31 COLLAPSES WITH NO DEAL"
LEAD_BODY = (
    "AFTER THE LONGEST CLIMATE SUMMIT IN HISTORY, MORE THAN 90 NATIONS "
    "REJECTED THE FINAL TEXT BECAUSE IT NEVER MENTIONED FOSSIL FUELS. "
    "THE FIRST COP SINCE COPENHAGEN 2009 TO END WITHOUT AN AGREEMENT."
)

# (region, headline, detail)
STORIES = [
    ("AFRICA", "UKRAINE SINKS RUSSIAN WARSHIP OFF LIBYA",
     "KYIV SAYS SEVEN SEA DRONES SANK THE CORVETTE MERKURY AT BENGHAZI."),
    ("EUROPE", "RUSSIA KEEPS TESTING NATO'S SKIES",
     "25 AIRSPACE VIOLATIONS IN 2026; A DRONE BRIEFLY ENTERED POLAND."),
    ("MIDDLE EAST", "US-IRAN STANDOFF SHARPENS AT HORMUZ",
     "UK LOGS RECORD IRANIAN ATTACKS IN THE STRAIT; US AND QATAR HOLD TALKS."),
    ("MIDDLE EAST", "ISRAELI STRIKES KILL THREE IN GAZA",
     "DEAD INCLUDE A UNRWA WORKER; 99% OF GAZA FACES CONTAMINATION RISK."),
    ("ASIA", "FACTORY FIRE KILLS 24 IN INDONESIA",
     "CANDY PLANT BLAZE IN BANTEN LEAVES ABOUT 30 WORKERS MISSING."),
    ("ASIA", "US BLACKLISTS MEGASPEED",
     "SINGAPORE FIRM IN NVIDIA SPY CASE HIT WITH EXPORT CONTROLS."),
    ("BUSINESS", "NVIDIA BRINGS BACK HUANG",
     "BOARD UNANIMOUSLY REINSTATES ITS CEO DAYS AFTER HIS OUSTER."),
    ("AMERICAS", "DEMOCRATS WIN 258 SEATS",
     "LARGEST HOUSE MAJORITY SINCE 1992; FIRST GEN Z WOMAN ELECTED."),
    ("AMERICAS", "STATES SUE SPACEX OVER GROK IMAGES",
     "OREGON AND VIRGINIA SUE OVER ALLEGED GROK-GENERATED ABUSE IMAGES."),
    ("AMERICAS", "CAR BOMB ROCKS COLOMBIA",
     "BLAST DESTROYS BUILDINGS IN VILLAVICENCIO."),
    ("SPORT", "ALCARAZ WINS ATP FINALS",
     "BEATS ZVEREV IN TURIN; MARQUEZ CLINCHES AN EIGHTH MOTOGP TITLE."),
]

ALSO = [
    "ZELENSKYY URGES FOUR-WAY TALKS",
    "PENTAGON REBUKES CANADA OVER F-35S",
    "SOUTH KOREA TRACKS RUSSIAN JETS",
    "INDIA NO. 3 IN ASIA POWER INDEX",
]

REGION_LINE_1 = "GLOBAL 1    EUROPE 1    MIDDLE EAST 2    AFRICA 1"
REGION_LINE_2 = "ASIA 2    AMERICAS 3    BUSINESS 1    SPORT 1"

FOOTER = "SOURCES: CNN, FT, NPR, GUARDIAN, AP, AL JAZEERA, ABC NEWS  -  24 NOV 2026"


# ------------------------------------------------------------------- render
def render():
    c = Canvas(W, H, PAPER)
    M = 36                      # side margin
    CW = W - 2 * M              # content width

    # ---- masthead ------------------------------------------------------
    c.text_center("TUESDAY'S WORLD NEWS", W // 2, 28, 2, RED)
    c.text_center("TUESDAY 24 NOVEMBER 2026", W // 2, 50, 5, INK)
    c.text_center("IN ONE PICTURE  -  12 DATED STORIES  -  8 REGIONS",
                  W // 2, 96, 3, GREY)
    c.hline(M, 132, CW, RED, 4)
    c.hline(M, 140, CW, INK, 1)

    # ---- lead story ----------------------------------------------------
    y = 152
    c.draw_text(LEAD_KICKER, M, y, 2, RED)
    y += 26
    c.draw_text(LEAD_HEAD, M, y, 4, INK)
    y += 40
    for line in wrap(LEAD_BODY, 2, CW):
        c.draw_text(line, M, y, 2, GREY)
        y += 17
    c.hline(M, 262, CW, RULE, 1)

    # ---- region strip --------------------------------------------------
    c.rect(M, 270, CW, 40, BAND)
    c.text_center(REGION_LINE_1, W // 2, 277, 2, INK)
    c.text_center(REGION_LINE_2, W // 2, 295, 2, INK)

    # ---- story grid: 2 columns x 6 rows -------------------------------
    gx, gy = M, 322
    col_w = (CW - 24) // 2
    row_h, row_gap = 104, 5
    for idx, (region, head, detail) in enumerate(STORIES):
        col, row = idx % 2, idx // 2
        x = gx + col * (col_w + 24)
        yy = gy + row * (row_h + row_gap)
        c.draw_text(region, x, yy + 4, 2, RED)
        hy = yy + 20
        head_lines = wrap(head, 3, col_w)
        assert len(head_lines) <= 2, f"headline wraps to {len(head_lines)} lines: {head!r}"
        for line in head_lines:
            c.draw_text(line, x, hy, 3, INK)
            hy += 25
        dy = yy + 70
        detail_lines = wrap(detail, 2, col_w)
        assert len(detail_lines) <= 2, f"detail wraps to {len(detail_lines)} lines: {detail!r}"
        for line in detail_lines:
            c.draw_text(line, x, dy, 2, GREY)
            dy += 17
        if col == 0:
            c.rect(x + col_w + 12, yy + 4, 1, row_h - 8, RULE)

    # ---- "also today" box (fills the 12th grid slot) -------------------
    x = gx + (col_w + 24)
    yy = gy + 5 * (row_h + row_gap)
    c.rect(x, yy, col_w, row_h, BAND)
    c.draw_text("ALSO TODAY", x + 10, yy + 6, 2, RED)
    ay = yy + 26
    for item in ALSO:
        lines = wrap("* " + item, 2, col_w - 20)
        assert len(lines) == 1, f"ALSO item wraps: {item!r}"
        for line in lines:
            c.draw_text(line, x + 10, ay, 2, INK)
            ay += 17

    # ---- footer ---------------------------------------------------------
    c.hline(M, 982, CW, INK, 1)
    c.text_center(FOOTER, W // 2, 992, 2, GREY)
    return c


# ------------------------------------------------------------- PNG encoder
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def png_bytes(canvas):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        start = y * canvas.w * 3
        raw += canvas.px[start:start + canvas.w * 3]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def write_png(canvas, path):
    png = png_bytes(canvas)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


def main():
    # Gate assertions: render twice, outputs must be byte-identical.
    png1 = png_bytes(render())
    png2 = png_bytes(render())
    assert png1 == png2, "non-deterministic output: two renders differ"
    # Gate assertions: a whole 1024x1024 PNG, at most 1 MiB.
    assert png1[:8] == b"\x89PNG\r\n\x1a\n", "output is not a PNG"
    w, h = struct.unpack(">II", png1[16:24])
    assert (w, h) == (1024, 1024), f"expected 1024x1024, got {w}x{h}"
    assert len(png1) <= 1048576, f"output {len(png1)} bytes exceeds 1 MiB"
    size = write_png(render(), OUT)
    assert size == len(png1), "written file differs from verified bytes"
    print(f"wrote {OUT}: {w}x{h}, {size} bytes")


if __name__ == "__main__":
    main()
