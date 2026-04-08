# EP019: Function Calling Across Different AI Models

**Format:** Solo host monologue with practical comparison
**Duration target:** 4-5 minutes (~1000 words)
**pubDate:** Wed, 08 Apr 2026 08:00:00 +0000

---

## Script

Welcome back to AI Dev Tools — the Crazyrouter Podcast. I'm your host, and today we're diving into one of the most important capabilities in the AI API world: function calling.

If you're building anything beyond basic chat — agents, workflows, tool-augmented systems — function calling is how your model reaches out and *does* things. It decides when to call a function, formats the arguments as JSON, and lets your code execute the actual operation. Then you feed the result back, and the model continues reasoning.

Simple concept. But here's the problem: every major model implements function calling slightly differently. And those differences matter a lot when you're shipping production code.

---

**Let's break down the big four.**

**OpenAI — GPT-4o and GPT-4.1.**

OpenAI basically invented the modern function calling API. They call it "tools" now — you send an array of tool definitions with JSON Schema descriptions, and the model returns a `tool_calls` array in the response. It supports parallel function calling, meaning the model can request multiple tool calls in a single response. GPT-4o is extremely reliable at producing valid JSON and following schema constraints. GPT-4.1 takes it further with even better instruction adherence for tool selection. If you've built against OpenAI's format, congratulations — it's become the de facto standard.

**Anthropic — Claude Opus 4 and Claude Sonnet.**

Claude uses the same conceptual approach but with some key differences. Tool definitions go in a `tools` array, but the response format is different — Claude returns `tool_use` content blocks rather than a separate `tool_calls` field. Claude is excellent at deciding *when* to use tools, arguably more thoughtful than GPT-4o about whether a tool call is actually necessary. Claude Opus 4 also handles complex nested JSON schemas exceptionally well. One gotcha: Claude's tool call IDs have a different format than OpenAI's, which matters if you're parsing responses manually.

**Google — Gemini 2.5 Pro and Flash.**

Gemini supports function calling through its own API format, with function declarations in the request. The response comes back with function call parts. Gemini 2.5 Pro is competitive on accuracy but has quirks — it sometimes includes extra explanation alongside tool calls instead of making clean, standalone calls. Gemini Flash 2.0 is blazing fast for simple function calls, making it great for high-volume, straightforward tool-use tasks. Google is also pushing "automatic function calling" in their SDK where the SDK executes functions for you — convenient for prototyping, but you lose control in production.

**DeepSeek — DeepSeek V3 and DeepSeek R1.**

DeepSeek V3 supports OpenAI-compatible function calling, which is a huge advantage — same format, same JSON schema definitions, same response structure. In practice, V3 handles simple and moderate tool schemas well, though it can struggle with deeply nested or very complex schemas compared to GPT-4o or Claude. The real value is the price point: you get solid function calling at a fraction of the cost of frontier models. DeepSeek R1, the reasoning model, has more limited tool support since it's optimized for chain-of-thought rather than structured output.

---

**The compatibility problem.**

Here's what makes this messy. If you're building directly against each provider's API, you're writing four different integration layers. OpenAI's `tool_calls` response format. Claude's `tool_use` content blocks. Gemini's function call parts. And then DeepSeek's OpenAI-compatible but not always identical behavior.

That's a lot of glue code. A lot of edge cases. A lot of "it works with GPT-4o but breaks with Claude."

---

**This is exactly what an API gateway solves.**

With Crazyrouter, you send function calls in the OpenAI format — because that's become the standard — and the gateway handles the translation. You define your tools once using OpenAI's JSON Schema format. You send the request with any model name. Crazyrouter translates the tool definitions to Claude's format, Gemini's format, or passes them directly to OpenAI-compatible models.

The response comes back normalized. Same structure regardless of which model processed it. Your code doesn't need to know whether Claude used `tool_use` blocks or GPT-4o used `tool_calls`. It's all unified.

---

**Practical recommendations.**

Based on real-world usage patterns, here's my guidance:

For **high-reliability tool calling** where correctness is critical — financial transactions, database mutations, anything you can't easily undo — use GPT-4o or Claude Opus 4. They produce the most consistently valid JSON and make the fewest spurious tool calls.

For **high-volume, simple tools** — fetching data, search queries, basic lookups — Gemini Flash or DeepSeek V3. Fast, cheap, good enough. Save your budget for where it matters.

For **complex agent workflows** with many tools — Claude Opus 4 has an edge. It's better at choosing the *right* tool when you give it ten or twenty options. GPT-4o sometimes defaults to the first plausible tool rather than the best one.

For **parallel tool calling** — when you want the model to make multiple function calls at once — GPT-4o and GPT-4.1 are strongest. Claude supports it but is more conservative, often preferring sequential calls.

---

**Testing your function calls across models.**

Here's a practical tip. Before you commit to a model for tool-calling tasks, test these edge cases:

One: optional parameters. Does the model correctly omit them or fill in defaults?

Two: enum values. Does it stick to the defined options or hallucinate new ones?

Three: nested objects. Can it handle a schema three levels deep?

Four: the "don't call" case. Give it a prompt that doesn't require a tool. Does it correctly respond with text instead of forcing a tool call?

Five: parallel calls. Ask something that requires two tools. Does it call both, or just one?

Run those five tests with each model through Crazyrouter, and you'll have a clear picture of which model fits your use case.

---

**Wrapping up.**

Function calling is the bridge between language models and the real world. Every major model supports it now, but the implementations vary in format, reliability, and edge-case handling.

The smart approach in 2026: don't lock into one model's function calling format. Use a gateway that normalizes the interface. Test multiple models on your specific tool schemas. Route to the right model for the right task.

Crazyrouter handles all of this. One API, one format, every model's function calling capability — normalized and ready to use.

Try it at crazyrouter.com. Links in the show notes. See you in the next episode.
