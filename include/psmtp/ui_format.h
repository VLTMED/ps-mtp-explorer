#ifndef PSMTP_UI_FORMAT_H
#define PSMTP_UI_FORMAT_H
#include <stddef.h>
#include <stdint.h>
void psmtp_ui_size(char *,size_t,uint64_t);
const char *psmtp_ui_kind(const char *,int);
int psmtp_ui_name_compare(const char *,const char *);
enum {PSMTP_SORT_NAME,PSMTP_SORT_NAME_DESC,PSMTP_SORT_SIZE,PSMTP_SORT_SIZE_DESC,PSMTP_SORT_NEWEST,PSMTP_SORT_OLDEST,PSMTP_SORT_TYPE,PSMTP_SORT_COUNT};
const char *psmtp_ui_sort_label(int);
int psmtp_ui_compare(int,const char *,int,uint64_t,const char *,const char *,int,uint64_t,const char *);
void psmtp_ui_extension(char out[12],const char *,int);
#endif
