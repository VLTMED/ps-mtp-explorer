#ifndef PSMTP_LOCALE_AR_H
#define PSMTP_LOCALE_AR_H
#include <stddef.h>
#include <stdint.h>

/* Translate an exact UI string or printf-format template; otherwise return it unchanged. */
const char *psmtp_translate_text(const char *text);

/* Decode, sanitize bidi controls, Arabic-shape and reorder one UI text run. */
size_t psmtp_text_visual(const char *text, uint32_t *visual, size_t capacity, int *is_rtl);

/* This build uses Arabic right-to-left UI layout. */
int psmtp_locale_rtl(void);

#endif
