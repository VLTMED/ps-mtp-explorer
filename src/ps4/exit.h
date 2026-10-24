#ifndef PSMTP_PS4_EXIT_H
#define PSMTP_PS4_EXIT_H
#include <stdio.h>

__attribute__((noreturn)) void psmtp_ps4_exit(int status,FILE *log);
#endif
