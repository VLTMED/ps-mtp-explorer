/* PSMTP integration changes are documented in NOTICE.txt. */
#include "defs.h"
#include "kernelrw.h"
#include "jailbreak.h"

#ifndef PSMTP_TEST_JBC
__asm__("psmtp_jbc_open:\nmov $5, %rax\nmov %rcx, %r10\nsyscall\njnc 1f\nneg %rax\n1: ret");
__asm__("psmtp_jbc_close:\nmov $6, %rax\nmov %rcx, %r10\nsyscall\njnc 1f\nneg %rax\n1: ret");

#endif
int psmtp_jbc_open(const char*, int);
int psmtp_jbc_close(int);

static uintptr_t prison0;
static uintptr_t rootvnode;

static int resolve(void)
{
unsigned restarts=0, visited;
restart:;
    if(++restarts>8) return -1;
    visited=0;
    uintptr_t td = jbc_krw_get_td();
    if(!td) return -1;
    uintptr_t proc = jbc_krw_read64(td+8, KERNEL_HEAP);
    for(;;)
    {
        if(++visited>4096) return -1;
        int pid;
        if(jbc_krw_memcpy((uintptr_t)&pid, proc+0xb0, sizeof(pid), KERNEL_HEAP))
            goto restart;
        if(pid == 1)
            break;
        uintptr_t proc2 = jbc_krw_read64(proc, KERNEL_HEAP);
        uintptr_t proc1 = jbc_krw_read64(proc2+8, KERNEL_HEAP);
        if(proc1 != proc)
            goto restart;
        proc = proc2;
    }
    uintptr_t pid1_ucred = jbc_krw_read64(proc+0x40, KERNEL_HEAP);
    uintptr_t pid1_fd = jbc_krw_read64(proc+0x48, KERNEL_HEAP);
    if(jbc_krw_memcpy((uintptr_t)&prison0, pid1_ucred+0x30, sizeof(prison0), KERNEL_HEAP))
        return -1;
    if(jbc_krw_memcpy((uintptr_t)&rootvnode, pid1_fd+0x18, sizeof(rootvnode), KERNEL_HEAP))
    {
        prison0 = 0;
        return -1;
    }
    return 0;
}

uintptr_t jbc_get_prison0(void)
{
    if(!prison0)
        resolve();
    return prison0;
}

uintptr_t jbc_get_rootvnode(void)
{
    if(!rootvnode)
        resolve();
    return rootvnode;
}

static inline int ppcopyout(void* u1, void* u2, uintptr_t k)
{
    return jbc_krw_memcpy((uintptr_t)u1, k, (uintptr_t)u2-(uintptr_t)u1, KERNEL_HEAP);
}

static inline int ppcopyin(const void* u1, const void* u2, uintptr_t k)
{
    return jbc_krw_memcpy(k, (uintptr_t)u1, (uintptr_t)u2-(uintptr_t)u1, KERNEL_HEAP);
}

int jbc_get_cred(struct jbc_cred* ans)
{
    uintptr_t td = jbc_krw_get_td();
    if(!td) return -1;
    uintptr_t proc = jbc_krw_read64(td + 8, KERNEL_HEAP);
    uintptr_t ucred = jbc_krw_read64(proc + 0x40, KERNEL_HEAP);
    uintptr_t fd = jbc_krw_read64(proc + 0x48, KERNEL_HEAP);

    if (ppcopyout(&ans->uid, 1 + &ans->svuid, ucred + 4)
        || ppcopyout(&ans->rgid, 1 + &ans->svgid, ucred + 20)
        || ppcopyout(&ans->prison, 1 + &ans->prison, ucred + 0x30)
        || ppcopyout(&ans->cdir, 1 + &ans->jdir, fd + 0x10)
        || ppcopyout(&ans->sceProcType, 1 + &ans->sceProcCap, ucred + 88))
        return -1;

    return 0;
}

