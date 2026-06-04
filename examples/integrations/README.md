# Integration Examples

Complete, copy-paste ready examples for adding Tilo to your existing LLM stack.

## Quick pick

| You use | Example file | Install |
|---|---|---|
| OpenAI SDK | [`openai_example.py`](./openai_example.py) | `pip install tilo openai` |
| Anthropic SDK | [`anthropic_example.py`](./anthropic_example.py) | `pip install tilo anthropic` |
| LangChain | [`langchain_example.py`](./langchain_example.py) | `pip install tilo langchain-openai langchain-core` |

## The one-liner pattern

Every adapter follows the same pattern: **LLM response → Tilo AIP spec → render with `@adam2go/tilo-react`**.

### OpenAI

```python
from tilo.adapters.openai import tilo_spec_from_completion

spec = tilo_spec_from_completion(openai_response, title="My Surface")
```

### Anthropic

```python
from tilo.adapters.anthropic_sdk import tilo_spec_from_message

spec = tilo_spec_from_message(anthropic_response, title="My Surface")
```

### LangChain (any chain or agent)

```python
from tilo.adapters.langchain import TiloCallbackHandler

handler = TiloCallbackHandler(title="My Chain")
chain.invoke(input, config={"callbacks": [handler]})
spec = handler.to_spec()
```

## What the spec gives you

```python
from tilo.schemas.artifact import ArtifactSpecV1

validated = ArtifactSpecV1.model_validate(spec)
print(validated.title)                    # e.g. "Q3 Revenue"
print([b.type for b in validated.blocks]) # e.g. ["heading", "metric", "metric"]
```

## Render in React

```tsx
import { renderArtifactBlock } from "@adam2go/tilo-react";

// Render any block from the spec
{spec.blocks.map(block => (
  <div key={block.id}>{renderArtifactBlock(block)}</div>
))}
```

## Automatic block type mapping

| LLM output | Tilo block type |
|---|---|
| Plain text | `markdown` |
| JSON object with ≤8 short values | `metric` (one per key) |
| JSON array of objects | `table` |
| OpenAI tool call | `tool_preview` |
| Anthropic `tool_use` block | `tool_preview` |
| LangChain tool result | `tool_preview` |
| Invalid / complex JSON | `markdown` (code block) |

## Running the examples

```bash
# OpenAI
export OPENAI_API_KEY=sk-...
python examples/integrations/openai_example.py

# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python examples/integrations/anthropic_example.py

# LangChain
export OPENAI_API_KEY=sk-...
python examples/integrations/langchain_example.py
```

All examples also run without an API key and print a deterministic demo output.
