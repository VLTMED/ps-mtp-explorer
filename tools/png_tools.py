"""Tiny RGB PNG writer for generated diagnostic assets/previews (standard library)."""
import struct
import zlib

def write_rgb(path, width, height, rgb):
    if len(rgb) != width * height * 3:
        raise ValueError('RGB byte count does not match dimensions')
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag+data))
    raw = b''.join(b'\0'+rgb[y*width*3:(y+1)*width*3] for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB',width,height,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))

def diagnostic_icon(path):
    width = height = 512
    rgb = bytearray(bytes([13,19,25]) * width * height)
    def rect(x,y,w,h,color):
        for row in range(y,y+h):
            rgb[(row*width+x)*3:(row*width+x+w)*3] = bytes(color)*w
    rect(24,24,464,8,(255,217,102)); rect(24,480,464,8,(255,217,102))
    rect(96,100,320,185,(83,192,170)); rect(112,116,288,153,(20,32,40))
    rect(240,285,32,32,(83,192,170)); rect(192,317,128,12,(83,192,170))
    glyphs={'M':['10001','11011','10101','10001','10001','10001','10001'],
            'T':['11111','00100','00100','00100','00100','00100','00100'],
            'P':['11110','10001','10001','11110','10000','10000','10000']}
    for j,ch in enumerate('MTP'):
        for y,row in enumerate(glyphs[ch]):
            for x,bit in enumerate(row):
                if bit=='1': rect(132+j*90+x*12,363+y*12,12,12,(255,217,102))
    write_rgb(path,width,height,rgb)


def explorer_icon(path):
    """Original folder/phone mark, supersampled at 2x for smooth launcher edges."""
    import math
    scale=2; side=512*scale
    rgb=bytearray(side*side*3)
    for y in range(side):
        color=(10+int(5*(1-y/side)),16+int(9*(1-y/side)),25+int(16*(1-y/side)))
        rgb[y*side*3:(y+1)*side*3]=bytes(color)*side
    def rounded(x,y,w,h,r,color):
        x*=scale;y*=scale;w*=scale;h*=scale;r*=scale
        for row in range(h):
            dy=r-row if row<r else row-(h-r-1) if row>=h-r else 0
            inset=r-int(math.sqrt(max(0,r*r-dy*dy))) if dy else 0
            start=((y+row)*side+x+inset)*3
            rgb[start:start+(w-2*inset)*3]=bytes(color)*(w-2*inset)
    rounded(65,145,382,255,29,(5,10,16))
    rounded(83,117,146,93,19,(91,225,195))
    rounded(65,159,382,232,24,(91,225,195))
    rounded(80,181,352,194,15,(17,32,43))
    rounded(208,207,96,145,15,(237,243,251))
    rounded(218,219,76,108,7,(26,49,61))
    rounded(244,338,24,5,2,(26,49,61))
    output=bytearray(512*512*3)
    for y in range(512):
        for x in range(512):
            for c in range(3):
                output[(y*512+x)*3+c]=sum(rgb[((y*2+dy)*side+x*2+dx)*3+c] for dy in range(2) for dx in range(2))//4
    write_rgb(path,512,512,output)
