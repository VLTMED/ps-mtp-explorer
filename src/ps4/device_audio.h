#ifndef PSMTP_DEVICE_AUDIO_H
#define PSMTP_DEVICE_AUDIO_H
#include <stdio.h>
void psmtp_audio_open(FILE *);
void psmtp_audio_notify(unsigned,FILE *);
void psmtp_audio_status(FILE *);
void psmtp_audio_close(FILE *);
#endif
