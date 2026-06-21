from pathlib import Path
import re, requests, subprocess, json, xml.etree.ElementTree as ET
from datetime import datetime, timezone

root = Path('/root/.openclaw/workspace/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

ep = 87
title = 'EP087: Vision Model Routing Is Really Media Routing'
short_title = 'Vision Model Routing Is Really Media Routing'
description = 'A practical episode about image understanding APIs, URL image inputs, Gemini and Claude inline media conversion, Qwen and OpenAI-style URL passthrough, and why production AI gateways need media-aware routing instead of just model-aware routing.'
pub_date = 'Sun, 21 Jun 2026 11:55:00 +0000'

script = """EP087: Vision Model Routing Is Really Media Routing

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about image understanding models, but from an infrastructure angle that most benchmark posts skip: where does the image actually travel?

When developers compare vision models, they usually ask three questions. Can it understand the image? How much does it cost? How fast is it? Those are good questions, but in production there is a fourth one: when the user sends an image URL, does your gateway download that image, or does the upstream model provider fetch it directly?

That sounds like an implementation detail. It is not. It affects bandwidth, latency, privacy boundaries, SSRF protection, error messages, token estimation, and operating cost.

In OpenAI-compatible chat requests, the common pattern is a message with text plus an image_url object. It looks clean. The client sends a URL, and the model answers. But behind the scenes, every provider handles that URL differently.

Some OpenAI-style routes can preserve the image URL in the upstream request. In those cases, the gateway may not need to fetch the full image before forwarding the request, although token estimation or validation might still inspect the URL. This is the path developers usually imagine when they say, let the provider fetch the image.

Qwen vision routes can also be attractive for this pattern. In practical testing, Qwen3 VL Flash is especially interesting because it combines low input price, successful image recognition, and a code path that is closer to URL passthrough than forced base64 conversion. For a gateway trying to reduce its own outbound media traffic, that matters.

But Gemini-style routing is different in many gateway implementations. If the upstream Gemini protocol path expects inline data, the gateway may download the image URL, convert it to base64 or inline media, and then send that payload to Gemini. The user still sent a URL, but the gateway did the media fetch. That means URL support at the API surface does not automatically mean upstream-native URL fetching.

Claude has a similar nuance. Claude's native API supports URL sources in some contexts, but if a gateway receives an OpenAI-compatible image_url request and converts it into Claude format by downloading the image and sending base64, then the operational behavior is still gateway-side media fetching. The model may understand the image perfectly, but it does not solve the gateway bandwidth problem.

This is why the phrase supports image_url is too vague for production docs. There are at least three different meanings.

First, the API accepts an image_url field from the client. Second, the gateway can transform that field into a format the upstream model accepts. Third, the upstream provider receives the original URL and fetches the media itself. Those are not the same capability.

A good vision model benchmark should separate them.

In a recent practical comparison, the most useful production ranking was not simply best vision model. It was more like this. Qwen3 VL Flash is a strong default when you want low cost and less gateway-side media handling. GPT-4.1 Mini is fast and stable, but costs more. GPT-4.1 Nano is cheaper and can work for simple visual recognition, but you should not expect the same reasoning depth. Qwen3 VL Plus is a quality-first option when the flash tier is not enough.

Gemini 2.5 Flash Lite is more complicated. It can be cheap, and it can be useful, but if your goal is specifically to reduce gateway outbound traffic, it may not be the best first choice when the adapter downloads URLs and sends inline data upstream.

There is also a second reliability lesson. A text-only health check is not enough for a vision route. A channel can return HTTP 200 for text prompts and still mishandle inline image parts. In one failure pattern, the response looked successful, but the prompt token usage showed that only the text arrived. The model did not fail at understanding the image. The image part was effectively dropped before the model used it.

That means vision routes need vision smoke tests. Send a tiny public image, ask a deterministic question, check that the answer is correct, and check that usage looks like image tokens were included. If the prompt token count is basically just the text prompt, your vision path is not healthy even if the HTTP status is 200.

For gateways, the design recommendation is simple: make media handling explicit.

Your model registry should track whether each route supports client URL input, whether the adapter fetches media, whether upstream URL passthrough is preserved, whether base64 input is accepted, maximum file size, allowed MIME types, and whether token estimation prefetches the image.

Your router should not only route by model name. It should route by media behavior. If a customer wants minimum gateway bandwidth, prefer routes with upstream URL fetching. If a customer wants maximum compatibility with private or short-lived URLs, gateway-side fetch and inline conversion may actually be safer, because the gateway can authenticate or rehost the media before sending it to the model. Different product goals need different media paths.

Your error messages should also tell the truth. If the gateway blocked a URL because of SSRF protection or disallowed ports, say that the gateway attempted to fetch the image and the URL was rejected by media safety policy. Do not make the user think the vision model itself failed.

Finally, token estimation needs a policy. If you always download the URL just to estimate image size or MIME type, then even a URL-passthrough route still creates gateway outbound traffic. For routes that truly support upstream URL fetching, you may want a no-prefetch mode with conservative token estimates, usage reconciliation after the upstream response, or route-specific accounting rules.

The big takeaway is this: vision model routing is really media routing. The model name is only one part of the decision. The image transport path can determine cost, reliability, security, and customer experience.

So the next time someone asks which image understanding model is best, ask a sharper question: best for what media path? If the answer is low-cost URL image recognition with less gateway-side fetching, Qwen3 VL Flash deserves a serious look. If the answer is fastest stable general-purpose vision, GPT-4.1 Mini may be the safer route. If the answer is maximum compatibility across weird image sources, inline conversion can still be useful, but you should price and monitor it honestly.

That is it for today. Thanks for listening to AI Dev Tools — The Crazyrouter Podcast. See you in the next episode."""

script_path = root/f'episodes/ep{ep:03d}_script.txt'
script_path.write_text(script, encoding='utf-8')

# Reuse existing local Crazyrouter key discovery pattern without printing secrets.
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
