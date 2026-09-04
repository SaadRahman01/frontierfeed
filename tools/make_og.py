"""Generate docs/og.png — the 1200x630 social card. Run manually, commit the result.

Standard library only: zlib and struct are enough to emit a PNG, and the
wordmark is drawn from the bitmap font below rather than a real typeface. That
keeps requirements.txt at three lines. The card is static, so this script is
not part of the hourly run — re-run it only when the wordmark or tagline
changes.

    python tools/make_og.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

W, H = 1200, 630

PAPER = (0xE6, 0xE9, 0xE4)
INK = (0x10, 0x14, 0x18)
INK_SOFT = (0x4C, 0x55, 0x5E)
RULE = (0xC3, 0xCA, 0xC2)
BREAKING = (0x8E, 0x1B, 0x2E)
FEATURE = (0x2E, 0x5E, 0x4E)
FIX = (0x62, 0x6D, 0x78)

# 5x7 glyphs, one string per row. Only the characters the card actually uses.
FONT = {
    " ": ".....:.....:.....:.....:.....:.....:.....",
    "a": ".....:.###.:....#:.####:#...#:#...#:.####",
    "b": "#....:#....:####.:#...#:#...#:#...#:####.",
    "c": ".....:.....:.####:#....:#....:#....:.####",
    "d": "....#:....#:.####:#...#:#...#:#...#:.####",
    "e": ".....:.....:.###.:#...#:#####:#....:.####",
    "f": "..##.:.#..#:.#...:####.:.#...:.#...:.#...",
    "g": ".....:.....:.####:#...#:.####:....#:.###.",
    "h": "#....:#....:####.:#...#:#...#:#...#:#...#",
    "i": "..#..:.....:.##..:..#..:..#..:..#..:.###.",
    "j": "...#.:.....:..##.:...#.:...#.:#..#.:.##..",
    "k": "#....:#....:#...#:#..#.:###..:#..#.:#...#",
    "l": ".##..:..#..:..#..:..#..:..#..:..#..:.###.",
    "m": ".....:.....:##.#.:#.#.#:#.#.#:#.#.#:#.#.#",
    "n": ".....:.....:####.:#...#:#...#:#...#:#...#",
    "o": ".....:.....:.###.:#...#:#...#:#...#:.###.",
    "p": ".....:.....:####.:#...#:####.:#....:#....",
    "q": ".....:.....:.####:#...#:.####:....#:....#",
    "r": ".....:.....:#.##.:##..#:#....:#....:#....",
    "s": ".....:.....:.####:#....:.###.:....#:####.",
    "t": ".#...:.#...:####.:.#...:.#...:.#..#:..##.",
    "u": ".....:.....:#...#:#...#:#...#:#..##:.##.#",
    "v": ".....:.....:#...#:#...#:#...#:.#.#.:..#..",
    "w": ".....:.....:#...#:#.#.#:#.#.#:#.#.#:.#.#.",
    "x": ".....:.....:#...#:.#.#.:..#..:.#.#.:#...#",
    "y": ".....:.....:#...#:#...#:.####:....#:.###.",
    "z": ".....:.....:#####:...#.:..#..:.#...:#####",
    "'": "..#..:..#..:.....:.....:.....:.....:.....",
    "-": ".....:.....:.....:#####:.....:.....:.....",
    ".": ".....:.....:.....:.....:.....:.##..:.##..",
}

GLYPH_W, GLYPH_H = 5, 7
ADVANCE = 6  # glyph width plus a one-column gap


def blank() -> list[list[tuple[int, int, int]]]:
    return [[PAPER] * W for _ in range(H)]


def rect(px, x: int, y: int, w: int, h: int, color) -> None:
    for row in range(max(0, y), min(H, y + h)):
        line = px[row]
        for col in range(max(0, x), min(W, x + w)):
            line[col] = color


def text(px, s: str, x: int, y: int, scale: int, color) -> int:
    """Draw s at (x, y) scaled up. Returns the x cursor after the last glyph."""
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            raise KeyError(f"no glyph for {ch!r} — add it to FONT")
        for gy, row in enumerate(glyph.split(":")):
            for gx, cell in enumerate(row):
                if cell == "#":
                    rect(px, x + gx * scale, y + gy * scale, scale, scale, color)
        x += ADVANCE * scale
    return x


def width_of(s: str, scale: int) -> int:
    return len(s) * ADVANCE * scale - scale


def png(px) -> bytes:
    raw = bytearray()
    for row in px:
        raw.append(0)  # filter type 0 (None) for every scanline
        for r, g, b in row:
            raw += bytes((r, g, b))

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


WORDMARK = "frontierfeed"
LINE1 = "release and news tracker for claude"
LINE2 = "unofficial - open source - updated hourly"


def build() -> bytes:
    px = blank()
    rect(px, 0, 0, 22, H, INK)  # the left gauge the entry cards also use
    text(px, WORDMARK, 100, 200, 13, INK)
    rect(px, 100, 330, 1000, 2, RULE)
    text(px, LINE1, 102, 372, 4, INK_SOFT)
    text(px, LINE2, 102, 420, 4, INK_SOFT)
    for n, color in enumerate((BREAKING, FEATURE, FIX)):
        rect(px, 100 + n * 136, 520, 120, 14, color)
    return png(px)


def main() -> None:
    for label, s, scale in (("wordmark", WORDMARK, 13), ("line1", LINE1, 4), ("line2", LINE2, 4)):
        end = 100 + width_of(s, scale)
        if end > W - 60:
            raise SystemExit(f"{label} overflows the card: ends at {end}px of {W}")
    out = Path("docs/og.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(build())
    print(f"wrote {out} ({out.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
