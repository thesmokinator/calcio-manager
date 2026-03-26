"""Convert an image to half-block terminal background art.

Uses "cover" mode: resizes to fill the target area, then center-crops.
Half-block characters (U+2580) give 2 vertical pixels per terminal row.

Usage:
    uv run --with pillow python scripts/convert_image.py <image> [options]
"""

import argparse
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
    """Convert an image to a Python module with hex-encoded half-block art."""
    parser = argparse.ArgumentParser(description="Convert image to terminal art")
    parser.add_argument("image", help="Path to the source image")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--cols", type=int, default=200, help="Target columns (default: 200)")
    parser.add_argument("--rows", type=int, default=50, help="Target terminal rows (default: 50)")
    parser.add_argument("--brightness", type=float, default=0.35, help="Brightness factor (default: 0.35)")
    parser.add_argument("--desaturation", type=float, default=0.5, help="Desaturation factor (default: 0.5)")
    args = parser.parse_args()

    img = Image.open(args.image).convert("RGB")
    orig_w, orig_h = img.size
    print(f"Original: {orig_w}x{orig_h}", file=sys.stderr)

    cols = args.cols
    rows = args.rows
    pixel_rows = rows * 2

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
            r1, g1, b1 = mute(r1, g1, b1, args.brightness, args.desaturation)
            r2, g2, b2 = mute(r2, g2, b2, args.brightness, args.desaturation)
            data.extend([r1, g1, b1, r2, g2, b2])

    hex_str = data.hex()
    print(f"Data:     {len(data)} bytes  ({cols}x{rows} cells)", file=sys.stderr)

    # Build output
    out = sys.stdout
    if args.output:
        out = open(args.output, "w")

    out.write(f'"""Pre-rendered background art ({cols}x{rows})."""\n\n')
    out.write(f"COLS = {cols}\n")
    out.write(f"ROWS = {rows}\n")
    out.write('# Half-block art: each cell = 6 bytes (R1G1B1 R2G2B2) for fg/bg of \\u2580\n')
    out.write("DATA = (\n")
    line_len = 120
    for i in range(0, len(hex_str), line_len):
        out.write(f'    "{hex_str[i:i + line_len]}"\n')
    out.write(")\n")

    if args.output:
        out.close()
        print(f"Written:  {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
