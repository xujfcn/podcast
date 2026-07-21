from pathlib import Path
import json,re,subprocess,xml.etree.ElementTree as ET
import requests
root=Path('/root/.openclaw/workspace/podcast'); ep=99
title='EP099: Idempotency for AI APIs — Preventing Duplicate Work and Duplicate Charges'
description='How to make AI API workflows safe under retries: idempotency keys, request state, streaming recovery, tool side effects, and billing reconciliation.'
pub_date='Wed, 22 Jul 2026 08:00:00 +0000'
script='''EP099: Idempotency for AI APIs — Preventing Duplicate Work and Duplicate Charges

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about idempotency: the design property that keeps a retry from becoming duplicate work, a duplicate tool call, or a duplicate charge.

AI API requests fail in uncomfortable ways. A client may time out even though the provider completed the generation. A stream may disconnect after a tool call was accepted. A gateway may retry after a network reset without knowing whether the first request reached the provider. If the operation has side effects, repeating it blindly is dangerous.

The first building block is an idempotency key. The client creates a stable key for one logical operation and sends it with every retry. The gateway stores the key, request fingerprint, current state, and final result. A repeated request with the same key returns the existing result instead of starting new work.

The key must describe the logical operation, not merely the transport attempt. A new HTTP connection or a new provider request should not create a new logical key. At the same time, the gateway must reject reuse of a key with a different request body. Otherwise a stale key can accidentally return the wrong result.

Use explicit states: received, running, completed, failed, and expired. A second request that arrives while the first is running can wait, receive a polling response, or get a clear in-progress status. It should not start a second provider call unless the policy has a deliberate lease-recovery rule.

Leases matter when workers crash. Store an owner, heartbeat, and expiration time. If a worker disappears, another worker can safely take over only after the lease expires. The recovery path should record the takeover and preserve the original idempotency key.

Streaming needs special care. Persist completed chunks or a resumable cursor when the product requires recovery. If that is too expensive, define the stream as advisory and require a final fetch by request ID. The client should be able to ask whether the logical operation completed, rather than guessing from a broken connection.

Tool calls are the hardest case. Reading data is usually easier to retry than sending an email, creating an order, or charging a card. Give every side-effecting tool call its own idempotency key and make the tool provider honor it. If the provider cannot guarantee this, place the action behind a durable command queue and reconcile the result before retrying.

Billing must be reconciled separately from response delivery. A client timeout does not prove that usage was not incurred. Record provider request IDs, usage events, and customer-facing charge IDs. When a retry happens, link it to the same logical request and make the billing policy explicit.

Idempotency keys should have a retention period. Keep them long enough to cover client retries, queue delays, and support investigations. Expiration must be visible: after a key expires, a repeated request may be treated as new work, but the API should return that behavior clearly.

Test the failure matrix: timeout before send, timeout after send, gateway crash, worker crash, provider duplicate response, stream disconnect, tool success with lost acknowledgement, and billing event delayed. The happy path is the least interesting test.

The result is a safer AI gateway. Retries can improve reliability without multiplying cost or side effects. Request IDs make the operation traceable, idempotency keys make it repeatable, and reconciliation makes uncertainty manageable.

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
