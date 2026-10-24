"""Build the real controller/renderer with mock adapters for browser QA."""
import ast
import argparse
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[1]
common=ast.literal_eval(re.search(r'common = (\[.*\])',(ROOT/'tools/build_host.py').read_text()).group(1))
version=re.search(r'#define PSMTP_VERSION "([^"]+)"',(ROOT/'include/psmtp/version.h').read_text()).group(1)
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=ROOT/('build-ps4-'+version))
parser.add_argument('--production',action='store_true')
args=parser.parse_args()
build=args.output.resolve()
build.mkdir(exist_ok=True)
cmd=[str(ROOT/'.tools/ziglang/zig.exe'),'cc','-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-function',
     '-fsanitize=address,undefined','-Iinclude','-Itests','-Isrc/ps4','-isystem',str(ROOT/'.tools/sdk/OpenOrbis/PS4Toolchain/include/stb')]
cmd+=common+['src/ps4/ui_font.c','src/ps4/ui_draw.c','src/ps4/console_render.c','tests/host_explorer.c','-o',str(build/'ui-host.exe')]
if args.production:cmd+=['-DPSMTP_PRODUCTION=1']
subprocess.run(cmd,cwd=ROOT,check=True)
print('Built synthetic-device controller/renderer host:',build/'ui-host.exe')
