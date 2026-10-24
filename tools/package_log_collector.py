"""Bundle the Windows read-only log collector; contains no PS4 executable."""
import hashlib
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT/'artifacts/PS-MTP-Launch-Log-Collector'
DEST.mkdir(parents=True, exist_ok=True)
for name in ['Capture-PS4-Launch-Log.cmd', 'Capture-PS4-Existing-Crash.cmd', 'Collect-PS4LaunchLog.ps1']:
    shutil.copyfile(ROOT/'tools'/name, DEST/name)
shutil.copyfile(ROOT/'docs/LAUNCH_LOGS.md', DEST/'START-HERE.md')
shutil.copyfile(ROOT/'LICENSE', DEST/'LICENSE.txt')
contents = sorted(p for p in DEST.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
(DEST/'SHA256SUMS.txt').write_text(''.join(
    hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.name + '\n' for p in contents), encoding='ascii')
archive_path = ROOT/'artifacts/PS-MTP-Launch-Log-Collector.zip'
with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(DEST.iterdir()):
        if path.is_file():
            archive.write(path, DEST.name+'/'+path.name)
with zipfile.ZipFile(archive_path) as archive:
    if archive.testzip() is not None:
        raise SystemExit('Collector ZIP CRC check failed')
    expected = {DEST.name+'/'+p.name for p in DEST.iterdir() if p.is_file()}
    if set(archive.namelist()) != expected:
        raise SystemExit('Collector ZIP file list mismatch')
print('Windows log collector only (no PKG):', archive_path)
print('SHA256:', hashlib.sha256(archive_path.read_bytes()).hexdigest())
