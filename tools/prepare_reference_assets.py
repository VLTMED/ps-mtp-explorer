"""Extract small supplied UI assets; never use a screen capture as a UI background.

Run with the bundled Python/Pillow runtime. Originals stay untouched. The C
renderer consumes the generated RGBA arrays; PNG files remain editable assets.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--resources', type=Path, default=ROOT.parent/'psmtpResource')
args = parser.parse_args()
source = args.resources.resolve()
output = ROOT/'assets/reference'
output.mkdir(parents=True, exist_ok=True)
screen = Image.open(source/'1792455114194.jpg').convert('RGB')
options = Image.open(source/'1792496064015.jpg').convert('RGB')
scale = screen.width/2048
manifest = {'source':str(source), 'references':{}, 'assets':{}}
for p in sorted(source.rglob('*')):
    if p.is_file():
        im=Image.open(p)
        manifest['references'][p.name]={'size':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}

assets=[]
def asset(name, box, size, mode='white', original=screen):
    vector=ROOT/'assets/icons'/(name+'.svg')
    if vector.exists():
        # Clean icons take precedence over the older AI screenshot excerpts.
        # Run prepare_clean_icons.mjs to render changes to these SVG sources.
        path=output/(name+'.png')
        if not path.is_file(): raise SystemExit('Render the clean vector icons first: '+str(vector))
        crop=Image.open(path).convert('RGBA')
        manifest['assets'][name]={'source':vector.relative_to(ROOT).as_posix(),'size':list(crop.size),
            'mode':'clean-vector','svg_sha256':hashlib.sha256(vector.read_bytes()).hexdigest(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        assets.append((name,crop));return
    crop=original.crop(tuple(round(v*scale) for v in box)).convert('RGBA')
    if mode in ('white','gold'):
        pixels=[]
        for r,g,b,_ in crop.getdata():
            if mode=='gold':
                alpha=255 if r>70 and r>b*1.5 and g>b*1.3 else 0
                pixels.append((r,g,b,alpha))
            else:
                # The reference has a dark surface behind these isolated marks.
                base=80 if name=='phone' else 48
                a=max(0,min(255,round((max(r,g,b)-base)*255/(223-base))))
                pixels.append((238,231,231,a))
        crop.putdata(pixels)
    elif mode=='document':
        # Remove only the edge-connected dark card around the supplied paper.
        # Keep enclosed ink/shading intact and soften the antialiased outline.
        pixels=crop.load(); pending=[(x,y) for x in range(crop.width) for y in (0,crop.height-1)]
        pending += [(x,y) for y in range(crop.height) for x in (0,crop.width-1)]
        visited=set()
        while pending:
            x,y=pending.pop()
            if (x,y) in visited or not (0<=x<crop.width and 0<=y<crop.height): continue
            visited.add((x,y));r,g,b,a=pixels[x,y]
            if max(r,g,b)>110: continue
            pixels[x,y]=(r,g,b,0)
            pending.extend(((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
    crop=crop.resize(size,Image.Resampling.LANCZOS)
    path=output/(name+'.png');crop.save(path)
    manifest['assets'][name]={'source': '1792496064015.jpg' if original is options else '1792455114194.jpg',
        'box_display_2048':list(box),'size':list(size),'mode':mode,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assets.append((name,crop))

asset('wordmark',(68,43,675,94),(570,48))
asset('platform',(1616,48,1802,89),(176,39))
asset('folder',(1708,246,1910,411),(192,156),'gold')
asset('phone',(62,192,101,244),(34,46))
asset('usb',(62,281,99,330),(34,44))
asset('drive',(56,370,104,415),(40,40))
asset('settings',(56,491,107,541),(40,40))
asset('home',(436,170,475,211),(34,35))
asset('copy',(708,391,753,439),(36,39),original=options)
asset('move',(708,460,753,506),(36,38),original=options)
asset('rename',(708,529,753,576),(36,38),original=options)
asset('delete',(708,601,753,649),(36,39),original=options)
asset('info',(706,676,753,724),(39,40),original=options)
asset('document',(788,758,883,887),(81,110),'document')
asset('thumb_pkg',(490,754,644,885),(178,132),'rgba')
asset('thumb_image',(1000,754,1226,885),(218,132),'rgba')
asset('thumb_video',(1288,754,1516,885),(218,132),'rgba')

icon=Image.open(source/'app icon.jpg').convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
icon.save(output/'icon0.png')
manifest['assets']['icon0']={'source':'app icon.jpg','size':[512,512], 'sha256':hashlib.sha256((output/'icon0.png').read_bytes()).hexdigest()}
header='/* Generated from supplied small assets. See assets/reference/provenance.json. */\n'
header+='typedef struct {int w,h;const unsigned char *rgba;} psmtp_ui_asset;\n'
for name,im in assets:
    data=im.tobytes()
    header+='static const unsigned char ui_'+name+'_bytes[]={\n'
    header+=''.join(','.join(str(v) for v in data[i:i+40])+',\n' for i in range(0,len(data),40))+'};\n'
    header+=f'static const psmtp_ui_asset ui_{name}={{{im.width},{im.height},ui_{name}_bytes}};\n'
(ROOT/'src/ps4/reference_assets.inc').write_text(header,encoding='ascii')
(output/'provenance.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('Prepared',len(assets),'small RGBA assets and launcher icon; source images preserved')
