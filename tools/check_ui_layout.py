"""Compare reference fixtures to 0.8.0 outside explicitly changed icon/shortcut areas."""
import json
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
build=ROOT/'build-ps4-0.8.1'
visual=build/'visual';visual.mkdir(exist_ok=True)
results={}
for name in ['reference-grid','reference-options','reference-transfer','reference-list']:
    before=Image.open(ROOT/'build-ps4-0.8.0'/(name+'.png')).convert('RGB')
    after=Image.open(build/(name+'.png')).convert('RGB')
    mask=Image.new('L',before.size,255);draw=ImageDraw.Draw(mask)
    def allow(x,y,w,h):draw.rectangle((x,y,x+w-1,y+h-1),fill=0)
    allow(1514,48,176,39)  # Platform controller artwork, same existing box.
    for row in range(3): allow(56,164+row*82+12,40,52)
    allow(56,462,40,40);allow(411,163,31,32)
    allow(1600,235,192,156)
    if name=='reference-list':
        for row in range(12):allow(419,267+row*39,29,28)
    else:
        for index in range(8):allow(466+(index%4)*264,257+(index//4)*232,124,101)
        allow(752,713,80,108)
    if name=='reference-options':
        for row in range(6):allow(666,302+row*67,31,33)
    if name!='reference-transfer':allow(588,979,365,40)
    difference=ImageChops.difference(before,after)
    red,green,blue=difference.split()
    changed=ImageChops.lighter(ImageChops.lighter(red,green),blue).point(lambda v:255 if v else 0)
    outside=ImageChops.multiply(changed,mask)
    count=outside.histogram()[255]
    results[name]={'pixels_changed_outside_allowed_regions':count,'passed':count==0}
    if count:outside.save(visual/(name+'-unexpected-layout-changes.png'))
report={'baseline':'0.8.0 native reference fixtures','candidate':'0.8.1 native reference fixtures',
        'notes':'Masks cover only icon drawing boxes and the two removed shortcut hints. Typography, panel geometry, card boundaries, media thumbnails and other controls are compared exactly.',
        'screens':results}
(visual/'layout-preservation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if any(not v['passed'] for v in results.values()):raise SystemExit(1)
