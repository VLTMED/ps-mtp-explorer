"""Compare recorded upstream exports and run host models, never build a PKG.

Firmware labels in the host fixtures are routing inputs, not console coverage.
Passing this verifier cannot open the universal hardware release gate.
"""
import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exports(document):
    return {symbol['name']: symbol['encoded_id']
            for module in document['modules'] for library in module['libraries']
            if library['is_export'] for symbol in library['symbols'] if symbol.get('name')}


def input_hashes():
    paths = [*ROOT.glob('src/*.c'), *ROOT.glob('include/**/*.h'), *ROOT.glob('src/ps4/*.c'), *ROOT.glob('src/ps4/*.h'),
             *ROOT.glob('third_party/libjbc/*.[ch]'), *ROOT.glob('tests/*.c'), *ROOT.glob('tests/*.h'),
             ROOT/'CMakeLists.txt', ROOT/'tools/build_host.py', ROOT/'tools/build_ps4.py',
             Path(__file__).resolve(), ROOT/'docs/CROSS_FIRMWARE_SOURCES.json']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(paths))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-tests', action='store_true')
    parser.add_argument('--large-transfers', action='store_true')
    parser.add_argument('--native-syntax', action='store_true')
    parser.add_argument('--cc', help='native syntax compiler; defaults to prepared LLVM 18')
    parser.add_argument('--host-cc', help='host compiler argument to build_host.py')
    parser.add_argument('--reference-dir', type=Path, help='directory of captured upstream files')
    parser.add_argument('--output', type=Path, default=ROOT/'build-cross-firmware/validation.json')
    args = parser.parse_args()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    evidence = json.loads((ROOT/'docs/CROSS_FIRMWARE_SOURCES.json').read_text())
    report = {'scope': 'source comparisons and simulated API/kernel behavior only',
              'universal_compatibility_verified': False, 'release_allowed': False,
              'release_gate_reason': 'No cross-firmware console or complete binary/ABI validation; models cannot establish >90% universal reliability.',
              'export_comparisons': [], 'checks': []}
    status = 0
    report['inputs_sha256'] = input_hashes()
    try:
        expected = {'libkernel': {'_fstatfs'}, 'libSceBgft': {
            'sceBgftServiceIntInit', 'sceBgftServiceIntTerm',
            'sceBgftServiceIntDownloadRegisterTaskByStorageEx',
            'sceBgftServiceIntDownloadUnregisterTask', 'sceBgftServiceDownloadStartTask',
            'sceBgftServiceDownloadStopTask', 'sceBgftServiceDownloadGetProgress'}}
        baseline = {}
        for record in evidence['export_comparison']:
            symbols = {s['name']: s['nid'] for s in record['exports']}
            if set(symbols) != expected[record['library']]:
                raise ValueError('Incomplete recorded exports: '+record['url'])
            previous = baseline.setdefault(record['library'], symbols)
            if previous != symbols:
                raise ValueError('Export NIDs differ: '+record['url'])
            if args.reference_dir:
                key = ('doc-' if record['library']=='libkernel' else 'bgft-')+record['firmware']
                path = args.reference_dir/(key+'.txt')
                original = exports(json.loads(path.read_text(encoding='utf-8-sig')))
                if any(original.get(name) != nid for name, nid in symbols.items()):
                    raise ValueError('Captured source does not match selected exports: '+str(path))
            report['export_comparisons'].append(record)
        report['checks'].append({'name': 'recorded-export-comparison', 'passed': True,
                                 'captured_sources_checked': bool(args.reference_dir),
                                 'note': 'Matching exports do not prove identical function implementations or struct ABI.'})
        if args.run_tests:
            log = output.parent/'host-tests.log'
            command = [sys.executable, str(ROOT/'tools/build_host.py'), '--sanitize', '--output', str(output.parent)]
            if args.host_cc: command += ['--cc', args.host_cc]
            if args.large_transfers: command += ['--large-transfers']
            with log.open('w', encoding='utf-8') as stream:
                result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            text = log.read_text(encoding='utf-8')
            report['checks'].append({'name': 'sanitized-host-tests', 'passed': result.returncode==0,
                                     'log': str(log), 'log_sha256': sha(log),
                                     'large_transfers': args.large_transfers,
                                     'suite_count': len(re.findall(r'^Building (?!psmtp_demo)', text, re.M))})
            if result.returncode: raise RuntimeError('Host tests failed; see '+str(log))
        if args.native_syntax:
            cc = args.cc or str(ROOT/'.tools/llvm18/bin/clang.exe')
            sdk = ROOT/'.tools/sdk/OpenOrbis/PS4Toolchain'
            tree = ast.parse((ROOT/'tools/build_ps4.py').read_text())
            sources = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id=='SOURCES' for t in n.targets))
            flags = ['-target', 'x86_64-pc-freebsd12-elf', '-std=c99', '-D_POSIX_C_SOURCE=200809L',
                     '-DPSMTP_EXPERIMENTAL_PS4_USB=1', '-nostdinc', '-I'+str(ROOT/'include'),
                     '-isystem', str(sdk/'include'), '-isystem', str(sdk/'include/orbis/_types'),
                     '-isystem', str(sdk/'include/stb'), '-fPIC', '-fshort-wchar', '-fno-stack-protector',
                     '-Wall', '-Wextra', '-Werror', '-O2', '-fsyntax-only']
            results = []
            for production in (False, True):
                for source in sources:
                    active = flags+(['-DPSMTP_PRODUCTION=1', '-include', str(ROOT/'src/ps4/release_config.h')] if production else [])
                    if source.startswith('third_party/libjbc/'):
                        active += ['-std=gnu99', '-ffreestanding', '-mno-red-zone', '-mno-sse', '-mno-sse2',
                                   '-mno-mmx', '-fno-asynchronous-unwind-tables', '-fno-unwind-tables', '-Wno-unused-parameter']
                    result = subprocess.run([cc, *active, str(ROOT/source)], capture_output=True, text=True)
                    results.append({'source': source, 'production': production, 'exit_code': result.returncode,
                                    'output': result.stdout+result.stderr})
            log = output.parent/'native-syntax.json'
            log.write_text(json.dumps(results, indent=2)+'\n')
            passed = all(r['exit_code']==0 for r in results)
            report['checks'].append({'name': 'native-syntax', 'passed': passed, 'translation_units': len(results),
                                     'compiler': cc, 'compiler_sha256': sha(Path(cc)) if Path(cc).is_file() else None,
                                     'log': str(log), 'log_sha256': sha(log)})
            if not passed: raise RuntimeError('Native syntax checks failed; see '+str(log))
    except (ValueError, OSError, RuntimeError, StopIteration, KeyError) as error:
        report['error'] = str(error)
        status = 1
    if report['inputs_sha256'] != input_hashes():
        report['error'] = 'Source inputs changed during verification; rerun against a stable snapshot.'
        status = 1
    report['automated_checks_passed'] = status==0
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(('PASS' if not status else 'FAIL')+': automated source/model checks; universal release gate remains CLOSED')
    print(output)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
