#ifndef PSMTP_SHA256_H
#define PSMTP_SHA256_H
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t h[8]; uint64_t bytes; uint8_t block[64]; size_t used; } psmtp_sha256;
void psmtp_sha256_init(psmtp_sha256 *);
void psmtp_sha256_update(psmtp_sha256 *,const void *,size_t);
void psmtp_sha256_final(psmtp_sha256 *,uint8_t digest[32]);
#endif
