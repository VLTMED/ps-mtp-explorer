"""Embed the checked-in Arabic UI catalog as UTF-8 C string literals."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'locales/ar.json'
TARGET = ROOT / 'src/ps4/locale_ar_data.inc'
PRINTF = re.compile(r'%(?:\d+\$)?[-+ #0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?(?:hh|h|ll|l|z|t|j|L)?[diouxXfFeEgGaAcspn]')


def c_string(value: str) -> str:
    # JSON string escapes are valid C string escapes; raw Arabic remains UTF-8.
    return json.dumps(value, ensure_ascii=False)


def embed() -> Path:
    translations = json.loads(CATALOG.read_text(encoding='utf-8'))
    if not isinstance(translations, dict) or not translations:
        raise ValueError('Arabic catalog must be a non-empty JSON object')
    entries = []
    for source, target in sorted(translations.items()):
        if not isinstance(source, str) or not isinstance(target, str) or not source:
            raise ValueError('Arabic catalog contains an invalid entry')
        src_tokens = PRINTF.findall(source)
        dst_tokens = PRINTF.findall(target)
        if src_tokens != dst_tokens:
            raise ValueError(f'format placeholders differ for {source!r}: {src_tokens!r} != {dst_tokens!r}')
        entries.append(f'    {{ {c_string(source)}, {c_string(target)} }},')
    output = '/* Generated from locales/ar.json by tools/embed_locale.py. */\n'
    output += 'static const psmtp_translation psmtp_ar_translations[] = {\n'
    output += '\n'.join(entries) + '\n};\n'
    if not TARGET.exists() or TARGET.read_text(encoding='utf-8') != output:
        TARGET.write_text(output, encoding='utf-8')
    return TARGET


if __name__ == '__main__':
    print(embed())
