from pathlib import Path
import json,re,subprocess,xml.etree.ElementTree as ET
import requests

root=Path('/root/.openclaw/workspace/podcast'); ep=101
title='EP101: The Metrics That Matter Before You Switch AI Models'
description='A practical guide to evaluating AI models in production: accepted-result rate, latency, retries, fallback share, and cost per accepted result.'
pub_date='Tue, 21 Jul 2026 15:30:00 +0000'
script='''EP101: The Metrics That Matter Before You Switch AI Models

Welcome back to AI Dev Tools — The Crazyrouter Podcast. After one hundred episodes about models, APIs, gateways, and developer workflows, today we are focusing on a question teams often ask too early: should we switch models?

The answer should not begin with a leaderboard. It should begin with a measurement plan. A model is useful when it produces an accepted result for a real task, within the latency and budget that your product can tolerate.

Start with accepted-result rate. Define what good means for each workflow. For extraction, the output may need to match a schema and pass field validation. For code generation, it may need to compile and pass a replayed test set. For customer support, it may need to follow policy and receive a positive review. HTTP 200 is only transport success; it is not task success.

Next, measure latency by percentile rather than average. Averages hide the slow tail. Track p50, p95, and p99 time to first token and time to final result. A slightly slower model may be the better choice if it avoids retries, repairs, and fallbacks. Conversely, a fast model may be ideal for short classification or routing decisions.

Measure retry amplification. If one accepted result requires 1.4 provider calls on average, your apparent token price is not your real cost. Include timeouts, malformed JSON, truncated answers, rate-limit retries, and fallback calls. The operational unit is cost per accepted result, not cost per million input tokens.

Record fallback share as well. Fallbacks are valuable when they improve reliability, but a rising fallback rate can signal a provider problem, a bad route, an overloaded model, or an unrealistic prompt. Break the metric down by model, provider, region, task type, and time window.

Do not forget consistency. A model that produces one excellent answer and one unusable answer may be less valuable than a slightly weaker model with stable behavior. Replay a fixed evaluation set, then sample real production requests with privacy controls. Compare schema validity, refusal behavior, tool-call correctness, and regression rates.

Cost needs context. Include input and output tokens, caching, retries, validation calls, image or audio charges, and human review. If a model saves ten cents per request but creates a support ticket every hundred requests, the saving may be imaginary. Build a cost model around the complete workflow.

Routing should follow task shape. Use cheaper and faster routes for predictable transformations. Reserve stronger models for ambiguity, long context, difficult code, or recovery from a failed first attempt. Keep the application interface stable so that routing policy can change without rewriting business logic.

Finally, define a switch threshold before you run the comparison. For example: move traffic only if accepted-result rate improves by three percentage points, p95 latency stays below the product budget, and cost per accepted result falls by ten percent. Predefined thresholds protect teams from choosing a model because of one impressive demo.

The practical workflow is simple: build a replay set, define acceptance tests, collect provider and route metadata, compare percentiles, calculate retry-adjusted cost, run a controlled rollout, and keep a rollback path. A model switch is an operational change, not just a configuration edit.

That is it for today. Before switching models, measure what your users actually accept. Try the unified API at crazyrouter.com, and see you in the next episode.'''
(root/'episodes').mkdir(exist_ok=True); (root/'audio').mkdir(exist_ok=True)
(root/f'episodes/ep{ep:03d}_script.txt').write_text(script,encoding='utf-8')
tools=Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8'); key=re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)',tools).group(1)
paras=script.split('\n\n'); n=len(paras); parts=['\n\n'.join(paras[:n//3]),'\n\n'.join(paras[n//3:2*n//3]),'\n\n'.join(paras[2*n//3:])]
for i,part in enumerate(parts,1):
 out=root/f'episodes/ep{ep:03d}_part{i}.mp3'; r=requests.post('https://crazyrouter.com/v1/audio/speech',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':'tts-1','voice':'alloy','input':part},timeout=300); print('part',i,r.status_code,flush=True); r.raise_for_status(); out.write_bytes(r.content)
concat=root/f'episodes/ep{ep:03d}_concat.txt'; concat.write_text(''.join(f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1,4)))
audio=root/f'audio/ep{ep:03d}.mp3'; subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(audio)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)],capture_output=True,text=True,check=True); sec=float(json.loads(r.stdout)['format']['duration']); dur=f'{int(sec//60)}:{int(sec%60):02d}'; size=audio.stat().st_size
feed=root/'feed.xml'; tree=ET.parse(feed); channel=tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'); enc.set('length',str(size)); enc.set('type','audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=dur; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text=f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'; items=channel.findall('item'); channel.insert(list(channel).index(items[0]) if items else len(list(channel)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
print('DONE',audio,size,dur)
