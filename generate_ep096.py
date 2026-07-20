from pathlib import Path
import json, re, subprocess, time, xml.etree.ElementTree as ET
import requests

root=Path('/root/.openclaw/workspace/podcast'); ep=96
title='EP096: The Real Cost of AI API Failures — Retries, Truncation, and Routing'
description='A practical guide to measuring AI API reliability beyond HTTP 200: incomplete outputs, retries, validation, fallback routing, and cost per accepted result.'
pub_date='Mon, 20 Jul 2026 08:00:00 +0000'
script='''EP096: The Real Cost of AI API Failures — Retries, Truncation, and Routing

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about a metric that is easy to ignore and expensive to miss: the cost of an AI API failure.

Many teams start with a simple question: what does one million tokens cost? That is useful, but it is not enough. A production request can return HTTP 200, consume tokens, and still fail the application because the output was truncated, invalid JSON, incomplete code, or missing a required field.

The first rule is to separate transport success from task success. Transport success means the request reached the provider and the server returned a response. Task success means the response passed the checks your application actually needs. Those are different events and should be logged separately.

At the gateway layer, record the provider, model, request ID, latency, input and output tokens, finish reason, retry count, validation result, and final route. For structured output, also record the schema version and the validation error category. This turns a vague complaint such as the model failed into an observable failure mode.

The most common failure is truncation. A response can end with finish_reason equal to length even when the beginning looks excellent. For a long coding answer, the missing section may contain the final function, the tests, or the error handling. The correct behavior is not to blindly accept the answer. Mark it incomplete, then retry with a larger output budget, a smaller prompt, a split task, or a different model.

The second failure is invalid structure. If a workflow asks for JSON, parse it before handing it to downstream code. Do not repair arbitrary text with increasingly complicated regular expressions. Prefer a provider-supported structured-output mode when available, validate against a schema, and return the exact validation error to the retry policy.

The third failure is semantic. A response can be valid JSON and still contain the wrong unit, an impossible date, an empty list, or a value outside an allowed range. Add domain checks: dimensions for physics, boundary cases for time windows, syntax and tests for code, and independent calculations for important numbers.

Retries have a cost, but no retry policy is also costly. The useful metric is cost per accepted result. If a cheap model succeeds once out of two attempts and a more expensive model succeeds on the first attempt, the cheaper model may not be cheaper in the workflow. Include retry tokens, validation calls, latency, and human repair time when comparing routes.

A practical retry policy should be narrow. Retry transient transport errors with backoff. Retry rate limits according to the provider's retry-after signal. Retry truncation by changing the output budget or splitting the task. Retry schema failures with a constrained repair prompt. Do not retry an obviously unsupported task forever; route it to a model or tool that can actually complete it.

Fallback routing works best when it is step-aware. If only the code-generation step fails, send that step to the fallback model instead of repeating research, planning, and context loading. Preserve the same request ID and record the original failure so the final result can be audited.

Streaming introduces another important distinction. A stream can deliver useful partial text before a disconnect, but partial text is not automatically a valid result. For prose, partial recovery may be acceptable. For code or JSON, it usually is not. Define completion criteria per output type and enforce them after the stream closes.

The dashboard should show accepted-result rate, not just provider uptime. Useful panels include success rate by model and task type, truncation rate, schema failure rate, p95 latency, retry amplification, average cost per accepted result, and fallback share. Break these down by prompt version because a routing change can look like a model regression when the real cause is a larger prompt.

The implementation pattern is simple. Put a validation gate after every model call. Give the gate a typed result such as accepted, retryable, reroutable, or rejected. Attach a reason code. Then let the gateway make a policy decision instead of leaving every client to reinvent failure handling.

The larger lesson is that AI reliability is an application property. Providers matter, models matter, and price matters, but the accepted result is what creates value. Measure the complete workflow, make failure visible, and route based on the type of work rather than a single leaderboard number.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. Try the unified API at crazyrouter.com, and see you in the next episode.'''
(root/'episodes').mkdir(exist_ok=True); (root/'audio').mkdir(exist_ok=True)
(root/f'episodes/ep{ep:03d}_script.txt').write_text(script,encoding='utf-8')
tools=Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8'); m=re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)',tools)
if not m: raise SystemExit('API key not found')
key=m.group(1); paras=script.split('\n\n'); n=len(paras); parts=['\n\n'.join(paras[:n//3]),'\n\n'.join(paras[n//3:2*n//3]),'\n\n'.join(paras[2*n//3:])]
for i,part in enumerate(parts,1):
 out=root/f'episodes/ep{ep:03d}_part{i}.mp3'; r=requests.post('https://crazyrouter.com/v1/audio/speech',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':'tts-1','voice':'alloy','input':part},timeout=300); print('part',i,r.status_code,flush=True); r.raise_for_status(); out.write_bytes(r.content)
concat=root/f'episodes/ep{ep:03d}_concat.txt'; concat.write_text(''.join(f"file \'ep{ep:03d}_part{i}.mp3\'\n" for i in range(1,4)))
audio=root/f'audio/ep{ep:03d}.mp3'; subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(audio)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)],capture_output=True,text=True,check=True); sec=float(json.loads(r.stdout)['format']['duration']); dur=f'{int(sec//60)}:{int(sec%60):02d}'; size=audio.stat().st_size
feed=root/'feed.xml'; tree=ET.parse(feed); channel=tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'); enc.set('length',str(size)); enc.set('type','audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=dur; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text=f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'; items=channel.findall('item'); channel.insert(list(channel).index(items[0]) if items else len(list(channel)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
ET.parse(feed); print('DONE',audio,size,dur)
