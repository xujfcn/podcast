from pathlib import Path
import re, requests, subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

ep = 90
title = 'EP090: Video APIs Need Real Task Evidence, Not Just Model Lists'
short_title = 'Video APIs Need Real Task Evidence, Not Just Model Lists'
description = 'A practical episode about production video generation APIs: async task submission, polling, model availability, endpoint drift, archived video URLs, and why teams should test Wan, Veo, Seedance, and Kling with real calls before writing integration docs or choosing a provider.'
pub_date = 'Tue, 30 Jun 2026 09:25:00 +0000'

script = """EP090: Video APIs Need Real Task Evidence, Not Just Model Lists

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about video generation APIs, and why model lists are not enough evidence for production integration.

In text generation, a quick API test is usually simple. You send a prompt, you get a response, and you can immediately inspect whether the route works. Video generation is different. Most serious video models are asynchronous. You submit a task, receive an id, poll a query endpoint, wait for the upstream provider, and eventually get a generated media URL. That means a successful submit response is only the first half of the story.

This matters because video API documentation can look complete while the actual production path still has hidden details. A model may appear in a model list, but a channel can be temporarily unavailable. A sample model name may be outdated. A query endpoint may return fields that differ from the example. A task may say queued, processing, in progress, success, succeeded, completed, or failed depending on the route family. If your integration treats all of those as one shape, it will break.

So the first rule for video API work is: test the full lifecycle. Do not only test submit. Test submit, task id extraction, polling, terminal status detection, final media URL extraction, and HTTP access to the generated file.

For a gateway that supports multiple video families, the route surface is especially important. Wan text-to-video can use a `/v1/video/generations` style route. Veo can use a unified video creation route. Seedance may use a native Volc-style task endpoint. Kling uses its own text-to-video and query paths. These are all video generation APIs, but they are not the same protocol.

That is not necessarily a problem. A gateway can expose different provider-native contracts when that is the most accurate way to preserve model capability. But it does mean developers need to know which models belong to which endpoint family. If you send a Wan model to the wrong unified route, or a Seedance model to an outdated alias, you can get a model-not-found error even though the product does support video generation.

The second rule is: use the runtime model list as evidence, not just a static page. Documentation is useful for request shapes and recommended paths, but active model availability can change by region, channel, account, and provider status. A good integration workflow should call `/v1/models`, filter for video endpoint types, and then match those model names to the right docs page.

The third rule is: normalize task states carefully. In one provider family, success may be called `SUCCESS`. In another, it may be `succeeded`. In another, it may be `completed`. Some responses put the status at the top level. Others put it under `data.status`, `output.task_status`, or a provider-specific envelope. A production client should avoid assuming one universal response shape unless the API explicitly guarantees it.

The fourth rule is: prefer archived media URLs when the gateway provides them. Upstream result URLs may be temporary, signed, region-specific, or short-lived. A gateway archived URL is easier for applications, logs, demos, QA, and support teams. When testing video generation, always verify that the final URL is reachable, returns a video MIME type, and has a plausible file size.

This is also where pricing comparisons get more honest. It is easy to say one video model is cheaper than another. But for real applications, the metric is not only price per second or price per request. The practical metric is cost per usable generated video. That includes failed tasks, retries, moderation failures, model unavailability, queue time, resolution, duration, and whether the output is good enough to accept.

For example, a high-volume SaaS product generating short marketing clips may care about 480p or 720p throughput, predictable task completion, and low retry rates. A creative studio may care more about quality and control. An AI automation workflow may care about API reliability, polling semantics, and whether the result URL can be consumed by the next tool automatically.

That is why video API evaluation should be written as a test matrix, not a marketing list. A useful matrix includes: model name, endpoint, request payload, submit HTTP status, task id field, query endpoint, terminal status, final media URL field, generation time, output size, and notes about failure modes.

Models like Wan, Veo, Seedance, and Kling are all important for different reasons. Wan is useful for practical text-to-video and image-to-video workflows. Veo is important because Google’s video models are becoming a reference point for high-quality generation. Seedance is important because ByteDance and Doubao video models are moving fast in multimodal generation. Kling is important because it has a rich public video capability surface, including text-to-video, image-to-video, and newer reference workflows.

But the developer question is not just, “Does the platform list these models?” The better question is, “Can I submit a real task today, poll it to completion, retrieve the MP4, and build a stable application around the response?”

For documentation teams, this changes how docs should be maintained. Every video API doc should be backed by a recent live task, or at least clearly marked as beta, hidden, deprecated, or temporarily unavailable. If a public example uses a model name that no longer appears in `/v1/models`, the example should be updated. If a query response returns `data.artifact_url` instead of `output.video_url`, the docs should show that reality.

For engineering teams, the recommendation is simple. Before choosing a video API provider, run five small tests: one Wan text-to-video task, one Veo task, one Seedance task, one Kling task, and one failure-path test using an unavailable or invalid model name. Save every response. Then build your integration around the observed lifecycle, not around a perfect imaginary API.

This is what turns video API selection from guesswork into infrastructure work. Real task evidence beats model lists. Polling behavior matters. Archived URLs matter. Error shapes matter. And for high-volume generation, the most important number is cost per usable completed video.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. See you in the next episode."""

