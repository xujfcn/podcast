from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 173
title = 'EP173: AI API Contract Testing — Survive Model and Provider Churn'
description = 'A practical guide to AI API contract testing: define behavioral contracts, probe model capabilities, validate structured outputs, and catch provider changes before they break production workflows.'
pub_date = 'Wed, 30 Sep 2026 08:30:00 +0000'
script = '''EP173: AI API Contract Testing — Survive Model and Provider Churn

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Model APIs are moving targets. A provider can change a model version, latency profile, tool-calling behavior, or structured-output edge case without changing the shape of a familiar endpoint. Today we will build AI API contract tests that catch those changes before they become production incidents.

Start by defining the contract at the level your application actually depends on. The endpoint and HTTP status are not enough. Record the required input fields, supported modalities, tool schema, output shape, refusal behavior, latency budget, token limits, and the actions that may follow a response. A contract is a promise about usable behavior, not just a URL.

Separate hard requirements from quality expectations. A JSON object with the required fields may be a hard requirement. A concise answer, a particular style, or a target accuracy may be a quality expectation. This distinction lets your gateway route requests intelligently: hard failures can trigger a fallback, while softer regressions can create an alert or send traffic to evaluation.

Build a small golden corpus. Include ordinary requests, long-context cases, empty and malformed inputs, multilingual examples, tool calls, refusals, and adversarial prompts. Keep the corpus versioned and remove private customer data. The goal is not to test every possible conversation. It is to maintain a compact set of cases that represent the failure modes your product cannot afford.

Test capabilities before routing traffic. A provider may claim compatibility with an OpenAI-style API while differing on JSON schema enforcement, parallel tool calls, streaming chunks, image inputs, or finish reasons. Run a capability probe when a route is added or changed. Save the result with the model identifier, provider, timestamp, and test-suite version.

Validate structured output as data. Parse the response, validate it against the schema, reject extra fields when they are unsafe, and check semantic constraints that a JSON parser cannot see. For example, a currency amount should be non-negative, a date should be valid, and a tool argument should reference an allowed resource. Never let “valid JSON” stand in for “safe to execute.”

Exercise streaming separately. Streaming introduces partial objects, duplicated chunks, reordered events, disconnects, and usage metadata that arrives at the end. Your contract tests should reconstruct the final response, verify event ordering, handle an interrupted stream, and confirm that cancellation stops downstream work. A non-streaming test cannot prove that the streaming path is reliable.

Measure latency in stages. Record time to first token, time between chunks, total completion time, queue delay, and retry time. A route can have an acceptable average while violating the interactive SLO for the first token. Put budgets around each stage and test both a warm request and a cold or rate-limited request.

Test error translation at the gateway boundary. Upstream providers expose different status codes and error formats. Your application should receive a stable error taxonomy for authentication, quota, throttling, invalid input, safety refusal, timeout, overload, and transient provider failure. Verify that retries happen only for retryable classes and that a fallback does not repeat a non-retryable mistake.

Use shadow and canary evaluation for upgrades. Run the new model or provider against a safe sample without changing user-visible results. Compare schema pass rate, tool-call accuracy, refusal patterns, latency, token use, and cost per successful task. During a canary, cap traffic and define rollback thresholds before the experiment starts. A gateway such as Crazyrouter can centralize the route split, but the acceptance criteria must belong to the workload owner.

Watch for silent semantic drift. A model may keep the same schema while changing how it interprets a field, when it calls a tool, or how often it refuses. Add assertions about invariants and important decisions, not only snapshots of exact wording. Prefer rubric-based evaluation, deterministic checks, and human review for a small sample over brittle string comparisons.

Treat contract failures as release blockers according to risk. A missing optional style preference should not stop a deployment. A tool argument that can send money, delete data, or expose another tenant should. Define severity, owner, and response for each failed assertion. Store the evidence so an engineer can reproduce the failure without guessing which model version was active.

Keep contracts close to code and operations. Put schemas, probes, fixtures, thresholds, and route metadata in version control. Publish the suite in CI for deterministic checks, then run scheduled live probes for provider behavior and latency. Alert on meaningful regressions, not every noisy sample. When a provider changes, the first question should be whether the contract still holds.

The practical lesson is simple: compatibility is something you measure. Define the behavior your application needs, probe capabilities, validate outputs semantically, test streaming and errors, and canary changes with explicit rollback thresholds. Model choice becomes safer when every route has an executable contract.

That is it for today. Test the contract before trusting the route, and see you in the next episode. Visit crazyrouter.com to route your AI workloads through one reliable API gateway.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(root / f'episodes/ep{ep:03d}_chunk{i}.mp3')], check=True)
concat = root / f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join(f"file 'ep{ep:03d}_chunk{i}.mp3'\n" for i in range(1, len(parts) + 1)))
audio = root / f'audio/ep{ep:03d}.mp3'
subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat), '-c:a', 'libmp3lame', '-q:a', '4', str(audio)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
probe = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', str(audio)], capture_output=True, text=True, check=True)
seconds = float(json.loads(probe.stdout)['format']['duration'])
duration = f'{int(seconds // 60)}:{int(seconds % 60):02d}'
size = audio.stat().st_size
feed = root / 'feed.xml'
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
if not any((x.findtext('title') or '').startswith(f'EP{ep:03d}:') for x in channel.findall('item')):
    item = ET.Element('item')
    ET.SubElement(item, 'title').text = title
    ET.SubElement(item, 'description').text = description
    ET.SubElement(item, 'pubDate').text = pub_date
    enc = ET.SubElement(item, 'enclosure')
    enc.attrib.update(url=f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3', length=str(size), type='audio/mpeg')
    ET.SubElement(item, 'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ns = 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    ET.SubElement(item, f'{{{ns}}}duration').text = duration
    ET.SubElement(item, f'{{{ns}}}episode').text = str(ep)
    ET.SubElement(item, f'{{{ns}}}episodeType').text = 'full'
    ET.SubElement(item, f'{{{ns}}}explicit').text = 'false'
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep173'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
