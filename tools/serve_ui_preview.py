"""Loopback-only QA server for native C frames; not a replacement web frontend.

Use bundled Python with Pillow. Static /screen routes use C renderer fixtures;
/explorer runs the production controller loop with synthetic devices and no
native filesystem mutation adapter. Browser input maps to PS4 buttons.
"""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import io
import json
import re
from pathlib import Path
import subprocess
import threading
from urllib.parse import urlparse
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
version=re.search(r'#define PSMTP_VERSION "([^"]+)"',(ROOT/'include/psmtp/version.h').read_text()).group(1)
parser.add_argument('--build',type=Path,default=ROOT/('build-ps4-'+version))
parser.add_argument('--port',type=int,default=8765)
args=parser.parse_args();build=args.build.resolve()
live=None;state={};png=b'';lock=threading.Lock();history=[]
work=ROOT/('.research/ui-preview-'+version);work.mkdir(parents=True,exist_ok=True)
def receive():
    global state,png
    line=live.stdout.readline()
    if not line: raise RuntimeError('Native host stopped; inspect host-stderr.log')
    state=json.loads(line)
    if not state.get('exited'):
        im=Image.open(work/'frame.ppm');out=io.BytesIO();im.save(out,format='PNG');png=out.getvalue()
    history.append(dict(state));return state
def reset():
    global live
    if live and live.poll() is None:
        live.stdin.close()
        try: live.wait(timeout=3)
        except subprocess.TimeoutExpired: live.terminate();live.wait(timeout=3)
    err=(work/'host-stderr.log').open('a')
    live=subprocess.Popen([str(build/'ui-host.exe'),str(work/'frame.ppm')],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
    err.close();return receive()
PAGE='''<!doctype html><html><head><meta charset="utf-8"><title>PSMTP native renderer QA</title>
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#121011}canvas{display:block;width:100vw;height:100vh;object-fit:contain}#note{position:fixed;bottom:0;right:0;background:#222;color:white;font:12px sans-serif;padding:4px}body[data-clean] #note{display:none}</style></head>
<body><canvas id="screen" width="1920" height="1080" aria-label="Native PS4 explorer preview"></canvas><div id="note">Host QA · synthetic devices · Enter X · Escape Circle · T Options · V L3</div><script src="/preview.js"></script></body></html>'''
SCRIPT='''var canvas=document.getElementById('screen'),ctx=canvas.getContext('2d');var live=location.pathname==='/explorer';var latest={},queue=Promise.resolve();
if(new URLSearchParams(location.search).has('clean'))document.body.setAttribute('data-clean','');
async function redraw(){var response=await fetch(live?'/api/frame':'/frame/'+location.pathname.split('/').pop()+'.png');if(!response.ok)throw Error(await response.text());var image=await createImageBitmap(await response.blob());ctx.drawImage(image,0,0,1920,1080);image.close();canvas.dataset.ready='true';canvas.dataset.frame=latest.frame||0;}
async function send(command){if(!live)return;latest=await(await fetch('/api/input',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command})})).json();await redraw();}
var keys={ArrowUp:1,ArrowDown:2,ArrowLeft:4,ArrowRight:8,Enter:16,Escape:32,c:64,t:128,o:256,q:512,e:1024,z:2048,x:4096,v:8192,Delete:16384,r:32768};
addEventListener('keydown',event=>{if(keys[event.key]){event.preventDefault();queue=queue.then(()=>send(String(keys[event.key]))).catch(error=>{console.error(error);canvas.dataset.error=error.message;});}});
window.qaState=()=>latest;window.qaHotplug=command=>(queue=queue.then(()=>send(command)));
(async()=>{if(live)latest=await(await fetch('/api/state')).json();await redraw();})();'''
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*unused): pass
    def send(self,data,kind='application/json',code=200):
        self.send_response(code);self.send_header('Content-Type',kind);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    def do_GET(self):
        path=urlparse(self.path).path
        try:
            if path in ['/','/explorer'] or path.startswith('/screen/'): self.send(PAGE.encode(),'text/html; charset=utf-8')
            elif path=='/preview.js': self.send(SCRIPT.encode(),'text/javascript')
            elif path=='/api/state': self.send(json.dumps(state).encode())
            elif path=='/api/frame': self.send(png,'image/png')
            elif path=='/api/history': self.send(json.dumps(history).encode())
            elif path.startswith('/frame/') and path.endswith('.png') and Path(path).name in {p.name for p in build.glob('*.png')}:
                self.send((build/Path(path).name).read_bytes(),'image/png')
            elif path=='/favicon.ico':self.send(b'','image/x-icon',204)
            else:self.send(b'Not found','text/plain',404)
        except Exception as error:self.send(str(error).encode(),'text/plain',500)
    def do_POST(self):
        try:
            with lock:
                path=urlparse(self.path).path
                if path=='/api/reset': result=reset()
                elif path=='/api/input':
                    size=int(self.headers.get('Content-Length','0'))
                    if size>1024: raise ValueError('Input too large')
                    command=str(json.loads(self.rfile.read(size)).get('command',''))
                    if command not in ['p0','p1','u0','u1','q'] and (not command.isdecimal() or int(command)>65535):raise ValueError('Invalid controller input')
                    if state.get('exited'): raise ValueError('Reset the synthetic app first')
                    live.stdin.write(command+'\n');live.stdin.flush();result=receive()
                else:raise ValueError('Unknown endpoint')
                self.send(json.dumps(result).encode())
        except Exception as error:self.send(str(error).encode(),'text/plain',400)
reset();server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
print(f'Native UI QA at http://127.0.0.1:{args.port}/explorer ; static /screen/reference-grid',flush=True)
try:server.serve_forever()
except KeyboardInterrupt:pass
finally:
    if live and live.poll() is None:live.stdin.close();live.wait(timeout=5)
