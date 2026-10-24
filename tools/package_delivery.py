"""Create a labeled local test bundle after build, extraction and format checks."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile
from inspect_ps4 import elf, fake_self, converted_image, application_exit_imports
from ps4_runtime import runtime_inventory

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build',default=str(ROOT/'build-ps4'))
args=parser.parse_args()
BUILD=Path(args.build).resolve()
SDK=ROOT/'.tools/sdk/OpenOrbis/PS4Toolchain'

def sha(path):
    with Path(path).open('rb') as source: return hashlib.file_digest(source,'sha256').hexdigest()

report=json.loads((BUILD/'build-report.json').read_text())
release=report['release']
DEST=ROOT/('artifacts/ps-mtp-explorer-'+release+'-preview')
DEST.mkdir(parents=True,exist_ok=True)
if not report.get('package',{}).get('round_trip_verified'):
    raise SystemExit('A validated package build is required first')
for name,digest in report['sources_sha256'].items():
    if sha(ROOT/name)!=digest: raise SystemExit('Source changed since build: '+name)
runtime_inventory(BUILD/'package', report['runtime_modules'])
runtime_inventory(BUILD/'verified-extract/uroot', report['runtime_modules'])
raw=BUILD/(report['package']['content_id']+'.pkg')
if sha(raw)!=report['package']['sha256']: raise SystemExit('PKG changed since validation')
structure={'elf':elf(BUILD/'psmtp.elf',sdk=SDK),'oelf':elf(BUILD/'psmtp.oelf',True),
           'self':fake_self(BUILD/'package/eboot.bin'),
           'conversion':converted_image(BUILD/'psmtp.oelf',BUILD/'package/eboot.bin'),'hardware_tested':False}
structure['exit_import_check']=application_exit_imports(structure['elf']['imports'])
(BUILD/'structure-report.json').write_text(json.dumps(structure,indent=2)+'\n')
sdk_release=json.loads((ROOT/'.tools/downloads/openorbis-release.json').read_text())
provenance={'date':'2026-10-20','release':release,'experimental':True,'hardware_tested':False,
    'sdk_release':sdk_release['html_url'],'sdk_commit':'b458dfd9d2f5c40aa249b127c9b9b4488afdc686',
    'sdk_asset_sha256':'3c7cd5bb593ca74fa1c13fd59f3938dc0fc07985167f7275063019e63abe4526',
    'compiler':report['compiler_version'],'linker':report['linker_version'],
    'compiler_sha256':report['compiler_sha256'],'linker_sha256':report['linker_sha256'],
    'compiler_archive_sha256':'94af030060d88cc17e9f00ef1663ebdc1126b35e16bebdfa1e807984b70abd8f',
    'compiler_archive_source':'https://github.com/llvm/llvm-project/releases/download/llvmorg-18.1.8/LLVM-18.1.8-win64.exe',
    'pkgtool':'0.2.231.0 on .NET 9.0.19',
    'sdk_files_sha256':report['sdk_files_sha256'],'sources_sha256':report['sources_sha256'],
    'elf':report['elf'],'package':report['package'],'conversion':structure['conversion'],
    'runtime_modules':report['runtime_modules'],
    'host_tests':'23891 core/label/event/waveform checks plus 20000 inputs; 17236 production-filesystem-adapter checks; 65 process-access guards; 195 production libjbc context-model, 254 production USB-runtime, 71 production explorer/controller and 345 production audio lifecycle assertions under ASan/UBSan with simulated calls. Fourteen Python regression tests pass.',
    'previous_release':'0.8.0 retained. 0.8.1 replaces distorted pictograms, fixes exclusive drawer focus and removes Square/R3 shortcuts. Sound troubleshooting remains deferred.',
    'renderer':'Native 1920x1080 Noto Sans Light outlines; clean authored SVG icons; 44 Playwright checks including pixel assertions for exclusive drawer focus; 34 guarded sanitizer renderer scenarios. Four baseline fixture comparisons find zero changed pixels outside icon/removed-shortcut regions. Final evidence records preview source, host and package hashes. New controller/rendering changes await console testing.',
    'discovery_phone_names':report.get('discovery_phone_names',False),'device_connection_chimes':report.get('device_connection_chimes',False),
    'automatic_device_watch':report.get('automatic_device_watch',False),'device_poll_ms':report.get('device_poll_ms'),'retained_phone_session':report.get('retained_phone_session',False),'loading_delay_ms':report.get('loading_delay_ms'),
    'process_filesystem_access':report.get('process_filesystem_access',False),'access_profile':report.get('access_profile'),'libjbc_commit':report.get('libjbc_commit'),'implementation_phase':3,'phase_2_hardware_verified':False,'phase_3_complete':False,
    'clipboard_operations':report.get('clipboard_operations',False),'phone_to_native_paste':report.get('phone_to_native_paste',False),'native_copy_move_delete':report.get('native_copy_move_delete',False),'phone_delete':report.get('phone_delete',False),'direct_usb_probe':report.get('direct_usb_probe',False),
    'device_drawer':report.get('device_drawer',False),
    'mounted_usb_browsing':report.get('mounted_usb_browsing',False),
    'internal_browsing':report.get('internal_browsing',False),
    'modern_explorer_ui':report.get('modern_explorer_ui',False),
    'recursive_folder_copy':report.get('recursive_folder_copy',False),
    'folder_shared_reserve':report.get('folder_shared_reserve',False),
    'outline_font':report.get('outline_font'),
    'exit_import_check':structure['exit_import_check'],'usb_tests_enabled':report['usb_tests_enabled'],
    'interactive_browser_enabled':report.get('interactive_browser_enabled',False),'mtp_tests_enabled':report.get('mtp_tests_enabled',False),'usbd_review_sha256':report.get('usbd_review_sha256'),
    'copy_staging_directory':report.get('copy_staging_directory'), 'copy_readable_output':report.get('copy_readable_output',False), 'copy_native_stat_abi':report.get('copy_native_stat_abi',False), 'copy_allocated_capacity':report.get('copy_allocated_capacity',False), 'copy_absolute_open':report.get('copy_absolute_open',False), 'copy_descriptor_checks':report.get('copy_descriptor_checks',False), 'copy_private_directory':report.get('copy_private_directory',False), 'verified_copy_enabled':report.get('verified_copy_enabled',False), 'unresolved':'0.8.1 icon/focus/shortcut changes require PS4 validation. Existing body font, texture, generic live thumbnails and unavailable folder totals remain. Sound troubleshooting deferred by user. Library licensing is unspecified upstream; this is a personal local preview, not a claim of public redistribution rights. Phone upload/paste, above-4-GB hardware verification, crash recovery and installer integration remain incomplete'}
if release in ('0.9.0','0.10.0','0.10.1','0.11.0','0.11.1','0.11.2','0.12.0','0.13.0','0.14.0'):
    provenance.update({
        'host_tests':'Nine CTest suites and sanitizer runs: 23893 core checks, 18321 native filesystem assertions, 2162 media/name/wire checks, 15 preview mailbox assertions, 78 controller assertions, plus access/audio suites and 256 USB runtime checks; 22000 malformed parser inputs; 14 Python regressions.',
        'previous_release':'0.8.1 preserved. Continues the interrupted Rename/metadata/toolbar/performance update.',
        'renderer':'39 guarded sanitizer scenarios; 37 production controller/render checks with synthetic devices. Actual built PKG artwork/title parsed successfully. See visual/renderer-benchmark.json for same-host comparison with 0.8.1. Console validation remains.',
        'unresolved':'PS4 controller/TV and frame-rate validation remain. Video previews use embedded cover, same-name JPEG/PNG sidecar, or device thumbnail; no video-frame decoder. Native namespace/USB behavior is simulated in host tests. Phone rename requires advertised property operations and a writable filename descriptor. Sound troubleshooting, phone upload, above-4-GB hardware verification, crash recovery and installer work remain deferred.',
        'rename':True,'background_metadata_previews':True,'controller_toolbar':True,'cached_cpu_rendering':True})
if release in ('0.10.0','0.10.1'):
    provenance.update({
        'host_tests':'Nine native suites under ASan/UBSan and CTest; 24073 core/keyboard checks, 15485 native filesystem assertions, 2162 metadata checks, 15 preview checks, 77 controller checks, 583 audio lifecycle assertions, plus access/USB/context suites; 22000 malformed inputs; 14 Python regressions.',
        'previous_release':'0.9.0 accepted by the user as smooth at 60 FPS, with everything excellent. Prior packages preserved.',
        'renderer':'42 guarded native screens and 51 production controller/render checks; full-screen Settings, modal sort picker, QWERTY with Backspace, procedural controller glyphs. Console rendering and audio remain to be checked for this update.',
        'unresolved':'TV audio and transfer timing need console validation. Audio uses the system MAIN stereo port, explicit unity channel volume, continuous silence between cues and error recovery. No reserve or destination filler is created. Integrity is streamed SHA-256 plus one saved-file hash read; no source re-read or move rehash. Source/destination identities and metadata, exclusive creation and cancellation/error cleanup remain. Concurrent external writes are unsupported. Phone upload, video frame decoding, >4-GB hardware proof and installer work remain incomplete.',
        'fullscreen_settings':True,'sort_picker':True,'qwerty_keyboard':True,'controller_glyphs':True,'audio_system_main_stereo':True,'copy_reserve_bytes':0,'copy_destination_prefill':False,'copy_source_content_passes':1,'copy_destination_hash_passes':1})
if release=='0.10.1':
    provenance.update({
        'host_tests':'Nine sanitizer suites; 92 production controller/session assertions including renderer-to-log recursion with a failing guard-removal mutation; 14 Python regressions. Synthetic native APIs, no console execution of this build.',
        'previous_release':'0.10.0 preserved; console SIGSEGV captured after PS-button focus change. See UPDATE_0.10.1.md for address mapping and evidence hashes.',
        'renderer':'42 guarded render scenarios and 51 controller/render checks. No visual design change. New render guard blocks redraws originating from render-time logging; timing counters commit before writing logs.',
        'unresolved':'The captured recursive logging failure is corrected and reproduced in host tests. PS-button return/resume and normal exit still need hardware validation of 0.10.1. Phone upload, video frame decoding, >4-GB hardware proof and installer integration remain incomplete.',
        'diagnostic_render_reentry_guard':True,'render_timing_committed_before_logging':True})
if release in ('0.11.0','0.11.1','0.11.2','0.12.0','0.13.0','0.14.0'):
    provenance.update({
        'host_tests':'Ten native sanitizer suites including streamed-upload protocol assertions and integrated upload/copy/move/space regressions. Fourteen Python regressions. Native calls are simulated; see visual/validation-results.json for results.',
        'previous_release':'0.10.1 accepted by the user as working great; package preserved.',
        'renderer':'45 guarded renderer scenarios plus production controller/render checks for phone Paste and preflight storage warnings. Verification renders status text with no progress bar or percentage.',
        'unresolved':'Phone upload and native free-space reporting need console validation. Unknown free space blocks transfer. Standard SendObject supports each file up to 4294967282 bytes here; >=4-GiB upload, phone-to-phone copying, resume, video-frame decoding and direct installation remain incomplete. Interrupted MTP uploads may leave partial files; poisoned sessions are not replayed and native sources remain intact.',
        'phone_upload':True,'upload_max_file_bytes':4294967282,'pretransfer_space_check':True,'verification_status_only':True,'layered_system_chimes':True,
        'diagnostic_render_reentry_guard':True,'render_timing_committed_before_logging':True})
if release=='0.11.1':
    provenance.update({
        'previous_release':'0.11.0 capacity preflight regressed native transfers: native fstatfs returned EPERM with namespace-only access.',
        'storage_access_fix':'Apply and verify the complete pinned libjbc current-process credentials before workers start; includes already-global processes. No per-query credential switching or global kernel patches.',
        'hardware_diagnostic':'PS4 11.00 / GoldHEN capacity probe: statfs and fstatfs both succeeded under the loader access profile; /data available 155611271168 bytes. The application package still needs console transfer validation.',
        'unresolved':'Application capacity query and transfers need console validation of 0.11.1. Phone upload, TV chimes and >4-GB transfers remain hardware-unverified. Unknown free space still blocks transfer.'})
if release=='0.11.2':
    provenance.update({
        'date':'2026-10-22',
        'previous_release':'0.11.1 capacity checks succeeded on PS4; phone-to-native destination setup failed before copying with filesystem status -12 and logged EACCES.',
        'storage_access_fix':'Preserve original Unix UID/GID fields at startup while retaining libjbc Sony process type, credentials, capabilities and global filesystem references. Existing files and directory modes are not modified.',
        'transfer_diagnostics':'Record the first failing destination call and its errno immediately, before cleanup can replace it. Paths and file names are excluded.',
        'hardware_diagnostic':'Read-only FTP confirms existing /data/psmtp directories belong to UID 1; the 0.11.1 app runs as UID 0. A UID 0 loader probe could not create its unique diagnostic directory inside /data/psmtp (EACCES), so it created no files. The updated application profile requires console validation.',
        'unresolved':'0.11.2 owner-preserving Sony capacity profile and phone-to-native transfers need console testing. Unknown space remains blocked. Phone uploads, TV chimes and >4-GB transfers remain hardware-unverified. Manual PKG installation requested by the user.'})
if release in ('0.12.0','0.13.0','0.14.0'):
    validation=json.loads((BUILD/'visual/validation-results.json').read_text())
    large=validation.get('large_streams',{})
    if not large.get('passed') or large.get('bytes_each_direction',0)<=4294967296 or set(large.get('directions',[]))!={'native-to-phone','phone-to-native'}:
        raise SystemExit('Missing complete large-transfer evidence for both directions')
    if sha(BUILD/'visual/large-stream-validation.log')!=large.get('log_sha256'):
        raise SystemExit('Large-transfer validation log changed')
    for name,digest in large.get('sources_sha256',{}).items():
        if sha(ROOT/name)!=digest:raise SystemExit('Large-transfer source changed since validation: '+name)
    provenance.update({
        'date':'2026-10-22',
        'previous_release':'0.11.2 small phone-to-internal transfer passed on PS4: 4,259,840 bytes, SHA-256 reread matched, source preserved. See HARDWARE_RESULT_0.11.2.md.',
        'large_phone_upload':True,'upload_max_file_bytes':report['upload_max_file_bytes'],
        'host_tests':'Ten native ASan/UBSan suites, fourteen Python regressions, plus 540947 full large-transfer integration assertions. 4295032820 bytes streamed and SHA-256 verified in each direction using bounded synthetic storage. See visual/validation-results.json and large-stream-validation.log.',
        'large_upload_protocol':'Saturating ObjectInfo/container lengths, packet-aligned bounded streaming, short-packet/ZLP termination, and 30-second final commit response deadline. Requires advertised partial64 and size64 before large object creation.',
        'large_verification':'Select GetPartialObject64 for large files even when standard GetPartialObject is also advertised. Check exact 64-bit ObjectSize before/after SHA-256 read-back and before removing a move source.',
        'unresolved':'Large transfers in both directions need real phone/PS4 tests. This build retains the owner-and-capacity startup profile. Filesystems and receiver limits still apply. Phone-to-phone copying, resume, video-frame decoding and direct installation remain unimplemented. Installation is manual.'})
if release=='0.13.0':
    provenance.update({
        'date':'2026-10-22',
        'previous_release':'0.12.0 phone-to-PS4 transfer of 4862766944 bytes confirmed by read-only logs: saved SHA-256 match, source retained. Reverse hardware test remains pending. See HARDWARE_RESULT_0.12.0.md.',
        'host_tests':'Eleven native ASan/UBSan suites, fourteen Python regressions, and complete 4295032820-byte integrations in both directions. See visual/validation-results.json for counts and evidence hashes.',
        'streamed_phone_download':True,'download_buffer_bytes':262144,
        'transfer_optimization':'One advertised GetObject transaction with bounded direct bulk reads; advertised partial-read fallback only after healthy OperationNotSupported before payload. Unrolled SHA-256 with direct whole-block input; pinned directory guards; no successful content-transfer log flushing; 64-MiB log checkpoints; static verification screens redraw only on changes.',
        'transfer_measurements':'Receive and saved-file verification durations, USB wait, write/hash/read/sync/guard/UI times, request counts and selected endpoint packet sizes are logged. Host hash and protocol-call benchmarks are in visual/throughput-benchmark.json; they do not establish PS4 speed.',
        'large_verification':'Trusted exact 64-bit ObjectSize bounds streamed GetObject; saturated container length validated, full saved SHA-256 reread retained. Upload verification retains partial64 and exact size rechecks.',
        'unresolved':'0.13.0 throughput and USB behavior need console validation after manual PKG installation. No measured PS4 speedup or hardware-maximum claim. Reverse large-file hardware test remains pending. Phone-to-phone copying, resume, video-frame decoding and direct installation remain unimplemented.'})
if release=='0.14.0':
    provenance.update({
        'date':'2026-10-22',
        'previous_release':'User reports approximately doubled phone-to-PS4 transfer speed on 0.13.0. No separate timed 0.13.0 log measurement is claimed.',
        'host_tests':'Fourteen C sanitizer suites, fourteen Python regressions, 76 production controller/render checks, 52 guarded render scenarios and complete >4-GiB copy integrations both ways. Native installer/network calls are simulated. See visual/validation-results.json.',
        'renderer':'Live decimal MB/s and a recent four-second transfer ETA; one-second warmup, stalled-data detection, phase/file/clock reset. X on PKG opens Install confirmation on phone, Internal storage and USB. Native installer progress comes from BGFT. Verification remains status-only.',
        'live_transfer_speed':True,'recent_window_eta':True,'direct_pkg_install':True,'installer_loopback_only':True,'phone_pkg_staging':False,'installer_source_preserved':True,
        'pkg_installation':'Read-only selected source -> bounded 64-bit HTTP range bridge bound to 127.0.0.1 -> PS4 BGFT. Phone MTP session is exclusively owned by the reader until it joins. Sources are never removed; existing install/task conflicts are reported without uninstall, overwrite preparation, or taking ownership of foreign tasks. Native system validation and working storage remain.',
        'installer_abi':'Explicit 64-bit package sizes, progress fields and file offsets, with compile-time layout assertions; avoids the SDK undersized BGFT progress structure. Published flatz/Itemzflow declarations are referenced in UPDATE_0.14.0.md.',
        'unresolved':'0.14.0 native module loading, loopback HTTP and BGFT installation require PS4 validation after manual update. Host tests do not establish actual installation success. Keep PSMTP/source connected until delivery; check PS4 Notifications for final install status. Current application self-update remains manual. Reverse large-file hardware testing, phone-to-phone copy and resume remain pending.'})
(ROOT/'docs/BUILD_PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
shutil.copyfile(raw,DEST/('PS-MTP-Explorer-'+release+'-PREVIEW.pkg'))
for name in ['build-report.json','structure-report.json']:
    shutil.copyfile(BUILD/name,DEST/name)
preview_report=json.loads((BUILD/'ui-preview-report.json').read_text(encoding='utf-8'))
if release in ('0.9.0','0.10.0','0.10.1','0.11.0','0.11.1','0.11.2','0.12.0','0.13.0','0.14.0'):
    expected_scenarios=52 if release=='0.14.0' else 45 if release in ('0.11.0','0.11.1','0.11.2','0.12.0','0.13.0','0.14.0') else 42 if release in ('0.10.0','0.10.1') else 39
    if len(preview_report['scenarios'])!=expected_scenarios: raise SystemExit('Missing guarded renderer scenarios')
    visual_report=json.loads((BUILD/'visual/final-visual-results.json').read_text())
    functional_report=json.loads((BUILD/'visual/native-functional-results.json').read_text())
    if visual_report['package_sha256']!=report['package']['sha256'] or visual_report['preview_sources_sha256']!=preview_report['sources_sha256']:
        raise SystemExit('Visual evidence does not match this package and preview')
    if sha(BUILD/'ui-host.exe')!=functional_report['host_sha256'] or sha(ROOT/'tools/verify_native_ui.py')!=functional_report['verifier_sha256']:
        raise SystemExit('Controller host or verifier changed since validation')
    if len(functional_report['checks'])<(76 if release=='0.14.0' else 58 if release in ('0.11.0','0.11.1','0.11.2','0.12.0','0.13.0','0.14.0') else 51 if release in ('0.10.0','0.10.1') else 37): raise SystemExit('Missing native controller checks')
    for name,digest in visual_report['reviewed_images'].items():
        if sha(BUILD/name)!=digest: raise SystemExit('Reviewed image changed: '+name)
else:
    if len(preview_report['scenarios'])!=34: raise SystemExit('Expected 34 current UI scenarios')
    visual_report=json.loads((BUILD/'visual/final-visual-results.json').read_text(encoding='utf-8'))
    functional_report=json.loads((BUILD/'visual/final-functional-results.json').read_text(encoding='utf-8'))
    layout_report=json.loads((BUILD/'visual/layout-preservation.json').read_text(encoding='utf-8'))
    if visual_report['package_sha256']!=report['package']['sha256'] or visual_report['preview_sources_sha256']!=preview_report['sources_sha256']:
        raise SystemExit('Visual evidence does not match the current package/preview')
    if sha(BUILD/'ui-host.exe')!=visual_report['host_sha256'] or sha(ROOT/'tools/verify_ui_preview.mjs')!=visual_report['verifier_sha256']:
        raise SystemExit('Interactive QA host or verifier changed since verification')
    if len(functional_report['checks'])!=44 or functional_report['browserErrors'] or visual_report['browserErrors']:
        raise SystemExit('Expected 44 passing final controller/focus checks with no browser errors')
    if len(layout_report['screens'])!=4 or any(not s['passed'] for s in layout_report['screens'].values()):
        raise SystemExit('Existing UI layout preservation check failed')
for name,digest in preview_report['sources_sha256'].items():
    if sha(ROOT/name)!=digest: raise SystemExit('UI preview source changed: '+name)
for name in preview_report['scenarios']:
    if sha(BUILD/name)!=preview_report['images_sha256'][name]: raise SystemExit('UI preview changed: '+name)
    shutil.copyfile(BUILD/name,DEST/name)
shutil.copyfile(BUILD/'ui-preview-report.json',DEST/'ui-preview-report.json')
shutil.copyfile(BUILD/'package/sce_sys/icon0.png',DEST/'app-icon.png')
for document in (ROOT/'docs').iterdir():
    if document.is_file(): shutil.copyfile(document,DEST/document.name)
shutil.copyfile(ROOT/'LICENSE',DEST/'LICENSE-application-source.txt')
(DEST/'licenses').mkdir(exist_ok=True)
shutil.copyfile(SDK/'LICENSE',DEST/'licenses/OpenOrbis-GPL-3.txt')
shutil.copyfile(SDK/'include/stb/stb_image.h',DEST/'licenses/stb_image.h')
shutil.copyfile(SDK/'include/stb/stb_truetype.h',DEST/'licenses/stb_truetype.h')
shutil.copyfile(ROOT/'assets/fonts/OFL.txt',DEST/'licenses/NotoSans-OFL.txt')
shutil.copyfile(ROOT/'assets/fonts/NotoSans-Light-OFL.txt',DEST/'licenses/NotoSans-Light-OFL.txt')
shutil.copyfile(ROOT/'third_party/libjbc/NOTICE.txt',DEST/'licenses/libjbc-NOTICE.txt')
shutil.copyfile(ROOT/'third_party/libjbc/provenance.json',DEST/'licenses/libjbc-provenance.json')
# Corresponding SDK dummy module sources and build inputs; no firmware sources.
runtime_source = DEST/'openorbis-runtime-source'
for relative in ['libSceFios2/Makefile','libSceFios2/libSceFios2/lib.c',
                 'libSceFios2/libSceFios2/build.bat', 'libc/Makefile','libc/libc/lib.c','libc/libc/build.bat']:
    target=runtime_source/relative; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(SDK/'src/modules'/relative,target)
for relative in ['src/crt/crtlib.c','src/crt/crtlib.S','link.x','LICENSE']:
    target=runtime_source/relative;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(SDK/relative,target)
test_file=DEST/'psmtp-copy-test.bin'
test_file.write_bytes(bytes(range(256))*4096)
start=(ROOT/'docs/START_HERE.txt').read_text(encoding='utf-8').replace('@RELEASE@',release).replace('@TEST_SHA256@',sha(test_file))
(DEST/'START-HERE.txt').write_text(start,encoding='utf-8')
if (BUILD/'visual').exists(): shutil.copytree(BUILD/'visual',DEST/'visual',dirs_exist_ok=True)
# Full original source snapshot for this local build; no caches, SDK or private data.
sources=[]
for directory in ['src','include','tests','tools','docs','assets','.github','third_party']:
    sources += [p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
sources += [ROOT/p for p in ['README.md','LICENSE','CMakeLists.txt','Makefile.ps4','.gitignore','.gitattributes']]
with zipfile.ZipFile(DEST/'application-source.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for source in sorted(sources): archive.write(source,source.relative_to(ROOT).as_posix())
files=sorted(p for p in DEST.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt')
(DEST/'SHA256SUMS.txt').write_text(''.join(sha(p)+'  '+p.relative_to(DEST).as_posix()+'\n' for p in files))
bundle=ROOT/('artifacts/PS-MTP-Explorer-'+release+'-PREVIEW.zip')
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(DEST.rglob('*')):
        if p.is_file(): archive.write(p,p.relative_to(DEST.parent).as_posix())
with zipfile.ZipFile(bundle) as archive:
    if archive.testzip() is not None: raise SystemExit('Delivery ZIP CRC failure')
print('Created experimental, hardware-unverified test bundle:',bundle)
print('PKG SHA256:',report['package']['sha256'])
