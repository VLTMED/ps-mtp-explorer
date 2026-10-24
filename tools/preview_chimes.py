"""Export the production chimes as stereo WAVs; no audio hardware is used."""
import argparse
import array
import hashlib
import json
from pathlib import Path
import subprocess
import wave

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
output = parser.parse_args().output.resolve()
output.mkdir(parents=True, exist_ok=True)
source = output / 'chime-preview.c'
source.write_text('''#include "psmtp/device_sound.h"
#include <stdio.h>
int main(int argc,char **argv){int16_t pcm[PSMTP_CHIME_FRAMES*2];FILE *f;int event;
if(argc!=3)return 1;for(event=0;event<2;++event){psmtp_chime_render(event,0,pcm,PSMTP_CHIME_FRAMES);
f=fopen(argv[event+1],"wb");if(!f)return 2;if(fwrite(pcm,sizeof(pcm),1,f)!=1)return 3;if(fclose(f))return 4;}return 0;}
''')
exe = output / 'chime-preview.exe'
subprocess.run([str(ROOT / '.tools/ziglang/zig.exe'), 'cc', '-std=c99', '-O2',
                '-I' + str(ROOT / 'include'), str(ROOT / 'src/device_sound.c'), str(source),
                '-o', str(exe)], check=True)
raw = [output / 'disconnect.pcm', output / 'connect.pcm']
subprocess.run([str(exe), *map(str, raw)], check=True)
report = {}
for path in raw:
    data = path.read_bytes()
    samples = array.array('h', data)
    assert len(samples) == 48000 and samples[0] == samples[1] == samples[-2] == samples[-1] == 0
    peak = max(map(abs, samples))
    jump = max(abs(samples[i] - samples[i - 2]) for i in range(2, len(samples)))
    assert 1000 < peak < 5000 and jump < 2000
    target = path.with_suffix('.wav')
    with wave.open(str(target), 'wb') as out:
        out.setnchannels(2)
        out.setsampwidth(2)
        out.setframerate(48000)
        out.writeframes(data)
    report[target.name] = {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                           'duration_ms': 500, 'sample_rate': 48000, 'channels': 2,
                           'peak': peak, 'maximum_sample_step': jump}
assert report['connect.wav']['sha256'] != report['disconnect.wav']['sha256']
(output / 'audio-preview-report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
