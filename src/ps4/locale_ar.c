#include "psmtp/locale_ar.h"
#include <string.h>
#include <fribidi.h>
#include <fribidi-arabic.h>
#include <fribidi-brackets.h>
#include <fribidi-joining.h>
#include <fribidi-joining-types.h>
#include <fribidi-shape.h>

#define PSMTP_TEXT_CAPACITY 2048u
typedef struct { const char *source; const char *translated; } psmtp_translation;
#include "locale_ar_data.inc"

const char *psmtp_translate_text(const char *text) {
    size_t i;
    if (!text) return "";
    for (i = 0; i < sizeof(psmtp_ar_translations) / sizeof(psmtp_ar_translations[0]); ++i)
        if (!strcmp(text, psmtp_ar_translations[i].source)) return psmtp_ar_translations[i].translated;
    return text;
}

int psmtp_locale_rtl(void) { return 1; }

static FriBidiChar chars[PSMTP_TEXT_CAPACITY];
static FriBidiCharType bidi_types[PSMTP_TEXT_CAPACITY];
static FriBidiBracketType bracket_types[PSMTP_TEXT_CAPACITY];
static FriBidiLevel levels[PSMTP_TEXT_CAPACITY];
static FriBidiArabicProp arabic_props[PSMTP_TEXT_CAPACITY];

static uint32_t utf8_next(const unsigned char **text) {
    const unsigned char *p = *text;
    uint32_t c;
    unsigned n, i;
    if (!*p) return 0;
    c = *p++;
    if (c < 0x80) { *text = p; return c; }
    if (c >= 0xc2 && c <= 0xdf) { c &= 0x1f; n = 1; }
    else if (c >= 0xe0 && c <= 0xef) { c &= 0x0f; n = 2; }
    else if (c >= 0xf0 && c <= 0xf4) { c &= 0x07; n = 3; }
    else { *text = p; return 0xfffd; }
    for (i = 0; i < n; ++i) {
        if ((p[i] & 0xc0) != 0x80) { *text = p; return 0xfffd; }
        c = (c << 6) | (p[i] & 0x3f);
    }
    *text = p + n;
    if ((n == 1 && c < 0x80) || (n == 2 && c < 0x800) ||
        (n == 3 && c < 0x10000) || c > 0x10ffff ||
        (c >= 0xd800 && c <= 0xdfff)) return 0xfffd;
    return c;
}

static const char *bidi_control_name(uint32_t c) {
    switch (c) {
        case 0x061c: return "[ALM]";
        case 0x200e: return "[LRM]";
        case 0x200f: return "[RLM]";
        case 0x202a: return "[LRE]";
        case 0x202b: return "[RLE]";
        case 0x202c: return "[PDF]";
        case 0x202d: return "[LRO]";
        case 0x202e: return "[RLO]";
        case 0x2066: return "[LRI]";
        case 0x2067: return "[RLI]";
        case 0x2068: return "[FSI]";
        case 0x2069: return "[PDI]";
        default: return NULL;
    }
}

static int is_rtl_codepoint(uint32_t c) {
    return (c >= 0x0590 && c <= 0x08ff) ||
           (c >= 0xfb1d && c <= 0xfdff) ||
           (c >= 0xfe70 && c <= 0xfeff) ||
           (c >= 0x1ee00 && c <= 0x1eeff);
}

static size_t append_ascii_label(const char *s, size_t length) {
    while (*s && length < PSMTP_TEXT_CAPACITY) chars[length++] = (unsigned char)*s++;
    return length;
}

size_t psmtp_text_visual(const char *text, uint32_t *visual, size_t capacity, int *is_rtl) {
    const unsigned char *p;
    size_t length = 0, i, count;
    int rtl = 0;
    FriBidiParType base_dir;
    FriBidiLevel max_level;
    if (is_rtl) *is_rtl = 0;
    if (!text || !visual || !capacity) return 0;
    text = psmtp_translate_text(text);
    p = (const unsigned char *)text;
    while (*p && length < PSMTP_TEXT_CAPACITY) {
        uint32_t c = utf8_next(&p);
        const char *control = bidi_control_name(c);
        if (control) {
            length = append_ascii_label(control, length);
            continue;
        }
        chars[length++] = (FriBidiChar)c;
        if (is_rtl_codepoint(c)) rtl = 1;
    }
    count = length < capacity ? length : capacity;
    if (!length) return 0;
    if (rtl) {
        base_dir = FRIBIDI_PAR_RTL;
        fribidi_get_bidi_types(chars, (FriBidiStrIndex)length, bidi_types);
        fribidi_get_bracket_types(chars, (FriBidiStrIndex)length, bidi_types, bracket_types);
        max_level = fribidi_get_par_embedding_levels_ex(bidi_types, bracket_types,
                       (FriBidiStrIndex)length, &base_dir, levels);
        if (max_level) {
            fribidi_get_joining_types(chars, (FriBidiStrIndex)length, arabic_props);
            fribidi_join_arabic(bidi_types, (FriBidiStrIndex)length, levels, arabic_props);
            fribidi_shape(FRIBIDI_FLAGS_ARABIC | FRIBIDI_FLAG_SHAPE_MIRRORING,
                          levels, (FriBidiStrIndex)length, arabic_props, chars);
            if (fribidi_reorder_line(FRIBIDI_FLAGS_DEFAULT, bidi_types,
                                      (FriBidiStrIndex)length, 0, base_dir,
                                      levels, chars, NULL) != 0) {
                if (is_rtl) *is_rtl = 1;
                for (i = 0; i < count; ++i) visual[i] = chars[i];
                return count;
            }
        }
        if (is_rtl) *is_rtl = 1;
    }
    for (i = 0; i < count; ++i) visual[i] = chars[i];
    return count;
}
