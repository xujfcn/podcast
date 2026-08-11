from pathlib import Path
import json,re,subprocess,time,xml.etree.ElementTree as ET,requests
root=Path('/root/.openclaw/workspace/podcast'); ep=124
title='EP124: Prompt Caching for AI APIs — Cut Cost Without Cutting Quality'
description='A practical guide to prompt caching for AI APIs: identify reusable prefixes, measure real savings, manage invalidation and privacy, and combine caching with model routing.'
pub_date='Wed, 12 Aug 2026 08:30:00 +0000'
script='''EP124: Prompt Caching for AI APIs — Cut Cost Without Cutting Quality

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about prompt caching: one of the most practical ways to reduce AI API cost and latency without switching to a weaker model. When many requests share the same instructions, documents, examples, or tool definitions, paying to process that unchanged prefix every time is wasteful.

Start by understanding what can be reused. Common candidates include a long system prompt, product documentation, policy text, coding conventions, few-shot examples, and large tool schemas. Keep stable content at the beginning of the prompt and put request-specific content later. Providers usually identify reusable prefixes, so changing one early token can invalidate much more of the cache than expected.

Measure before optimizing. Record input tokens, cached input tokens, output tokens, latency, and cost for each route. Compare cold requests with warm requests using realistic traffic. A cache hit percentage alone is not enough; calculate actual dollars saved and time-to-first-token improvement.

Design prompts for stability. Separate durable instructions from frequently changing context. Avoid timestamps, random identifiers, and per-user values inside a reusable prefix unless they are required. Canonicalize tool definitions and JSON formatting so semantically identical prompts do not differ because of whitespace or key order.

Caching does not mean storing every response. Prompt caching generally reuses processed input context, while response caching returns a previously generated answer. They solve different problems. Response caching is useful for deterministic repeated questions, but it needs careful freshness, permission, and personalization rules.

Plan cache invalidation. Version system prompts, policies, tools, and knowledge snapshots. When behavior changes, deliberately move traffic to a new version instead of silently mutating shared content. Keep old versions long enough for in-flight requests, then retire them. Explicit versions also make cost and quality comparisons much easier.

Protect tenant boundaries. Never allow one customer to receive another customer's private prompt or cached response. Even when a provider manages prompt caching internally, avoid mixing sensitive tenant-specific content into a shared application prefix. Apply the same retention, encryption, and access-control policies used for prompts and logs.

Combine caching with model routing. A premium model with a high cache-hit rate may become cost-effective for workloads with large repeated context. A smaller model may still be better for short routine tasks. Compare cost per successful outcome after caching, not only the published uncached token price.

Watch operational edge cases. Cache behavior can differ by provider, model, region, account, and minimum prompt length. Entries may expire sooner than expected, and traffic bursts can produce cold starts. Build your economics around observed hit rates instead of assuming every request will be warm.

Test quality after restructuring prompts. Moving instructions or examples to improve cache reuse can change model behavior. Run regression evaluations for instruction following, tool selection, formatting, safety, and factual accuracy. Cost savings are useful only if the task still succeeds.

A simple rollout works well. First identify the routes with the largest repeated input. Then stabilize and version their prefixes. Enable caching for a small traffic slice, measure cold and warm behavior, and expand only when quality remains stable. Report monthly savings and latency changes so the optimization stays visible.

The practical lesson is simple. Put stable context first, remove unnecessary variability, measure cached tokens and successful outcomes, version your prefixes, and protect tenant data. With a unified API gateway such as Crazyrouter, you can combine prompt caching, routing, fallbacks, and usage analytics behind one API.

That is it for today. Stop paying repeatedly for context that has not changed. Visit crazyrouter.com, and see you in the next episode.'''
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
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3',length=str(size),type='audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=duration; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text='https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep124'; old=ch.findall('item'); ch.insert(list(ch).index(old[0]) if old else len(list(ch)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
print('DONE',audio,size,duration)