static int jbc_set_cred_internal(const struct jbc_cred* ans)
{
    uintptr_t td = jbc_krw_get_td();
    if(!td) return -1;
    uintptr_t proc = jbc_krw_read64(td + 8, KERNEL_HEAP);
    uintptr_t ucred = jbc_krw_read64(proc + 0x40, KERNEL_HEAP);
    uintptr_t fd = jbc_krw_read64(proc + 0x48, KERNEL_HEAP);

    if (ppcopyin(&ans->uid, 1 + &ans->svuid, ucred + 4)
        || ppcopyin(&ans->rgid, 1 + &ans->svgid, ucred + 20)
        || ppcopyin(&ans->prison, 1 + &ans->prison, ucred + 0x30)
        || ppcopyin(&ans->cdir, 1 + &ans->jdir, fd + 0x10)
        || ppcopyin(&ans->sceProcType, 1 + &ans->sceProcCap, ucred + 88))
        return -1;
    return 0;
}

int jbc_jailbreak_cred(struct jbc_cred* ans)
{
    uintptr_t prison0 = jbc_get_prison0();
    if (!prison0)
        return -1;
    uintptr_t rootvnode = jbc_get_rootvnode();
    if (!rootvnode)
        return -1;


    ans->sceProcCap = 0xffffffffffffffff;
    ans->sceProcType = 0x3801000000000013;
    ans->sonyCred = 0xffffffffffffffff;

    ans->uid = ans->ruid = ans->svuid = ans->rgid = ans->svgid = 0;
    ans->prison = prison0;
    ans->cdir = ans->rdir = ans->jdir = rootvnode;
    return 0;
}

static int jbc_open_this(const struct jbc_cred* cred0, uintptr_t vnode)
{
    if(!vnode)
        return -1;
    struct jbc_cred cred = *cred0;
    if(jbc_jailbreak_cred(&cred)) return -1;
    cred.cdir = cred.rdir = cred.jdir = vnode;
    if(jbc_set_cred_internal(&cred)) return -1;
    int ans = psmtp_jbc_open("/", 0);
    if(jbc_set_cred_internal(cred0)) {if(ans>=0) psmtp_jbc_close(ans);return -1;}
    return ans;
}

static int swap64(uintptr_t p1, KmemKind k1, uintptr_t p2, KmemKind k2)
{
    uintptr_t v1 = jbc_krw_read64(p1, k1);
    uintptr_t v2 = jbc_krw_read64(p2, k2);
    if(ppcopyin(&v2, 1+&v2, p1)
    || ppcopyin(&v1, 1+&v1, p2))
        return -1;
    return 0;
}

static int return0(void)
{
    return 0;
}

static void* fake_vtable[16] = {};

/* Verify the descriptor indirection actually used by the vnode swap against
 * a descriptor opened by the OS, before any credential writes. Canonical
 * pointers alone do not establish a compatible filedesc/file layout. */
static int context_preflight(const struct jbc_cred* old, const struct jbc_cred* next)
{
    uintptr_t td = jbc_krw_get_td();
    if(!td) return -1;
    uintptr_t proc = jbc_krw_read64(td+8, KERNEL_HEAP);
    uintptr_t fd = jbc_krw_read64(proc+0x48, KERNEL_HEAP);
    uintptr_t files = jbc_krw_read64(fd, KERNEL_HEAP);
    if(files<0xffff800000000000 || files>=0xffffffff00000000 || (files&7)) return -1;
    uintptr_t prisons[2] = {old->prison, next->prison};
    for(unsigned i=0;i<2;++i) {
        uint32_t refs=0;
        if(!prisons[i] || (prisons[i]&7)) return -1;
        if(jbc_krw_memcpy((uintptr_t)&refs,prisons[i]+0x14,sizeof(refs),KERNEL_HEAP)
        && jbc_krw_memcpy((uintptr_t)&refs,prisons[i]+0x14,sizeof(refs),KERNEL_TEXT)) return -1;
        if(!refs || refs==UINT32_MAX) return -1;
    }
    int probe=psmtp_jbc_open("/",0);
    if(probe<0) return -1;
    uintptr_t file=jbc_krw_read64(files+(uintptr_t)probe*8,KERNEL_HEAP);
    int valid=file>=0xffff800000000000 && file<0xffffffff00000000 && !(file&7)
        && jbc_krw_read64(file,KERNEL_HEAP)==old->rdir;
    if(psmtp_jbc_close(probe)) valid=0;
    return valid?0:-1;
}

