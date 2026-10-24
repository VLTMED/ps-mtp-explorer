#ifndef PSMTP_DEVICE_SOUND_H
#define PSMTP_DEVICE_SOUND_H
#include <stddef.h>
#include <stdint.h>
#define PSMTP_CHIME_RATE 48000u
#define PSMTP_CHIME_FRAMES 24000u
#define PSMTP_CHIME_BLOCK 256u

void psmtp_chime_render(int connected,size_t frame,int16_t *,size_t frames);
#endif
