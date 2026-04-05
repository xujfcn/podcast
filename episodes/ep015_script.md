# EP015: AI API Security Best Practices for Production Apps

## Script (~4 min, ~1000 words)

**[INTRO]**

Hey, welcome back to AI Dev Tools — the Crazyrouter Podcast. I'm your host, and today we're talking about something that doesn't get nearly enough attention in the AI developer community: security. Specifically, how to secure your AI API integrations when you're building for production. Because shipping a cool demo is one thing — keeping your users' data safe and your API bills under control is another.

Let's get into it.

**[THE STAKES]**

First, why does this matter so much right now? AI APIs are different from traditional APIs in a few important ways. The requests and responses often contain sensitive user data — personal details, private conversations, business logic. The costs can spike suddenly if something goes wrong — a prompt injection attack or a runaway loop can burn through hundreds of dollars in minutes. And the attack surface is novel. Prompt injection, jailbreaking, data exfiltration through model outputs — these are attack vectors that most security teams haven't fully mapped yet.

So let's talk about the five things you need to get right.

**[NUMBER ONE: NEVER EXPOSE API KEYS CLIENT-SIDE]**

This sounds obvious, but it's the number one mistake developers make. Your AI API keys should never appear in frontend JavaScript, mobile app binaries, or public repositories. Ever.

All AI API calls should go through your backend. Your server holds the key, makes the request, and returns only what the user needs to see. If you're building a mobile app, use a backend-for-frontend pattern. If you're using a gateway like Crazyrouter, you can generate user-scoped tokens with spending limits and model restrictions — so even if a token leaks, the blast radius is contained.

Speaking of which — rotate your keys regularly. Monthly at minimum. Most API providers make this painless.

**[NUMBER TWO: IMPLEMENT RATE LIMITING AND SPENDING CAPS]**

Your AI integration needs rate limits at multiple levels. Per-user limits prevent one bad actor from hammering your system. Global spending caps prevent a bug or attack from running up a massive bill overnight.

Set hard limits, not just alerts. An alert that fires at 3 AM after you've already spent five hundred dollars is not a security control — it's a post-mortem tool. Hard caps that kill the tap automatically are what you need.

Crazyrouter lets you set per-key spending limits and model allowlists, so you can restrict a particular integration to only the models it actually needs, at a budget it can't exceed. That's defense in depth.

**[NUMBER THREE: VALIDATE AND SANITIZE ALL INPUTS]**

Prompt injection is the SQL injection of the AI era. If your application takes user input and concatenates it directly into a system prompt, you're vulnerable. A malicious user can override your instructions, extract your system prompt, or manipulate the model into producing harmful outputs.

The mitigations: use structured input formats where possible — JSON fields instead of freeform text. Add a layer of input validation before the prompt is constructed. Use separate system and user message roles correctly — don't mix them. And test your prompts against adversarial inputs before shipping.

Also: treat model outputs as untrusted. If your app renders AI-generated content as HTML, you need to sanitize it like you would any user-generated content. XSS through model outputs is a real attack vector.

**[NUMBER FOUR: HANDLE DATA PRIVACY CORRECTLY]**

When user data goes into an AI prompt, you're sending it to a third-party API. Make sure your privacy policy reflects this. Check whether your AI provider uses inputs for model training — many enterprise tiers opt out by default, but consumer tiers often don't.

For sensitive data — healthcare, financial, legal — consider whether you should be using a cloud AI API at all, or whether a self-hosted model is more appropriate. If you're using an API gateway, look for one that doesn't log request contents, or that gives you control over logging granularity.

Also, implement data minimization. Don't send the entire user profile into every prompt. Send only what the model needs to answer the question.

**[NUMBER FIVE: LOG, MONITOR, AND AUDIT]**

You can't secure what you can't see. Log every AI API request — at minimum: the timestamp, the model used, the token counts, the user ID, and the cost. Store these logs somewhere you can query them.

Set up anomaly detection. If a user who normally makes ten requests a day suddenly makes a thousand, that's worth investigating. If your costs jump fifty percent overnight with no corresponding increase in traffic, something is wrong.

And do regular audits of your system prompts. Prompts drift. Engineers add exceptions, edge cases pile up, and what started as a clean, secure instruction set becomes a mess of contradictions that's easy to manipulate.

**[WRAPPING UP]**

So to summarize: keep your API keys server-side, enforce hard spending caps, validate all inputs against prompt injection, handle user data with privacy-first thinking, and build robust logging from day one.

AI security isn't fundamentally different from regular application security — it just has some new attack vectors layered on top. The fundamentals of least privilege, defense in depth, and monitoring apply just as much here.

If you want to start applying some of these practices today, Crazyrouter makes it easy to set per-key limits, model allowlists, and spending caps through a single dashboard. Check it out at crazyrouter.com.

Thanks for listening to AI Dev Tools — the Crazyrouter Podcast. I'll be back tomorrow with another episode. See you then.
