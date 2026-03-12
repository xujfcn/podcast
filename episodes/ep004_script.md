# EP004: AI Agent Skills — Build Smarter Agents with One Command

**Date:** March 14, 2026
**Duration:** ~4 min
**Host:** AI Dev Tools Podcast by Crazyrouter

---

## INTRO (15s)

Welcome back to AI Dev Tools — the Crazyrouter Podcast. I'm your host, and today we're talking about something that's changing how developers build AI agents: pre-built skills you can install with a single command.

## SEGMENT 1: The Agent Skills Problem (45s)

So here's the thing. Everyone's building AI agents right now. Chatbots, coding assistants, content generators, customer support bots. But every time you start a new agent project, you're writing the same boilerplate. Chat completion calls. Image generation wrappers. Text-to-speech pipelines. Speech-to-text handlers.

It's like web development before npm. Everyone reinventing the wheel. Copy-pasting from Stack Overflow. Debugging the same integration issues over and over.

What if you could just... install a skill? Like a plugin for your agent?

## SEGMENT 2: Enter npx crazyrouter-skills (60s)

That's exactly what Crazyrouter Skills does. Open your terminal and run:

npx crazyrouter-skills list

You'll see eight ready-to-use skills. Chat with 627 plus AI models. Image generation with DALL-E 3, GPT Image, and Gemini. Text-to-speech. Speech-to-text. OCR. Translation. Music generation with Suno. Video generation with Sora, Kling, and Veo.

Pick one. Say you want chat:

npx crazyrouter-skills install crazyrouter-chat

Done. You get a working script, documentation, and it's already wired to use Crazyrouter's unified API. One API key, all models, cheaper pricing.

The beauty is composability. Install chat plus image-gen plus TTS, and you've got an agent that can talk, see, and create — in about 30 seconds of setup.

## SEGMENT 3: Why This Matters for MCP (45s)

Now, if you're following the Model Context Protocol — MCP — this fits right in. MCP is all about giving AI models access to tools and context. Skills are essentially pre-packaged tools.

Instead of writing custom MCP tool handlers from scratch, you install a skill, point your MCP server at it, and your agent gains a new capability. Want your Claude or GPT agent to generate images? Install the image-gen skill. Need real-time translation? There's a skill for that.

The shift is from "build everything" to "compose what you need." And that's how the best developer ecosystems work. Think npm packages, VS Code extensions, Docker containers. Small, focused, composable units.

## SEGMENT 4: The Cost Angle (30s)

And here's the kicker — because all skills route through Crazyrouter, you get the same cost savings we talked about in Episode 3. Up to 60 percent off on major models. One bill. One API key. No juggling five different provider accounts.

You're not just saving development time with pre-built skills. You're saving money on every API call those skills make.

## OUTRO (15s)

That's it for today. Try it yourself — npx crazyrouter-skills list — and see what you can build. Links in the show notes. If this was useful, follow us on Spotify. See you tomorrow.

---

**Show Notes:**
- Install: `npx crazyrouter-skills list`
- npm: https://www.npmjs.com/package/crazyrouter-skills
- GitHub: https://github.com/xujfcn/crazyrouter-skills
- Crazyrouter: https://crazyrouter.com
- Docs: https://docs.crazyrouter.com/introduction
