#ifndef LIBJBC_H
#define LIBJBC_H

#ifdef __cplusplus
extern "C" {
#endif



#include "jailbreak.h"
#include "kernelrw.h"
typedef struct jbc_cred jbc_cred;


enum {
  CWD_KEEP,
  CWD_ROOT,
  CWD_RESET,
};

void jbc_run_as_root(void (*fn)(void *arg), void *arg, int cwd_mode);
int jbc_mount_in_sandbox(const char *system_path, const char *mnt_name);
int jbc_unmount_in_sandbox(const char *mnt_name);

#ifdef __cplusplus
}
#endif

#endif
