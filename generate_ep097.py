from pathlib import Path
import json,re,subprocess,xml.etree.ElementTree as ET
import requests
root=Path('/root/.openclaw/workspace/podcast'); ep=97
title='EP097: Building a Reliable AI API Gateway — Timeouts, Budgets, and Observability'
description='A practical architecture guide for reliable AI API gateways: deadlines, retries, token budgets, streaming, validation, fallback routing, and observability.'
pub_date='Mon, 20 Jul 2026 18:30:00 +0000'
script='''EP097: Building a Reliable AI API Gateway — Timeouts, Budgets, and Observability

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are designing a reliable AI API gateway. Not a gateway that simply forwards requests, but one that understands deadlines, budgets, validation, retries, and the difference between a response and a usable result.

The first design decision is to treat every request as a budget. The budget includes wall-clock time, input tokens, output tokens, retry attempts, and money. If the gateway does not track those limits explicitly, a single slow or incomplete provider call can consume the entire user experience.

Start with a deadline, not an arbitrary timeout. The client should send a request deadline when possible. The gateway computes the remaining time before each provider call and reserves time for validation and response delivery. A retry is only allowed if enough time remains for the retry to be useful.

Next, separate retryable failures from permanent failures. Network resets, selected 5xx responses, and rate limits may be retryable. Invalid authentication, unsupported parameters, malformed schemas, and policy denials are not fixed by repeating the same request. Every failure should receive a reason code so routing decisions can be inspected later.

Token budgets need the same discipline. An output limit that is too small causes truncation; a limit that is too large increases cost and latency. For long technical work, the gateway can use staged generation: ask for a plan, generate one section, validate it, and continue. This is often more reliable than asking for one enormous answer.

Streaming changes the failure model. A stream may deliver useful text before a disconnect, but partial content is not automatically a completed result. For prose, partial recovery may be acceptable. For JSON, code, and tool calls, the gateway should require a completion marker, parseability, or a successful validation step before marking the request accepted.

Structured output should be validated at the gateway boundary. Parse JSON, check the schema, and classify the result as accepted, retryable, reroutable, or rejected. Do not hide validation failures behind a generic 200 response. Downstream systems need to know whether they received a complete result.

Fallback routing should preserve context without repeating unnecessary work. If a model fails during code generation, route only that step to a fallback model. Keep the original request ID, model choice, finish reason, and validation error. This makes the final answer auditable and prevents duplicate billing caused by restarting the entire workflow.

Observability is the feature that makes all of this operable. Log provider, model, request ID, latency, token usage, finish reason, retry count, validation status, and final outcome. Build dashboards for accepted-result rate, p95 latency, truncation rate, schema failures, retry amplification, fallback share, and cost per accepted result.

Privacy matters too. Request logs should use redaction and configurable retention. Store enough metadata to debug routing without keeping sensitive prompts forever. Separate operational identifiers from customer content, and make access to detailed traces auditable.

A useful test suite should include provider timeouts, rate limits, malformed JSON, truncated code, duplicate requests, clock-boundary timestamps, streaming disconnects, and fallback exhaustion. Reliability is not proven by a successful happy-path demo. It is proven by predictable behavior when dependencies fail.

The gateway should also expose transparent response metadata. Clients benefit from knowing whether a result was retried, which model completed it, and whether validation passed. The exact provider details may be optional, but the acceptance state should never be ambiguous.

The core principle is simple: an AI API gateway is a reliability layer. It controls time, cost, correctness, and observability across changing model providers. Forwarding tokens is easy. Delivering an accepted result under a clear budget is the real product.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. Try the unified API at crazyrouter.com, and see you in the next episode.'''
(root/'episodes').mkdir(exist_ok=True); (root/'audio').mkdir(exist_ok=True)
(root/f'episodes/ep{ep:03d}_script.txt').write_text(script,encoding='utf-8')
tools=Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8'); key=re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)',tools).group(1)
paras=script.split('\n\n'); n=len(paras); parts=['\n\n'.join(paras[:n//3]),'\n\n'.join(paras[n//3:2*n//3]),'\n\n'.join(paras[2*n//3:])]
for i,part in enumerate(parts,1):
 out=root/f'episodes/ep{ep:03d}_part{i}.mp3'; r=requests.post('https://crazyrouter.com/v1/audio/speech',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':'tts-1','voice':'alloy','input':part},timeout=300); print('part',i,r.status_code,flush=True); r.raise_for_status(); out.write_bytes(r.content)
concat=root/f'episodes/ep{ep:03d}_concat.txt'; concat.write_text(''.join(f"file \'ep{ep:03d}_part{i}.mp3\'\n" for i in range(1,4)))
audio=root/f'audio/ep{ep:03d}.mp3'; subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(audio)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)],capture_output=True,text=True,check=True); sec=float(json.loads(r.stdout)['format']['duration']); dur=f'{int(sec//60)}:{int(sec%60):02d}'; size=audio.stat().st_size
feed=root/'feed.xml'; tree=ET.parse(feed); channel=tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'); enc.set('length',str(size)); enc.set('type','audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=dur; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text=f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'; items=channel.findall('item'); channel.insert(list(channel).index(items[0]) if items else len(list(channel)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
print('DONE',audio,size,dur)
