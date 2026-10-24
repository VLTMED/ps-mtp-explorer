#ifndef PSMTP_DIRENT_CHECK_H
#define PSMTP_DIRENT_CHECK_H
/* readdir owns traversal of its variable-length native buffer. BSD permits
 * the final record to absorb block slack, beyond sizeof(struct dirent).
 * Check only the prefix/name we actually read; never copy d_reclen bytes.
 * Reference: FreeBSD releng/9.0 sys/ufs/ufs/dir.h (directory block layout). */
static int psmtp_dirent_valid(const struct dirent *entry) {
    size_t n=entry->d_namlen;
    return n<sizeof(entry->d_name) && entry->d_reclen>=8u+n+1u &&
        entry->d_name[n]==0 && memchr(entry->d_name,0,n)==NULL;
}
#endif
