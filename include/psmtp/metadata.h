#ifndef PSMTP_METADATA_H
#define PSMTP_METADATA_H
#include <stddef.h>
#include <stdint.h>
typedef struct {void *user;uint64_t size;int (*read)(void *,uint64_t,uint8_t *,size_t);size_t consumed;} psmtp_meta_reader;
typedef struct {
    unsigned width,height;uint64_t duration_ms,items;int items_known,loaded,error;
    char title[128],content_id[64],title_id[32],version[32],codec[24];
    uint32_t *image;unsigned image_width,image_height;
    uint64_t revision;
} psmtp_metadata;
int psmtp_metadata_load(psmtp_meta_reader *,const char *,psmtp_metadata *);
int psmtp_metadata_image(const uint8_t *,size_t,psmtp_metadata *);
void psmtp_metadata_free(psmtp_metadata *);
#endif
