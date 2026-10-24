"""Drive the production controller/renderer using synthetic devices only."""
import hashlib
import json
import re
from pathlib import Path
import subprocess
from png_tools import write_rgb

ROOT=Path(__file__).resolve().parents[1]
VERSION=re.search(r'#define PSMTP_VERSION "([^"]+)"',(ROOT/'include/psmtp/version.h').read_text()).group(1)
BUILD=ROOT/('build-ps4-'+VERSION)
OUT=BUILD/'visual'
OUT.mkdir(exist_ok=True)
checks=[]
def check(name, condition):
    if not condition: raise AssertionError(name)
    checks.append(name)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
errors=(OUT/'native-host-stderr.txt').open('w')
host=subprocess.Popen([str(BUILD/'ui-host.exe'),str(OUT/'interactive.ppm')],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True,bufsize=1)
def state():
    line=host.stdout.readline()
    if not line: raise RuntimeError('Host stopped: '+(OUT/'native-host-stderr.txt').read_text())
    return json.loads(line)
def press(button):
    host.stdin.write(str(button)+'\n');host.stdin.flush();return state()
def capture(name):
    parts=(OUT/'interactive.ppm').read_bytes().split(b'\n',3)
    write_rgb(OUT/(name+'.png'),1920,1080,parts[3])
