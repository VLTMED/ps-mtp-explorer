#include "ui_font.h"
#include "psmtp/locale_ar.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>
#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wunused-function"
#endif
#define STB_TRUETYPE_IMPLEMENTATION
#define STBTT_STATIC
#include <stb_truetype.h>
#if defined(__clang__)
#pragma clang diagnostic pop
#endif
#include "font_data.inc"

#define GLYPHS 768
#define TEXT_CAPACITY 2048
typedef struct { uint32_t code; int px,w,h,x,y,advance,font_id; uint64_t used; unsigned char *alpha; } glyph;
static struct {
    stbtt_fontinfo latin,arabic;
    glyph cache[GLYPHS];
    uint64_t clock;
    int ready;
} font;
static unsigned quick[2048];

static int arabic_codepoint(uint32_t c) {
    return (c >= 0x0590 && c <= 0x08ff) ||
           (c >= 0xfb1d && c <= 0xfdff) ||
           (c >= 0xfe70 && c <= 0xfeff) ||
           (c >= 0x1ee00 && c <= 0x1eeff);
}

int psmtp_font_init(void) {
    if(font.ready) return 0;
    if(!stbtt_InitFont(&font.latin,psmtp_font_data,0) ||
       !stbtt_InitFont(&font.arabic,psmtp_arabic_font_data,0)) return -1;
    font.ready=1;
    return 0;
}

void psmtp_font_close(void) {
    unsigned i;
    for(i=0;i<GLYPHS;++i) free(font.cache[i].alpha);
    memset(&font,0,sizeof(font));
    memset(quick,0,sizeof(quick));
}

static glyph *lookup(uint32_t code,int px) {
    unsigned i,slot=0,hash;
    int advance,left,index,font_id=arabic_codepoint(code)?1:0;
    float scale;
    stbtt_fontinfo *face;
    glyph *g;
    if(!font.ready && psmtp_font_init()) return NULL;
    face=font_id?&font.arabic:&font.latin;
    hash=(code*31u+(unsigned)px*131u+(unsigned)font_id*977u)%2048;
    if(quick[hash]) {
        g=&font.cache[quick[hash]-1];
        if(g->used && g->code==code && g->px==px && g->font_id==font_id) {
            g->used=++font.clock;
            return g;
        }
    }
    for(i=0;i<GLYPHS;++i) {
        if(font.cache[i].used && font.cache[i].code==code &&
           font.cache[i].px==px && font.cache[i].font_id==font_id) {
            font.cache[i].used=++font.clock;
            quick[hash]=i+1;
            return &font.cache[i];
        }
        if(font.cache[i].used<font.cache[slot].used) slot=i;
    }
    g=&font.cache[slot];
    free(g->alpha);
    memset(g,0,sizeof(*g));
    index=stbtt_FindGlyphIndex(face,(int)code);
    if(!index) index=stbtt_FindGlyphIndex(face,0xfffd);
    scale=stbtt_ScaleForMappingEmToPixels(face,(float)px);
    stbtt_GetGlyphHMetrics(face,index,&advance,&left);
    g->alpha=stbtt_GetGlyphBitmap(face,scale,scale,index,&g->w,&g->h,&g->x,&g->y);
    g->advance=(int)(advance*scale+0.5f);
    g->code=code;g->px=px;g->font_id=font_id;g->used=++font.clock;
    quick[hash]=slot+1;
    return g;
}

static int visual_width(const uint32_t *visual,size_t count,int px) {
    size_t i;
    int width=0;
    for(i=0;i<count;++i) {
        glyph *g=lookup(visual[i],px);
        if(g) width+=g->advance;
    }
    return width;
}

int psmtp_font_width(const char *s,int px) {
    uint32_t visual[TEXT_CAPACITY];
    size_t count=psmtp_text_visual(s,visual,TEXT_CAPACITY,NULL);
    return visual_width(visual,count,px);
}

static uint32_t blend(uint32_t dst,uint32_t src,unsigned a) {
    unsigned inv=255-a;
    return 0xff000000u|(((dst&255)*inv+(src&255)*a+127)/255)|
        (((((dst>>8)&255)*inv+(src>>8&255)*a+127)/255)<<8)|
        (((((dst>>16)&255)*inv+(src>>16&255)*a+127)/255)<<16);
}

static int draw_one(uint32_t *frame,int x,int y,int px,int max_width,int box_left,
                    uint32_t code,uint32_t color,int *advance_out) {
    glyph *g=lookup(code,px);
    int i,j,baseline=y+px;
    if(!g || x-box_left+g->advance>max_width) return 0;
    for(j=0;j<g->h;++j) {
        int yy=baseline+g->y+j;
        if(yy<0 || yy>=1080) continue;
        for(i=0;i<g->w;++i) {
            int xx=x+g->x+i;
            unsigned a;
            if(xx<0 || xx>=1920 || xx>=box_left+max_width) continue;
            a=g->alpha?g->alpha[j*g->w+i]:0;
            if(a) frame[yy*1920+xx]=blend(frame[yy*1920+xx],color,a);
        }
    }
    if(advance_out) *advance_out=g->advance;
    return 1;
}

void psmtp_font_draw(uint32_t *frame,int x,int y,int px,int max_width,
                     const char *s,uint32_t color) {
    uint32_t visual[TEXT_CAPACITY];
    size_t count,i,first;
    int rtl=0,width,ellipsis=0,advance,box_left=x,cursor=x;
    if(!frame || max_width<=0) return;
    count=psmtp_text_visual(s,visual,TEXT_CAPACITY,&rtl);
    if(!count) return;
    width=visual_width(visual,count,px);
    if(width<=max_width) {
        if(rtl) cursor+=max_width-width;
        for(i=0;i<count;++i) {
            if(!draw_one(frame,cursor,y,px,max_width,box_left,visual[i],color,&advance)) return;
            cursor+=advance;
        }
        return;
    }
    {
        glyph *dot=lookup('.',px);
        if(dot) ellipsis=dot->advance*3;
    }
    if(rtl) {
        int used=0,remaining=max_width-(ellipsis<=max_width?ellipsis:0);
        first=count;
        while(first) {
            glyph *g=lookup(visual[first-1],px);
            int next=g?g->advance:0;
            if(used+next>remaining) break;
            used+=next;--first;
        }
        if(ellipsis<=max_width) for(i=0;i<3;++i) {
            if(draw_one(frame,cursor,y,px,max_width,box_left,'.',color,&advance)) cursor+=advance;
        }
        for(i=first;i<count;++i) {
            if(!draw_one(frame,cursor,y,px,max_width,box_left,visual[i],color,&advance)) break;
            cursor+=advance;
        }
    } else {
        int used=0,remaining=max_width-(ellipsis<=max_width?ellipsis:0);
        first=0;
        while(first<count) {
            glyph *g=lookup(visual[first],px);
            int next=g?g->advance:0;
            if(used+next>remaining) break;
            used+=next;++first;
        }
        for(i=0;i<first;++i) {
            if(!draw_one(frame,cursor,y,px,max_width,box_left,visual[i],color,&advance)) break;
            cursor+=advance;
        }
        if(ellipsis<=max_width) for(i=0;i<3;++i) {
            if(draw_one(frame,cursor,y,px,max_width,box_left,'.',color,&advance)) cursor+=advance;
        }
    }
}
