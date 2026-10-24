#ifndef PSMTP_NAME_H
#define PSMTP_NAME_H
#include <stddef.h>
#include <stdint.h>
int psmtp_name_encode(const char *,uint8_t *,size_t,size_t *);
int psmtp_name_valid(const char *);
#endif
