#ifndef PSMTP_UI_FONT_H
#define PSMTP_UI_FONT_H
#include <stdint.h>
int psmtp_font_init(void);
void psmtp_font_close(void);
int psmtp_font_width(const char *,int);
void psmtp_font_draw(uint32_t *,int,int,int,int,const char *,uint32_t);
#endif