int jbc_set_cred(const struct jbc_cred* newp)
{
    struct jbc_cred old, neww = *newp;
    if(jbc_get_cred(&old))
        return -1;
    if(old.cdir && !neww.cdir)
        neww.cdir = jbc_get_rootvnode();
    if(old.rdir && !neww.rdir)
        neww.rdir = jbc_get_rootvnode();
    if(old.jdir && !neww.jdir)
        neww.jdir = jbc_get_rootvnode();
    if(context_preflight(&old,&neww)) return -1;
    int cdir_fd = jbc_open_this(&old, neww.cdir);
    int rdir_fd = jbc_open_this(&old, neww.rdir);
    int jdir_fd = jbc_open_this(&old, neww.jdir);
    if(cdir_fd<0 || rdir_fd<0 || jdir_fd<0) {
        if(cdir_fd>=0) psmtp_jbc_close(cdir_fd);
        if(rdir_fd>=0) psmtp_jbc_close(rdir_fd);
        if(jdir_fd>=0) psmtp_jbc_close(jdir_fd);
        return -1;
    }
    struct jbc_cred elevated = neww;
    elevated.cdir = old.cdir;
    elevated.jdir = old.jdir;
    elevated.rdir = old.rdir;

    uint32_t rc;
    if(elevated.prison)
    {
        if(jbc_krw_memcpy((uintptr_t)&rc, elevated.prison+0x14, sizeof(rc), KERNEL_HEAP)
        && jbc_krw_memcpy((uintptr_t)&rc, elevated.prison+0x14, sizeof(rc), KERNEL_TEXT))
            return -1;
        if(rc==UINT32_MAX) return -1;
        rc++;
        if(jbc_krw_memcpy(elevated.prison+0x14, (uintptr_t)&rc, sizeof(rc), KERNEL_HEAP)
        && jbc_krw_memcpy(elevated.prison+0x14, (uintptr_t)&rc, sizeof(rc), KERNEL_TEXT))
            return -1;
    }
    if(jbc_set_cred_internal(&elevated))
        return -1;
    if(old.prison)
    {
        if(jbc_krw_memcpy((uintptr_t)&rc, old.prison+0x14, sizeof(rc), KERNEL_HEAP)
        && jbc_krw_memcpy((uintptr_t)&rc, old.prison+0x14, sizeof(rc), KERNEL_TEXT))
            return -1;
        if(!rc) return -1;
        rc--;
        if(jbc_krw_memcpy(old.prison+0x14, (uintptr_t)&rc, sizeof(rc), KERNEL_HEAP)
        && jbc_krw_memcpy(old.prison+0x14, (uintptr_t)&rc, sizeof(rc), KERNEL_TEXT))
            return -1;
    }
    uintptr_t td = jbc_krw_get_td();
    if(!td) return -1;
    uintptr_t proc = jbc_krw_read64(td + 8, KERNEL_HEAP);
    uintptr_t fd = jbc_krw_read64(proc + 0x48, KERNEL_HEAP);
    uintptr_t ofiles = jbc_krw_read64(fd, KERNEL_HEAP);
    int fds[3] = {cdir_fd, rdir_fd, jdir_fd};
    for(int i = 0; i < 3; i++)
    {
        if(fds[i] < 0)
            continue;
        uintptr_t file = jbc_krw_read64(ofiles+8*fds[i], KERNEL_HEAP);
        if(swap64(file, KERNEL_HEAP, fd+0x10+8*i, KERNEL_HEAP))
            return -1;
        if(jbc_krw_read64(file, KERNEL_HEAP) == 0)
        {
            if(!fake_vtable[0])
                for(size_t i = 0; i < sizeof(fake_vtable) / sizeof(fake_vtable[0]); i++)
                    fake_vtable[i] = return0;
            uintptr_t p = (uintptr_t)fake_vtable;
            if(ppcopyin(&p, 1+&p, file+8))
                return -1;
        }
        psmtp_jbc_close(fds[i]);
    }
    return 0;
}
