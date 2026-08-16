from pathlib import Path
import subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
ep = 146
title = 'EP146: AI API FinOps — Turn Model Spend Into an Operating Practice'
description = 'A practical guide to AI API FinOps: allocate model spend, set budgets, measure cost per outcome, detect waste, and give teams useful controls without slowing delivery.'
pub_date = 'Thu, 3 Sep 2026 08:30:00 +0000'
script = '''EP146: AI API FinOps — Turn Model Spend Into an Operating Practice

Welcome back to AI Dev Tools — The Crazyrouter Podcast. AI API usage can grow faster than the product team expects. A new feature adds a longer prompt, an agent retries more often, or a model upgrade changes the price and suddenly the monthly bill no longer explains itself. Today we will turn AI spend into an operating practice that helps teams control cost without blocking useful work.

Start with attribution. Record the service, feature, tenant, environment, model, route, request type, input tokens, output tokens, cached tokens, retries, fallbacks, and effective price. A single total is useful for accounting but useless for deciding what to change. A gateway such as Crazyrouter can centralize model access and usage accounting while applications attach the product identity needed for allocation.

Measure cost per outcome. Cost per request is not enough when outputs vary in length or require repair. Track cost per accepted result, completed document, resolved support case, successful tool action, or other product outcome. A cheaper model that creates more retries or human review may have a higher real cost.

Create budgets at multiple levels. Set a monthly forecast for the organization, limits for products and tenants, and per-request caps for prompts, output tokens, tool calls, and retries. Separate hard safety limits from alerts and soft targets. Developers should know whether a request was rejected, degraded, or merely approaching a budget.

Forecast from usage drivers. Model spend usually follows a small number of factors: active users, requests per user, input size, output size, model mix, retry rate, and feature adoption. Build a simple forecast from those drivers and compare it with actual usage each week. Large gaps are signals to investigate, not reasons to guess.

Find waste patterns. Look for repeated prompts, excessive history, oversized tool results, unnecessary high-end routing, abandoned streams, retry loops, and batch jobs running at the wrong priority. Use traces and cost metadata to connect the bill to a behavior engineers can actually fix. Do not optimize only the provider price while ignoring application waste.

Use routing policies deliberately. A smaller model may handle classification or extraction, while a stronger route is reserved for ambiguous reasoning. Cache stable work, batch offline jobs, and set context budgets where quality allows. Keep quality and latency thresholds beside cost thresholds so optimization does not quietly damage the user experience.

Make chargeback useful, not punitive. Show teams their usage with enough detail to learn from it, but avoid turning every experiment into an approval queue. Provide dashboards, budget notifications, example traces, and safe defaults. When a team exceeds a target, ask which outcome improved and whether the extra spend was intentional.

Review price and behavior changes. Provider pricing, model defaults, context limits, and caching rules can change. Version the effective price used in reports and annotate model or routing changes. Recalculate historical comparisons carefully so a price change is not mistaken for a sudden engineering regression.

Control sensitive cost data. Usage records may reveal customer activity, prompt sizes, feature adoption, or internal experiments. Restrict access, aggregate where possible, and avoid placing private prompts in finance dashboards. Cost visibility should respect the same tenant and retention rules as operational telemetry.

Establish a regular rhythm. Review daily anomalies, weekly feature and route trends, and monthly forecasts against actuals. Give owners one or two concrete actions rather than a wall of charts. The goal is not to make every request minimal; it is to make every meaningful unit of spend explainable.

The practical lesson is simple: AI FinOps connects money to product outcomes. Attribute usage, budget the right scopes, measure accepted results, find waste, route by need, and review changes continuously. With that discipline, teams can scale AI adoption while keeping cost predictable and decisions grounded.

That is it for today. Make every important token accountable to an outcome. Visit crazyrouter.com, and see you in the next episode.'''

(root / 'episodes').mkdir(exist_ok=True)
(root / 'audio').mkdir(exist_ok=True)
(root / f'episodes/ep{ep:03d}_script.txt').write_text(script)
parts = script.split('\n\n')
for i, part in enumerate(parts, 1):
    out = root / f'episodes/ep{ep:03d}_chunk{i}.mp3'
    subprocess.run(['edge-tts', '--voice', 'en-US-GuyNeural', '--text', part, '--write-media', str(out)], check=True)
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
    ET.SubElement(item, 'link').text = 'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep146'
    channel.insert(0, item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
print(f'DONE {audio} {size} bytes {duration}')