try:
    s=state();check('Phone starts in grid',s['view']==1 and not s['list'])
    s=press(1);check('Up reaches toolbar',s['toolbar']==1)
    s=press(8);check('Right focuses list button',s['toolbar']==2)
    s=press(16);check('X selects list view',s['list']==1)
    s=press(8);check('Right focuses sort button',s['toolbar']==3)
    before=s['selected'];writes=s['mtp_writes'];s=press(16)
    check('Sort opens a modal',s['view']==13 and s['menu_index']==0)
    s=press(2);check('Moving through choices does not apply sorting',s['sort']==0 and s['menu_index']==1)
    capture('interactive-sort-picker')
    s=press(32);check('Circle cancels sort without changing mode',s['sort']==0 and s['toolbar']==3)
    for mode in range(1,7):
        s=press(16);check('Sort starts at current choice '+str(mode),s['view']==13 and s['menu_index']==mode-1)
        s=press(2);s=press(16);check('Sort choice applies '+str(mode),s['sort']==mode and s['view']==1)
    s=press(16)
    for i in range(6):s=press(1)
    s=press(16);check('Name sorting can be selected directly',s['sort']==0)
    check('Sorting keeps selected item',s['selected']==before)
    check('Sorting uses no USB metadata reads',s['mtp_writes']==writes)
    s=press(4);s=press(4);s=press(16);check('Grid view selectable from toolbar',not s['list'])
    s=press(2);check('Down returns to file grid',s['toolbar']==0)
    s=press(4);check('Left opens device drawer',s['drawer']==1)
    s=press(2);check('USB device selectable',s['location']==2)
    s=press(2);check('Internal storage selectable',s['location']==1)
    s=press(2);check('Disabled Settings is skipped by navigation',not s['settings'] and s['location']==1)
    capture('interactive-settings-disabled')
    s=press(8);check('Right returns from drawer',not s['drawer'])
    s=press('n');before=s['install_starts']
    s=press(16);check('Native non-PKG X opens only Properties',s['view']==6 and not s['progress'] and s['properties_path'] and s['install_starts']==before)
    capture('interactive-properties-native')
    s=press(32)
    s=press(128)
    for i in range(4):s=press(2)
    check('Paste has a permanent disabled slot',s['view']==7 and s['menu_index']==4 and not s['paste_enabled'])
    capture('interactive-paste-disabled')
    s=press(16);check('Disabled Paste does not execute',s['view']==7 and s['menu_index']==4 and not s['clipboard'])
    s=press(32)
    s=press(128);check('Triangle opens Options',s['view']==7)
    for i in range(5):s=press(2)
    check('Rename reachable in Options',s['menu_index']==5)
    s=press(16);check('Rename opens controller keyboard',s['view']==12 and s['edit_length']>0)
    s=press(512);check('L1 clears name',s['edit_length']==0)
    s=press(16);check('Number row starts with 1',s['edit_length']==1)
    for i in range(11):s=press(8)
    s=press(16);check('Keyboard Backspace tile erases text',s['edit_length']==0)
    s=press(2);s=press(4);s=press(4);s=press(4);s=press(4);s=press(4);s=press(4);s=press(4);s=press(4);s=press(4)
    check('QWERTY letter row is reachable',s['menu_index']==12)
    s=press(16);check('X types selected character',s['edit_length']==1)
    s=press(128);s=press(8);s=press(16);check('Shift and arrows type another character',s['edit_length']==2)
    s=press(64);check('Square erases a character',s['edit_length']==1)
    s=press(1024);check('Adapter failure remains in rename dialog',s['view']==12)
    capture('interactive-rename')
    s=press(32);check('Circle cancels rename',s['view']==2)
    s=press(64);check('Square in browser does not copy',not s['clipboard'])
    s=press(16384);check('R3 in browser does not delete',s['progress']==0)
    s=press(128);s=press(2);s=press(2);s=press(16);check('Options Copy still works',s['clipboard']==1)
    capture('interactive-clipboard')
    # Copy from native storage, return to the retained phone, and paste there.
    s=press(4);s=press(1);s=press(1);s=press(8)
    check('Phone destination is reachable with native clipboard',s['view']==1 and s['clipboard']==1)
    s=press('n');before=s['install_starts']
    s=press(16);check('Phone non-PKG X opens only Properties',s['view']==6 and not s['progress'] and s['properties_path'] and s['install_starts']==before)
    capture('interactive-properties-phone')
    s=press(32)
    s=press(128)
    for i in range(4):s=press(2)
    check('Paste keeps its fixed slot when enabled',s['menu_index']==4 and s['paste_enabled'])
    capture('interactive-paste-enabled')
    s=press(16);check('Phone Paste opens a transfer review',s['view']==9)
    capture('interactive-phone-upload-review')
    s=press(32);check('Phone Paste review can be cancelled',s['view']==1)
    for error,label in [(-13,'insufficient-space'),(-14,'unknown-space')]:
        host.stdin.write('s'+str(error)+'\n');host.stdin.flush();s=state()
        s=press(128)
        for i in range(4):s=press(2)
        s=press(16);check('Pre-transfer warning '+label,s['view']==14)
        capture('interactive-'+label)
        s=press(16);check('Storage warning closes to browser '+label,s['view']==1)
    host.stdin.write('s0\n');host.stdin.flush();s=state()
    # Synthetic PKGs exercise the real X -> confirm -> start controller flow.
    for kind,label in [(0,'phone'),(2,'usb'),(1,'internal')]:
        if kind==2:
            s=press(4);s=press(2);s=press(8)
        elif kind==1:
            s=press(4);s=press(2);s=press(8)
        check('Install source reachable '+label,s['location']==kind)
        s=press('k');before=s['install_starts'];closed=s['install_closes']
        s=press(16);check('X on PKG opens install confirmation '+label,s['view']==15 and s['install_starts']==before)
        capture('interactive-install-'+label)
        s=press(32);check('Install cancellation starts nothing '+label,s['view']==(1 if kind==0 else 2) and s['install_starts']==before and s['install_closes']==closed+1)
        if kind==0:
            for cancel_phase in (1,2):
                s=press(16);s=press(16)
                check('Phone copy precedes registration '+str(cancel_phase),s['view']==3 and s['phase']==1 and s['install_starts']==before)
                if cancel_phase==2:s=press(0)
                s=press(32);closed+=1
                check('Circle cancels phone copy/verification without installer '+str(cancel_phase),s['view']==1 and s['install_starts']==before and s['install_closes']==closed+1)
        s=press(16);s=press(16)
        if kind==0:
            check('Confirmed phone package copies before installation',s['view']==3 and s['phase']==1 and s['install_starts']==before)
            capture('interactive-install-copy')
            s=press(0);check('Phone package verifies before installation',s['view']==3 and s['phase']==2 and s['install_starts']==before)
            capture('interactive-install-verify')
            s=press(0);check('Phone package publishes before installation',s['view']==3 and s['phase']==4 and s['install_starts']==before)
            s=press(0)
        check('Confirm opens installer progress '+label,s['view']==16)
        s=press(0);check('Confirmed package starts exactly once '+label,s['view']==16 and s['install_starts']==before+1)
        check('Installer reports incremental progress '+label,s['install_percent']==25)
        for target in (50,75,100):
            s=press(0);check('Installer live progress '+label+' '+str(target),s['view']==16 and s['install_percent']==target)
        s=press(0);check('Success popup follows completion '+label,s['view']==14 and s['install_closes']==closed+2 and s['notice_clean'])
        capture('interactive-install-success-'+label)
        s=press(16);check('Success popup returns to browser '+label,s['view']==(1 if kind==0 else 2))
    # New Folder is reachable even without selecting an existing item.
    s=press(128)
    for i in range(1):s=press(2)
    s=press(16);check('New Folder opens keyboard',s['view']==12 and s['edit_length']==10)
    capture('interactive-new-folder')
    s=press(32);check('New Folder can be cancelled',s['view']==2)
    s=press(128)
    for i in range(8):s=press(2)
    s=press(16);check('Options Exit closes host',s.get('exited') is True)
    host.wait(timeout=10);errors.close()
    check('Sanitizer host has no stderr',not (OUT/'native-host-stderr.txt').read_text().strip())
    report={'checks':checks,'host_sha256':sha(BUILD/'ui-host.exe'),'verifier_sha256':sha(Path(__file__)),'hardware_tested':False,'notes':'Actual C controller and renderer; synthetic storage. Native rename is tested separately through syscall simulation.'}
    (OUT/'native-functional-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(checks),'production controller/render checks')
finally:
    if host.poll() is None:host.terminate();host.wait(timeout=10)
    errors.close()
