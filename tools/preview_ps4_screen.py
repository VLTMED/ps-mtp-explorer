"""Render the shared TV console on the host. Does not invoke any PS4 APIs."""
import argparse
import os
from pathlib import Path
import subprocess
from png_tools import write_rgb
from embed_font import embed
embed()

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--sdk', default=str(ROOT/'.tools/sdk/OpenOrbis/PS4Toolchain'))
parser.add_argument('--output', default=str(ROOT/'build-ps4'))
parser.add_argument('--production', action='store_true')
args=parser.parse_args()
output=Path(args.output).resolve(); output.mkdir(exist_ok=True)
zig=ROOT/'.tools/ziglang'/('zig.exe' if os.name=='nt' else 'zig')
exe=output/('screen-preview.exe' if os.name=='nt' else 'screen-preview')
subprocess.run([str(zig),'cc','-std=c99','-O1','-g','-fsanitize=address,undefined',
    *(['-DPSMTP_PRODUCTION=1'] if args.production else []),
    '-I'+str(ROOT/'include'),'-I'+str(ROOT/'src/ps4'),'-I'+str(ROOT/'tests'),'-isystem',str(Path(args.sdk)/'include/stb'),
    str(ROOT/'src/pkg.c'),str(ROOT/'src/transfer_meter.c'),str(ROOT/'src/keyboard.c'),str(ROOT/'src/metadata.c'),str(ROOT/'src/ps4/ui_font.c'),str(ROOT/'src/ps4/ui_draw.c'),str(ROOT/'src/sha256.c'),str(ROOT/'src/locations.c'),str(ROOT/'src/ui_format.c'),str(ROOT/'src/diag_log.c'),str(ROOT/'src/name.c'),str(ROOT/'src/mtp.c'),str(ROOT/'src/navigator.c'),str(ROOT/'src/ps4/console_render.c'),str(ROOT/'tests/preview_screen.c'),
    '-o',str(exe)],check=True,cwd=ROOT)
scenarios=[('install-phone','install-phone-preview'),('install-internal','install-internal-preview'),('install-usb','install-usb-preview'),('install-progress','install-progress-preview'),('rate-steady','transfer-speed-preview'),('rate-warmup','transfer-speed-warmup-preview'),('rate-stall','transfer-speed-stall-preview'),('verify','verification-status-preview'),('verify-end','verification-status-end-preview'),('space-warning','insufficient-space-preview'),('sort','sort-options-preview'),('settings-audio','settings-audio-preview'),('rename-backspace','keyboard-backspace-preview'),('rename','rename-preview'),('toolbar','toolbar-preview'),('media-pkg','package-metadata-preview'),('media-photo','photo-metadata-preview'),('media-properties','metadata-properties-preview'),('browser','browser-preview'),('long-name','long-name-preview'),('empty','browser-empty-preview'),('local','internal-preview'),
 ('usb','usb-preview'),('drawer','device-drawer-preview'),('many-devices','many-devices-preview'),
 ('no-phone','no-phone-preview'),('local-empty','usb-empty-preview'),('loading','folder-loading-preview'),
 ('menu','options-menu-preview'),('controls','controller-guide-preview'),('confirm','copy-confirm-preview'),('copy','copy-progress-preview'),
 ('prepare','copy-prepare-preview'),('logs','diagnostics-preview'),('folder','folder-copy-preview'),
 ('scan','folder-scan-preview'),('details','file-details-preview'),('local-error','storage-error-preview'),
 ('font-stress','font-stress-preview'),('paste-review','paste-review-preview'),('move-review','move-review-preview'),('delete-review','delete-review-preview'),('delete-progress','delete-progress-preview'),('clipboard','clipboard-browser-preview'),('actions-phone','phone-actions-preview'),('operation-scan','operation-scan-preview'),('reference','reference-grid'),('reference-menu','reference-options'),('reference-progress','reference-transfer'),('reference-list','reference-list'),('reference-settings','reference-settings'),('reference-drawer-settings','reference-drawer-settings')]
import hashlib,json
for mode,name in scenarios:
    ppm=output/(name+'.ppm')
    subprocess.run([str(exe),str(ppm),mode],check=True,cwd=ROOT)
    data=ppm.read_bytes().split(b'\n',3);width,height=map(int,data[1].split())
    write_rgb(output/(name+'.png'),width,height,data[3])
    print('Host-only UI preview:',output/(name+'.png'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'hardware_tested':False,'sanitizers':True,'scenarios':[name+'.png' for _,name in scenarios],
 'images_sha256':{name+'.png':sha(output/(name+'.png')) for _,name in scenarios},
 'sources_sha256':{name:sha(ROOT/name) for name in ['src/pkg.c','include/psmtp/pkg.h','src/transfer_meter.c','include/psmtp/transfer_meter.h','src/ps4/package_install.c','src/ps4/package_install.h','include/psmtp/keyboard.h','src/keyboard.c','src/copy.c','src/ps4/copy_file.c','src/ps4/device_audio.c','include/psmtp/metadata.h','include/psmtp/name.h','include/psmtp/ui_format.h','src/metadata.c','src/ps4/preview.c','src/ps4/main.c','src/ps4/file_ops.c','src/name.c','src/ps4/console_render.c','src/ps4/ui_font.c','src/ps4/ui_draw.c','src/ps4/reference_assets.inc','src/ps4/font_data.inc','tests/reference_fixture.h','include/psmtp/version.h','src/locations.c','tests/preview_screen.c','src/ps4/console_render.h','src/ps4/file_store.h','include/psmtp/mtp.h','include/psmtp/locations.h','include/psmtp/navigator.h']}}
(output/'ui-preview-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
