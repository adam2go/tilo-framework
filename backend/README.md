# Tilo

**Turn any LLM into an interactive UI. One line of Python — no React, no frontend setup.**

```bash
pip install "tilo[openai]"
```

```python
import tilo

spec = tilo.generate(
    "Review this SaaS contract for payment, liability, and IP risks.",
    model="gpt-4o",          # or claude-opus-4-8 — provider auto-detected
)

tilo.view(spec)              # opens in your browser. that's it.
```

The LLM doesn't return a wall of text — it generates a **structured,
interactive surface**: a risk chart, a before/after diff, a checklist, a
human-approval gate, and a memory card, organised into tabs. Rendered with
**zero frontend setup**.

> No API key? Run `tilo demo` to open a sample surface.
> `tilo serve` then open `http://localhost:8000/playground` for a live editor.

## Works with your stack

```python
# OpenAI
from tilo.adapters.openai import generate_aip_spec
spec = generate_aip_spec(OpenAI(), "Analyse Q3 pipeline", skill="sales_dashboard")

# Anthropic
from tilo.adapters.anthropic_sdk import generate_aip_spec
spec = generate_aip_spec(Anthropic(), "Review this PR", skill="code_review")

# LangChain / LangGraph
from tilo.adapters.langchain import generate_aip_spec
spec = generate_aip_spec(ChatOpenAI(model="gpt-4o"), "Plan a trip to Tokyo")

# Bring your own LLM client
from tilo.prompt import AIPPromptBuilder
b = AIPPromptBuilder("Summarise this incident", skill="incident_response")
# b.system_prompt(), b.user_prompt() → your LLM → b.parse(response)
```

## Render anywhere

| | |
|---|---|
| Browser | `tilo.view(spec)` |
| Jupyter / Colab | `tilo.notebook(spec)` |
| Standalone HTML | `tilo.save_html(spec, "out.html")` |
| Production React | `npm install @adam2go/tilo-react` |

## Install options

```bash
pip install "tilo[openai]"      # OpenAI SDK
pip install "tilo[anthropic]"   # Anthropic SDK
pip install "tilo[langchain]"   # LangChain
pip install "tilo[all]"         # everything + Postgres driver
```

## Why Tilo

As LLMs get stronger, a wall of text is still a wall of text. Tilo turns model
output into something a human can **click, edit, approve, and reject** — and
turns those actions into structured signal the model can learn from.

- **Structured UI beats prose** for decisions.
- **Human confirmation is infrastructure** — stronger models need *more* gates, not fewer.
- **Confirmed memory, not auto-memory** — Tilo proposes; the human confirms.

## Links

- **GitHub**: https://github.com/adam2go/tilo-framework
- **Docs**: https://github.com/adam2go/tilo-framework/tree/main/docs
- **5-min quickstart**: https://github.com/adam2go/tilo-framework/blob/main/docs/tutorials/quickstart.md
- **React renderer**: https://www.npmjs.com/package/@adam2go/tilo-react

MIT License
