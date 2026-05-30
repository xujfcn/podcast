import re, requests, subprocess
from pathlib import Path

root = Path('/root/.openclaw/workspace/podcast')
text = Path('/root/.openclaw/workspace/TOOLS.md').read_text()
m = re.search(r'Authorization: Bearer ([^"\s]+)', text)
if not m:
    m = re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', text)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)
script = (root/'episodes/ep072_script.txt').read_text()
paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    r = requests.post(
        'https://crazyrouter.com/v1/audio/speech',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
        timeout=300,
    )
    print('part', i, 'status', r.status_code, r.headers.get('content-type'), flush=True)
    if not r.ok:
        print(r.text[:1000]); r.raise_for_status()
    out = root/f'episodes/ep072_part{i}.mp3'
    out.write_bytes(r.content)
    print('saved', out, out.stat().st_size, flush=True)
concat = root/'episodes/ep072_concat.txt'
concat.write_text("file 'ep072_part1.mp3'\nfile 'ep072_part2.mp3'\nfile 'ep072_part3.mp3'\n")
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(root/'audio/ep072.mp3')],check=True)
print('merged', root/'audio/ep072.mp3', (root/'audio/ep072.mp3').stat().st_size, flush=True)
