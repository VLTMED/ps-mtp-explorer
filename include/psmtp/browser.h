#ifndef PSMTP_BROWSER_H
#define PSMTP_BROWSER_H
#include "mtp.h"
#include <stdio.h>


int mtp_browser(mtp_client *, FILE *, FILE *, int);

void mtp_print_name(FILE *, const char *);
#endif
