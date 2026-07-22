from pathlib import Path
import json, re, subprocess, xml.etree.ElementTree as ET
import requests

root = Path('/root/.openclaw/workspace/podcast')
ep = 102
title = 'EP102: AI API Failover Drills — Test Recovery Before Production Breaks'
description = 'How to run practical AI API failover drills covering timeouts, rate limits, invalid output, provider outages, routing, idempotency, and recovery metrics.'
pub_date = 'Wed, 22 Jul 2026 08:30:00 +0000'
script = '''EP102: AI API Failover Drills — Test Recovery Before Production Breaks

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about failover drills: controlled tests that prove your AI application can recover when a model or provider stops behaving normally.

Most teams add a fallback model and assume the reliability problem is solved. But a fallback that has never been tested is only a configuration value. Production recovery depends on detection, routing, request state, output validation, and the ability to avoid duplicate side effects.

Start with a clear failure catalog. Test connection timeouts, slow first-token latency, rate limits, provider errors, authentication failures, malformed JSON, truncated output, empty responses, unsafe tool calls, and answers that are syntactically valid but fail the task. Each class needs a specific response. Some calls should be retried, some rerouted, and some rejected immediately.

The first drill is a hard provider outage. Force the primary route to return an error and confirm that traffic moves to the approved fallback. Measure how long detection takes, how many requests fail before the route changes, and whether the fallback has enough capacity. Verify that alerts include the provider, model, region, error category, and affected request count.

The second drill is a slow degradation. Add latency rather than returning a clean error. This is often more dangerous because requests remain open, consume concurrency, and trigger retries upstream. Define separate budgets for connection time, time to first token, and total completion time. A route should not wait forever merely because bytes are still arriving.

The third drill is invalid output. Return malformed JSON, a missing required field, or code that does not compile. Your application should treat validation failure as a first-class result, not as success. Record the failed validation rule and decide whether repair, retry, or rerouting is appropriate for that task.

The fourth drill covers rate limits. Confirm that exponential backoff includes jitter and respects provider retry guidance. Check that multiple workers do not create a retry storm. A shared queue or circuit breaker should reduce pressure rather than multiplying calls during an incident.

The fifth drill is duplicate prevention. Simulate a timeout after a provider or tool has already completed the work. Stable idempotency keys and request state should stop a retry from charging a customer twice, sending two emails, creating two records, or executing the same tool action again.

Test fallback compatibility as well. Models differ in context limits, tool-call formats, structured output support, safety behavior, and parameter handling. The fallback route must receive a request it actually supports. Normalize the interface at the gateway, but still validate model-specific capabilities before routing.

During every drill, collect operational metrics: accepted-result rate, p95 latency, time to detection, time to recovery, retry amplification, fallback share, validation failures, and cost per accepted result. A successful failover is not simply one that returns HTTP 200. It must preserve useful output, budget, and side-effect safety.

Run drills with a replay set before testing live traffic. Then use a small canary percentage in production, with a rollback switch and clear ownership. Schedule these exercises after major routing changes, provider migrations, SDK upgrades, and new tool integrations.

The final deliverable should be a short runbook. List the trigger, expected route, timeout budget, retry policy, fallback order, validation gate, alert destination, rollback step, and person responsible. Keep it close to the system that executes the policy so documentation and behavior do not drift apart.

Reliable AI systems are not those that never fail. They are systems that recognize failure quickly, contain it, recover predictably, and preserve enough evidence to explain what happened.

That is it for today. Test your fallback before you need it. Try the unified API at crazyrouter.com, and see you in the next episode.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8')
key = re.search(r'\*\*CrazyRouter\*\*:\s+(sk-[A-Za-z0-9_\-]+)', tools).group(1)
paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_part{i}.mp3'
    response = requests.post(
        'https://crazyrouter.com/v1/audio/speech',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
        timeout=300,
    )
    print('part', i, response.status_code, flush=True)
    response.raise_for_status()
    out.write_bytes(response.content)

concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1, 4)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c', 'copy', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size

feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((item.findtext('title') or '').startswith(f'EP{ep:03d}:') for item in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enclosure = ET.SubElement(item, 'enclosure')
    enclosure.set('url', f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enclosure.set('length', str(size))
    enclosure.set('type', 'audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    existing = channel.findall('item')
    channel.insert(list(channel).index(existing[0]) if existing else len(list(channel)), item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)

print('DONE', audio, size, duration)