script_path = root/f'episodes/ep{ep:03d}_script.txt'
script_path.write_text(script, encoding='utf-8')

tools = Path('/root/.openclaw/workspace/TOOLS.md').read_text(encoding='utf-8', errors='ignore')
m = re.search(r'Bearer\s+(sk-[A-Za-z0-9_\-]+)', tools)
if not m:
    raise SystemExit('Crazyrouter API key not found')
key = m.group(1)

paras = script.split('\n\n')
n = len(paras)
parts = ['\n\n'.join(paras[:n//3]), '\n\n'.join(paras[n//3:2*n//3]), '\n\n'.join(paras[2*n//3:])]
for i, part in enumerate(parts, 1):
    out = root/f'episodes/ep{ep:03d}_part{i}.mp3'
    if not out.exists() or out.stat().st_size < 1000:
        r = requests.post(
            'https://crazyrouter.com/v1/audio/speech',
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            json={'model': 'tts-1', 'voice': 'alloy', 'input': part},
            timeout=300,
        )
        print('part', i, 'status', r.status_code, r.headers.get('content-type'), flush=True)
        if not r.ok:
            print(r.text[:500])
            r.raise_for_status()
        out.write_bytes(r.content)
    print('saved', out.name, out.stat().st_size, flush=True)

concat = root/f'episodes/ep{ep:03d}_concat.txt'
concat.write_text(''.join([f"file 'ep{ep:03d}_part{i}.mp3'\n" for i in range(1,4)]), encoding='utf-8')
subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(root/f'audio/ep{ep:03d}.mp3')], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
audio = root/f'audio/ep{ep:03d}.mp3'
size = audio.stat().st_size

try:
    r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(audio)], capture_output=True, text=True, check=True)
    sec = float(json.loads(r.stdout)['format']['duration'])
    dur = f"{int(sec//60)}:{int(sec%60):02d}"
except Exception:
    dur = '6:00'

feed = root/'feed.xml'
ET.register_namespace('atom','http://www.w3.org/2005/Atom')
ET.register_namespace('itunes','http://www.itunes.com/dtds/podcast-1.0.dtd')
tree = ET.parse(feed)
channel = tree.getroot().find('channel')
for existing in channel.findall('item'):
    if (existing.findtext('title') or '').startswith(f'EP{ep:03d}:'):
        print(f'EP{ep:03d} already in feed')
        break
else:
    item = ET.Element('item')
    ET.SubElement(item,'title').text = title
    ET.SubElement(item,'description').text = description
    ET.SubElement(item,'pubDate').text = pub_date
    enc = ET.SubElement(item,'enclosure')
    enc.set('url',f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3')
    enc.set('length',str(size))
    enc.set('type','audio/mpeg')
    ET.SubElement(item,'guid').text = f'https://xujfcn.github.io/podcast/audio/ep{ep:03d}.mp3'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = dur
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episode').text = str(ep)
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType').text = 'full'
    ET.SubElement(item,'{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit').text = 'false'
    ET.SubElement(item,'link').text = f'https://crazyrouter.com?utm_source=rss&utm_medium=podcast&utm_campaign=ep{ep:03d}'
    items = list(channel.findall('item'))
    if items:
        channel.insert(list(channel).index(items[0]), item)
    else:
        channel.append(item)
    tree.write(feed, encoding='utf-8', xml_declaration=True)
    print('inserted', f'EP{ep:03d}', size, dur)

ET.parse(feed)
print('done', audio, size, dur)
