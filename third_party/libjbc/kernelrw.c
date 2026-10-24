/* GoldHEN-only integration: no Mira probing; see NOTICE.txt. */
#include <stdbool.h>
#include "kernelrw.h"

static int k_kcall(void* td, uint64_t** uap)
{
    (void)td;
    uint64_t* args = uap[1];
    args[0] = ((uint64_t(*)(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t, uint64_t))args[0])(args[1], args[2], args[3], args[4], args[5], args[6]);
    return 0;
}

#ifndef PSMTP_TEST_JBC
__asm__("kexec:\nmov $11, %rax\nmov %rcx, %r10\nsyscall\njnc 1f\nneg %rax\n1: ret");
#endif
int64_t kexec(void*, void*);

uint64_t jbc_krw_kcall(uint64_t fn, uint64_t a, uint64_t b, uint64_t c, uint64_t d, uint64_t e, uint64_t f)
{
    uint64_t args[7] = {fn, a, b, c, d, e, f};
    if(kexec(k_kcall, args)) return UINT64_MAX;
    return args[0];
}

#ifndef PSMTP_TEST_JBC
__asm__("k_get_td:\nmov %gs:0, %rax\nret");
extern char k_get_td[];
#else
uint64_t k_get_td(uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t);
#endif

uintptr_t jbc_krw_get_td(void)
{
    uintptr_t td = jbc_krw_kcall((uintptr_t)k_get_td, 0, 0, 0, 0, 0, 0);
    return td>=0xffff800000000000 && td<0xffffffff00000000 ? td : 0;
}

static inline bool check_ptr(uintptr_t p, KmemKind kind)
{
    if(kind == USERSPACE)
        return p < 0x800000000000;
    else if(kind == KERNEL_HEAP)
        return p >= 0xffff800000000000 && p < 0xffffffff00000000;
    else if(kind == KERNEL_TEXT)
        return p >= 0xffffffff00000000 && p < 0xfffffffffffff000;
    else
        return false;
}

#ifndef PSMTP_TEST_JBC
__asm__("k_kcpy:\nmov %rdx, %rcx\nrep movsb\nxor %eax, %eax\nret");
extern char k_kcpy[];
#else
uint64_t k_kcpy(uint64_t,uint64_t,uint64_t,uint64_t,uint64_t,uint64_t);
#endif

int jbc_krw_memcpy(uintptr_t dst, uintptr_t src, size_t sz, KmemKind kind)
{
    if(sz == 0)
        return 0;
    if(sz>UINTPTR_MAX-dst || sz>UINTPTR_MAX-src) return -1;
    bool u1 = check_ptr(dst, USERSPACE) && check_ptr(dst+sz-1, USERSPACE);
    bool ok1 = check_ptr(dst, kind) && check_ptr(dst+sz-1, kind);
    bool u2 = check_ptr(src, USERSPACE) && check_ptr(src+sz-1, USERSPACE);
    bool ok2 = check_ptr(src, kind) && check_ptr(src+sz-1, kind);
    if(!((u1 || ok1) && (u2 || ok2)))
        return -1;
    if(u1 && u2)
        return -1;
    return jbc_krw_kcall((uintptr_t)k_kcpy, dst, src, sz, 0, 0, 0)==0 ? 0 : -1;
}

uint64_t jbc_krw_read64(uintptr_t p, KmemKind kind)
{
    uint64_t ans;
    if(jbc_krw_memcpy((uintptr_t)&ans, p, sizeof(ans), kind))
        return -1;
    return ans;
}

int jbc_krw_write64(uintptr_t p, KmemKind kind, uintptr_t val)
{
    return jbc_krw_memcpy(p, (uintptr_t)&val, sizeof(val), kind);
}
