from pathlib import Path
import json, re, subprocess, xml.etree.ElementTree as ET
import requests

root = Path('/root/.openclaw/workspace/podcast')
ep = 95
title = 'EP095: Kimi K3 vs GLM-5.2 — Why Output Completeness Beats Leaderboards'
description = 'A practical benchmark-driven comparison of Kimi K3 and GLM-5.2 across university-level math, physics, and production Python, with a focus on correctness, output completeness, latency, and workflow routing.'
pub_date = 'Sun, 19 Jul 2026 10:20:00 +0000'
script = '''EP095: Kimi K3 vs GLM-5.2 — Why Output Completeness Beats Leaderboards

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are looking at a practical comparison between Kimi K3 and GLM-5.2, based on the kind of evaluation that matters after a model leaves a leaderboard: can it complete the task, survive verification, and fit a real workflow?

The benchmark used three university-level tasks. The first was a probability problem involving the expected stopping time for the self-overlapping binary pattern 1011. The second was a mechanics problem with friction, an inelastic collision, a coefficient of restitution, a spring, and an energy ledger. The third was production Python for aggregating API logs, handling time zones, half-open time windows, retries, missing fields, and invalid statuses.

The first lesson is that HTTP 200 is not the same as success. An API can return a successful HTTP status while the model answer ends with finish_reason equal to length. If the missing part contains the final formula, the energy check, or the runnable code, the request is not complete from the application’s point of view.

On the math problem, both Kimi K3 and GLM-5.2 delivered complete solutions. The correct general result is one over p plus one over p cubed q, where q equals one minus p. For p equal to two thirds, the expected stopping time is 93 over 8, or 11.625. For a fair binary sequence, it is 18. The important detail is the prefix automaton: the pattern has a self-overlap, so a near miss does not always return to the zero state.

The physics problem exposed a different engineering distinction. Kimi K3 calculated the speed before collision, solved momentum and restitution, checked that the two blocks separate, and handled the spring as a single-block compression problem. It also noticed that if the distance from the collision point to the spring is not specified, the compression cannot have one unique value. That is a strong sign of useful reasoning: the model did not silently invent a missing parameter.

In the same long physics task, GLM-5.2 returned HTTP 200 but the visible response ended because of the length limit. That result should not be described as a clean physics failure, and it should not be counted as a complete pass either. The fair description is that the reasoning and output budget did not produce a complete deliverable under that prompt and configuration.

The programming task made the difference even more concrete. A production answer has to define timestamp parsing, timezone requirements, the inclusive start and exclusive end boundary, duplicate request selection, retry precedence, missing cached tokens, success classification, deterministic sorting, summary statistics, and tests. Kimi K3 returned a full Python 3.11 implementation and a boundary-focused assertion set. GLM-5.2’s long response was again truncated before it could be treated as a complete implementation.

This leads to a better benchmark scorecard. Track correctness, but also track finish reason, visible output completeness, executable-code pass rate, schema validity, latency, token use, retry count, and cost per accepted result. A model that is slightly cheaper per token can be more expensive per successful task if it needs extra turns, manual repair, or a second model to finish the answer.

The result does not mean that Kimi K3 is universally better or that GLM-5.2 has no place in production. It means the routing decision depends on the unit of work. Kimi K3 looked stronger in this test for long, complete technical deliverables. GLM-5.2 may still be a good fit for shorter reasoning, structured intermediate steps, or workflows where the task is deliberately split into small calls and every response is validated.

A practical production pattern is to make completeness a gateway-level signal. Reject or retry responses whose finish reason is length. For code, run a syntax check and tests. For JSON, validate against a schema. For numerical work, verify dimensions, boundary cases, or independent calculations. Then route only the failed step to another model instead of restarting the whole workflow.

The broader point is simple: model selection is workflow design. Leaderboards tell you something about capability, but they do not tell you whether your exact prompt, output limit, tool schema, and verification process will produce an accepted result. Run a replay set from real work, keep the API interface stable, log the actual model and finish reason, and compare cost per successful task.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. Try the unified API at crazyrouter.com, and see you in the next episode.'''
(root/'episodes').mkdir(exist_ok=True); (root/'audio').mkdir(exist_ok=True)
(root/f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')
tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
m = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools)
if not m: raise SystemExit('API key not found')
key=m.group(1)
paras=script.split('\n\n'); n=len(paras)
parts=['\n\n'.join(paras[:n//3]),'\n\n'.join(paras[n//3:2*n//3]),'\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts,1):
 out=root/f'episodes/ep{ep:03d}_part{i}.mp3'
 r=requests.post('https://crazyrouter.com/v1/audio/speech',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':'tts-1','voice':'alloy','input':part},timeout=300)
 print('part',i,r.status_code,flush=True); r.raise_for_status(); out.write_bytes(r.content)
concat=root/f'episodes/ep{ep:03d}_concat.txt'; concat.write_text(''.join(f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1,4)))
audio=root/f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(audio)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)],capture_output=True,text=True,check=True)
sec=float(json.loads(r.stdout)['format']['duration']); dur=f'{int(sec//60)}:{int(sec%60):02d}'; size=audio.stat().st_size
feed=root/'feed.xml'; tree=ET.parse(feed); channel=tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date
 enc=ET.SubElement(item,'enclosure'); enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'); enc.set('length',str(size)); enc.set('type','audio/mpeg')
 ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=dur; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text=f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
 items=channel.findall('item'); channel.insert(list(channel).index(items[0]) if items else len(list(channel)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
ET.parse(feed); print('DONE',audio,size,dur)
