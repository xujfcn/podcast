from pathlib import Path
import json,re,subprocess,time,xml.etree.ElementTree as ET,requests
root=Path('/root/.openclaw/workspace/podcast'); ep=126
title='EP126: AI API Security — Keys, Tenants, Logs, and Safe Operations'
description='A practical guide to securing AI API applications: protect keys, isolate tenants, redact logs, control spend, and build safer operational workflows.'
pub_date='Fri, 14 Aug 2026 08:30:00 +0000'
script='''EP126: AI API Security — Keys, Tenants, Logs, and Safe Operations

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about security for AI API applications. The model is only one part of the risk surface. API keys, prompts, tool permissions, tenant data, billing controls, logs, and provider credentials all need clear boundaries if an AI product is going to operate safely.

Start with key hygiene. Never put a production key in frontend code, public repositories, screenshots, prompts, or chat messages. Store secrets in an approved secret manager or protected environment, limit who can read them, and rotate them when a team member leaves or a leak is suspected. Use separate keys for development, staging, production, and automation so one mistake does not expose everything.

Put your own backend between users and the model gateway whenever possible. The backend can authenticate users, apply quotas, select an allowed route, enforce content limits, and keep the provider key private. If a browser must call an API directly, use narrowly scoped short-lived credentials and accept that they are harder to protect than server-side secrets.

Separate tenants by design. Every request should carry a trusted tenant identity from your authentication layer, not an email address supplied by the client. Enforce tenant checks on prompts, files, conversation history, tool results, usage records, and billing data. Test that changing an ID in a request cannot reveal another customer's data.

Treat tools as privileged operations. A model may suggest an action, but your application should decide whether that action is permitted. Validate tool arguments against a strict schema, restrict destinations, require confirmation for irreversible actions, and use separate credentials with the smallest practical permissions. Do not give a general-purpose model unrestricted database, shell, payment, or email access.

Redact logs deliberately. Prompts and responses can contain personal data, credentials, private code, or customer records. Log metadata such as request IDs, model, route, latency, token counts, and outcome by default. If content must be retained for debugging, minimize it, encrypt it, apply a short retention period, and make access auditable. Remember that tracing systems and error dashboards are also data stores.

Control spend as a security measure. Per-key, per-user, and per-tenant rate limits reduce abuse and protect against runaway loops. Add daily or monthly budgets, anomaly alerts, maximum context sizes, and limits on expensive models or media generation. A leaked key is less damaging when it cannot generate an unlimited bill.

Validate external content. Retrieved documents, web pages, emails, and user uploads can contain prompt injection. Keep untrusted text separate from system instructions, label its source, limit what it can influence, and require application-side authorization for every tool call. The model should never be the final authority for permissions.

Secure provider and webhook integrations. Use TLS, verify signatures, validate timestamps, and reject replayed events. Keep provider credentials separate from customer credentials. When using multiple providers, record which data classes are allowed to leave your boundary and choose routes accordingly. Not every prompt should be sent to every provider.

Prepare for incidents. Define how to revoke keys, disable a route, freeze a tenant, preserve relevant evidence, notify affected users, and review the cause. Practice the procedure with a test key. Security controls that require inventing a process during an incident are likely to fail under pressure.

The practical lesson is simple. Keep keys private, isolate tenants, constrain tools, minimize logs, cap spending, treat external content as untrusted, and make revocation fast. With a unified API gateway such as Crazyrouter, centralized routing and usage controls can give teams a consistent security layer without scattering provider secrets across every application.

That is it for today. Build AI systems that are useful without becoming an uncontrolled access path. Visit crazyrouter.com, and see you in the next episode.'''
(root/'episodes').mkdir(exist_ok=True); (root/'audio').mkdir(exist_ok=True)
(root/f'episodes/ep{ep:03d}_script.txt').write_text(script)
tools=Path('/root/.openclaw/workspace/TOOLS.md').read_text(); key=re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)',tools).group(1)
parts=script.split('\n\n')
for i,part in enumerate(parts,1):
 out=root/f'episodes/ep{ep:03d}_chunk{i}.mp3'
 for attempt in range(1,4):
  r=requests.post('https://crazyrouter.com/v1/audio/speech',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':'tts-1','voice':'alloy','input':part},timeout=300)
  print('part',i,r.status_code,flush=True)
  if r.ok: out.write_bytes(r.content); break
  if attempt==3: r.raise_for_status()
  time.sleep(5*attempt)
concat=root/f'episodes/ep{ep:03d}_concat.txt'; concat.write_text(''.join(f"file \'ep{ep:03d}_chunk{i}.mp3\'\n" for i in range(1,len(parts)+1)))
audio=root/f'audio/ep{ep:03d}.mp3'; subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(audio)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)],capture_output=True,text=True,check=True); seconds=float(json.loads(probe.stdout)['format']['duration']); duration=f'{int(seconds//60)}:{int(seconds%60):02d}'; size=audio.stat().st_size
feed=root/'feed.xml'; tree=ET.parse(feed); ch=tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in ch.findall('item')):
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3',length=str(size),type='audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=duration; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text='https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep126'; old=ch.findall('item'); ch.insert(list(ch).index(old[0]) if old else len(list(ch)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
print('DONE',audio,size,duration)
