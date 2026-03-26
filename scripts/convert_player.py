"""Convert image to full-screen terminal background art.

Uses "cover" mode: resizes to fill the target area, then center-crops.
Half-block characters (U+2580) give 2 vertical pixels per terminal row.
"""

import sys
from colorsys import hls_to_rgb, rgb_to_hls

from PIL import Image


def mute(
    r: int, g: int, b: int,
    brightness: float = 0.35, desat: float = 0.5,
) -> tuple[int, int, int]:
    """Dim and desaturate a colour for a faded background look."""
    rf, gf, bf = r / 255, g / 255, b / 255
    h, l, s = rgb_to_hls(rf, gf, bf)
    l = min(1.0, l * brightness)
    s *= desat
    rf, gf, bf = hls_to_rgb(h, l, s)
    return int(rf * 255), int(gf * 255), int(bf * 255)


def main() -> None:
    img_path = sys.argv[1]
    img = Image.open(img_path).convert("RGB")
    orig_w, orig_h = img.size
    print(f"Original: {orig_w}x{orig_h}", file=sys.stderr)

    cols = 200          # target terminal columns
    rows = 50           # target terminal rows
    pixel_rows = rows * 2  # 2 vertical pixels per terminal row (half-blocks)

    # "Cover" resize: scale to fill, then center-crop
    scale = max(cols / orig_w, pixel_rows / orig_h)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    print(f"Scaled:   {new_w}x{new_h}", file=sys.stderr)

    left = (new_w - cols) // 2
    top = (new_h - pixel_rows) // 2
    img = img.crop((left, top, left + cols, top + pixel_rows))
    print(f"Cropped:  {cols}x{pixel_rows}  ->  {cols}x{rows} terminal", file=sys.stderr)

    pixels = list(img.getdata())

    data = bytearray()
    for row in range(0, pixel_rows, 2):
        for col in range(cols):
            r1, g1, b1 = pixels[row * cols + col]
            if row + 1 < pixel_rows:
                r2, g2, b2 = pixels[(row + 1) * cols + col]
            else:
                r2, g2, b2 = 0, 0, 0
            r1, g1, b1 = mute(r1, g1, b1)
            r2, g2, b2 = mute(r2, g2, b2)
            data.extend([r1, g1, b1, r2, g2, b2])

    hex_str = data.hex()
    print(f"Data:     {len(data)} bytes  ({cols}x{rows} cells)", file=sys.stderr)

    # Output Python module
    print(f'"""Pre-rendered background art ({cols}x{rows})."""')
    print()
    print(f"COLS = {cols}")
    print(f"ROWS = {rows}")
    print("# Half-block art: each cell = 6 bytes (R1G1B1 R2G2B2) for fg/bg of \\u2580")
    print("DATA = (")
    line_len = 120
    for i in range(0, len(hex_str), line_len):
        print(f'    "{hex_str[i:i + line_len]}"')
    print(")")


if __name__ == "__main__":
    main()
