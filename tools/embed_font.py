"""Embed the pinned OFL Latin and Arabic fonts; no runtime font-file dependency."""
from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parents[1]
FONTS = [
    (ROOT / 'assets/fonts/NotoSans-Light.ttf',
     '74ffdd438f2ae232371ceb00444dae93e2590d263a4ff4c5e2c8385aa8012fdb',
     'psmtp_font_data'),
    (ROOT / 'assets/fonts/NotoSansArabic-Regular.ttf',
     '504d7407d86875acf7d04dfaa0fd7524d0b8797723bc4aa18022f29db25b0b6e',
     'psmtp_arabic_font_data'),
]


def embed():
    out = '/* Generated from bundled OFL fonts; see their adjacent license files. */\n'
    for font, expected, symbol in FONTS:
        data = font.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Bundled font changed; review before embedding: {font.name}')
        out += f'static const unsigned char {symbol}[]={{\n'
        out += ''.join(','.join(str(v) for v in data[i:i + 32]) + ',\n'
                       for i in range(0, len(data), 32))
        out += '};\n'
    target = ROOT / 'src/ps4/font_data.inc'
    if not target.exists() or target.read_text(encoding='ascii') != out:
        target.write_text(out, encoding='ascii')
    return target


if __name__ == '__main__':
    print(embed())
