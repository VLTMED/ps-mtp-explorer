"""Compare preserved 0.8.1 and current renderer on identical host fixtures."""
from pathlib import Path
import json
import re
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
baseline=ROOT/'.research/renderer-baseline-0.8.1'
baseline.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'artifacts/ps-mtp-explorer-0.8.1-preview/application-source.zip') as archive:
    for name in archive.namelist():
        if name.startswith(('src/','include/','tests/reference_fixture.h')):
            path=baseline/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(name))
report={'hardware_tested':False,'configuration':'Same PC, Zig C -O2, no sanitizers, same reference fixture; 120 warm frames per case. Not PS4 FPS.','results':{}}
sources=['src/ps4/ui_font.c','src/ps4/ui_draw.c','src/ps4/console_render.c','src/sha256.c','src/locations.c','src/ui_format.c','src/diag_log.c','src/mtp.c','src/navigator.c']
current=re.search(r'#define PSMTP_VERSION "([^"]+)"',(ROOT/'include/psmtp/version.h').read_text()).group(1)
for version,root in [('0.8.1',baseline),(current,ROOT)]:
    exe=ROOT/('build-ps4-'+current)/('benchmark-'+version+'.exe')
    files=[root/s for s in sources]
    if version!='0.8.1':
        files.extend([root/'src/name.c',root/'src/keyboard.c'])
    command=[str(ROOT/'.tools/ziglang/zig.exe'),'cc','-std=c99','-O2','-I'+str(root/'include'),'-I'+str(root/'src/ps4'),'-I'+str(root/'tests'),'-isystem',str(ROOT/'.tools/sdk/OpenOrbis/PS4Toolchain/include/stb')]+[str(p) for p in files]+[str(ROOT/'tests/benchmark_render.c'),'-o',str(exe)]
    subprocess.run(command,check=True,cwd=ROOT)
    report['results'][version]={mode:json.loads(subprocess.check_output([str(exe),mode],cwd=ROOT,text=True)) for mode in ['grid','menu']}
out=ROOT/('build-ps4-'+current)/'visual/renderer-benchmark.json';out.parent.mkdir(exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
