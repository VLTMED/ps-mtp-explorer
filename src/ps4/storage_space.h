#ifndef PSMTP_STORAGE_SPACE_H
#define PSMTP_STORAGE_SPACE_H
#include <stdint.h>
#include <stdio.h>
int psmtp_native_space(const char *,const char *,uint64_t *,uint64_t *,FILE *);


int psmtp_space_require(const char *,const char *,uint64_t,FILE *);
#endif
