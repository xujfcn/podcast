from pathlib import Path
import re, requests, subprocess, json, xml.etree.ElementTree as ET

root = Path('/root/.openclaw/workspace/podcast')
(root/'episodes').mkdir(exist_ok=True)
(root/'audio').mkdir(exist_ok=True)

ep = 89
title = 'EP089: GLM-5.2 and the New Shape of Long-Horizon AI APIs'
short_title = 'GLM-5.2 and the New Shape of Long-Horizon AI APIs'
description = 'A practical episode about GLM-5.2, long-horizon coding models, 1M-token context, reasoning-token budgets, unlimited RPM promises, and what engineering teams should measure before moving agent workflows into production.'
pub_date = 'Wed, 24 Jun 2026 10:25:00 +0000'

script = """EP089: GLM-5.2 and the New Shape of Long-Horizon AI APIs

Welcome back to AI Dev Tools — The Crazyrouter Podcast. Today we are talking about GLM-5.2, and more broadly, what long-horizon coding models mean when they become ordinary API infrastructure.

The headline around GLM-5.2 is easy to understand: strong coding ability, long context, open weights, and a serious push toward agentic engineering. But for developers, the more interesting question is not simply whether GLM-5.2 is impressive. The question is: what changes when this kind of model is available through an API endpoint that teams can put into real workflows?

The first change is context strategy. A 1M-token context window is not just a bigger prompt box. It changes what a team can reasonably send to a model. Instead of pasting one file, you can include architecture notes, API contracts, migration plans, logs, test output, and repository conventions. For coding agents, that matters because many failures are not caused by weak syntax generation. They are caused by context fragmentation. The model forgets why a constraint exists, misses an earlier decision, or rewrites a boundary it should have preserved.

Long context helps, but it does not remove the need for discipline. If you put a million tokens of messy information into a model, you can still get messy results. The better pattern is structured context: project overview, constraints, allowed commands, verification steps, risk boundaries, and the specific task. Long context is most valuable when it lets the model carry engineering judgment forward, not when it becomes a junk drawer.

The second change is that reasoning-token budgets become a real operational parameter. With models like GLM-5.2, you may see a call succeed while visible output is short or even empty if the output budget is too small relative to internal reasoning. That is not just a model curiosity; it is a product integration issue. If your application sets max tokens too aggressively, you can create false failures. The request worked, the model reasoned, but the user did not receive enough final answer.

So production teams should test token settings the way they test timeout settings. For short extraction tasks, a compact budget may be fine. For coding plans, refactors, or long debugging sessions, leave enough room for the final answer. Log prompt tokens, completion tokens, reasoning tokens if available, latency, and empty-output cases separately. If you do not measure them separately, you will misdiagnose the route.

The third change is RPM. Unlimited RPM sounds simple, but in production it should still be interpreted carefully. High request capacity is useful for batch testing, agent fleets, background jobs, and multi-user products. But unlimited RPM does not mean unlimited good outcomes. You still need concurrency control, retries, backoff, queue visibility, cost limits, and failure classification.

This is especially true for agent workflows. One user instruction can become dozens of model calls, tool calls, tests, retries, and summaries. If the model is cheap enough and the route is available enough, developers are tempted to let agents run freely. That is dangerous unless the workflow has a clear goal, a budget, a stop condition, and verification gates.

The fourth change is model selection. GLM-5.2 is especially interesting for coding, backend refactoring, structured plans, and long-document engineering tasks. It may not be the right default for every use case. If you need low-latency classification, a smaller model may be better. If you need image understanding, you need a vision model. If you need high-polish design output, you may still want a frontier multimodal model or a dedicated creative workflow.

That is why gateway routing matters. The best API layer is not just a catalog of model names. It should help teams route by task type: lightweight automation, long-horizon coding, visual reasoning, speech, image generation, video generation, and fallback. GLM-5.2 belongs in the long-horizon engineering bucket, where context, reasoning, and stability are more important than raw speed.

The fifth change is benchmark design. Public benchmark numbers are useful, especially coding and terminal-task benchmarks. But an engineering team should run its own tests before switching production workflows. A practical GLM-5.2 evaluation might include five tasks: an algorithm function with tests, a backend migration plan, a structured JSON extraction, a long-context retrieval task, and a small frontend generation task.

Then score the result across dimensions that matter: did the code run, did the plan identify real risks, was the JSON valid, did the model retrieve hidden constraints, did the frontend actually produce usable HTML, how long did each request take, and did token settings produce complete visible output?

This kind of evaluation is less glamorous than a leaderboard, but far more useful. It tells you whether the model fits your workflow, not just whether it looks strong on a chart.

There is also a strategic point here. Models like GLM-5.2 make open or widely accessible intelligence feel less theoretical. If a long-horizon coding model can be called through a standard OpenAI-compatible client, then teams can test it without rebuilding their stack. They can swap the model name, keep the same SDK, and compare results against their existing routes.

That lowers the cost of experimentation. And in AI infrastructure, lowering the cost of experimentation is a big deal. The teams that win are not the teams that memorize model rankings. They are the teams that can test new routes quickly, measure outcomes, and update routing policy without rewriting the application.

So the takeaway is this: GLM-5.2 is not only a model launch. It is a reminder that long-horizon AI is becoming an API product category. The important integration questions are now context structure, reasoning budgets, latency, RPM, task routing, verification, and cost per successful engineering task.

If you are testing it this week, do not only ask whether it is smart. Ask whether it can hold your project constraints, return complete answers with your token settings, survive your concurrency pattern, and produce outputs your CI or validation layer can verify.

That is how model excitement turns into production infrastructure.

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
