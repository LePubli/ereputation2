# Claude Instructions

Always optimize token usage.

Rules:
- Be concise.
- Use short answers between tool calls.
- Maximum 25 words between actions.
- Maximum 100 words for final explanations.
- Avoid repeating context.
- Never restate file contents unless necessary.
- Do not explain obvious code.

Before any large modification:
- Run /compact

When exploring code:
- Read only necessary files.
- Never scan entire project unless explicitly requested.

When debugging:
- Prefer targeted reads.
- Avoid verbose logs.

Coding style:
- Minimal comments.
- Production-ready code only.
- No placeholder code.
- No unnecessary abstractions.

Communication style:
- Telegraphed concise technical language.
- Prioritize execution over explanations.
- 
Critical rules:
- Minimize token usage at all times.
- Prefer action over explanation.
- Never summarize unchanged code.
- Never repeat previous reasoning.
- Keep responses dense and technical.
- Use shortest correct answer possible.
- Read minimal files required.
- Avoid full-project analysis unless mandatory.

- Use compressed technical language internally.

Example:
"Need optimize API latency. Check DB indexes. Avoid full scans. Cache expensive queries."

Avoid:
Long prose.
Polite filler.
Repeated explanations.
