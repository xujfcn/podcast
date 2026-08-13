from pathlib import Path
import json,re,subprocess,time,xml.etree.ElementTree as ET,requests
root=Path('/root/.openclaw/workspace/podcast'); ep=128
title='EP128: AI API Testing — Build Regression Checks Before Users Find Bugs'
description='A practical guide to testing AI API applications: build representative cases, validate structured outputs, test tools and fallbacks, and catch regressions before production.'
pub_date='Sun, 16 Aug 2026 08:30:00 +0000'
script='''EP128: AI API Testing — Build Regression Checks Before Users Find Bugs

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about testing AI API applications. Traditional unit tests still matter, but they cannot fully describe a system whose outputs vary, tools fail, providers throttle, and prompts evolve. Reliable AI testing combines deterministic checks with representative examples and production evidence.

Start with the contract. Define what the application promises: required fields, allowed actions, latency targets, safety rules, citation behavior, and success conditions. Deterministic contract tests can then verify JSON schemas, tool arguments, status handling, and error formats even when the generated wording changes.

Build a small representative dataset. Include common requests, difficult cases, multilingual inputs, long contexts, ambiguous instructions, adversarial content, and recent production failures. Each example should explain what behavior matters and what would count as failure. A focused set that the team reviews beats a huge unmaintained prompt dump.

Separate test layers. Unit-test routing decisions, prompt construction, parsers, redaction, retry limits, and budget checks without calling a model. Integration-test provider adapters, streaming, structured outputs, tool calls, and fallbacks. End-to-end tests should exercise the complete user task with realistic dependencies and controlled test accounts.

Use assertions that match the task. Exact string matching is brittle for open-ended answers. Prefer schema validity, required facts, citation presence, successful tool completion, code tests, policy compliance, and task-level outcomes. For subjective quality, use calibrated human review or a model judge checked against human decisions.

Test failure paths deliberately. Simulate 429 responses, timeouts, truncated streams, malformed JSON, provider errors, invalid tools, retrieval misses, and partial results. Verify that retries stop at the deadline, fallbacks preserve the contract, errors are safe to show users, and side effects are not duplicated.

Protect test data. Remove unnecessary personal information, use synthetic accounts for tools and payments, and never put production credentials in fixtures. Test logs and traces too: a failure report should not accidentally print API keys, private prompts, or customer documents.

Watch for prompt and model drift. Pin model versions where reproducibility matters, record prompt and policy versions, and keep a change history. When a provider updates behavior, rerun the regression set. A test result without its model, prompt, route, and date is difficult to interpret.

Add online checks carefully. Sample production outcomes, user corrections, escalations, invalid-output rates, and fallback spikes. Feed confirmed failures back into the regression set. Do not treat every re-prompt as a failure automatically; users can change their minds or ask follow-up questions.

Set release gates. Define which checks must pass before changing a route or prompt. For important workflows, require quality not to drop beyond a threshold and require cost and latency to remain within budget. Run canaries before full rollout and keep a rollback path.

Make failures actionable. Classify them as missing context, wrong route, instruction conflict, hallucination, formatting error, tool failure, policy refusal, or timeout. Link each class to an owner and a new test. The purpose of testing is not to produce a score; it is to make the next release safer.

The practical lesson is simple. Test the contract, the route, the provider adapter, the tools, the failure paths, and the complete task. With a unified API gateway such as Crazyrouter, centralized routing and model access make it easier to run consistent regression checks across providers.

That is it for today. Find the bugs in evaluation before users find them in production. Visit crazyrouter.com, and see you in the next episode.'''
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
 item=ET.Element('item'); ET.SubElement(item,'title').text=title; ET.SubElement(item,'description').text=description; ET.SubElement(item,'pubDate').text=pub_date; enc=ET.SubElement(item,'enclosure'); enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3',length=str(size),type='audio/mpeg'); ET.SubElement(item,'guid').text=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'; ns='http://www.itunes.com/dtds/podcast-1.0.dtd'; ET.SubElement(item,f'{{{ns}}}duration').text=duration; ET.SubElement(item,f'{{{ns}}}episode').text=str(ep); ET.SubElement(item,f'{{{ns}}}episodeType').text='full'; ET.SubElement(item,f'{{{ns}}}explicit').text='false'; ET.SubElement(item,'link').text='https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep128'; old=ch.findall('item'); ch.insert(list(ch).index(old[0]) if old else len(list(ch)),item); tree.write(feed,encoding='utf-8',xml_declaration=True)
print('DONE',audio,size,duration)
