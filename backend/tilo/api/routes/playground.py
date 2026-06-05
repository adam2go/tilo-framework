"""Playground & welcome routes.

Serves a zero-setup welcome page at `/` and an interactive AIP playground
at `/playground` where developers can paste a spec (or generate one) and
see it render instantly — no React, no build step.
"""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from tilo.prompt import BUILTIN_SKILLS
from tilo.viewer import _CHART_JS, _CSS, _RENDER_JS

router = APIRouter(tags=["playground"])


# A built-in sample spec showcasing many block types.
_SAMPLE_SPEC = {
    "version": "tilo/aip/v1",
    "title": "Contract Risk Review",
    "status": "ready",
    "blocks": [
        {"id": "h", "type": "heading", "props": {"text": "High-Risk Clauses Found", "severity": "high"}},
        {"id": "m1", "type": "metric", "props": {"label": "Risk Score", "value": "7.2", "delta": "+1.1"}},
        {"id": "m2", "type": "metric", "props": {"label": "Clauses", "value": "24"}},
        {"id": "chart", "type": "chart", "title": "Risk by Category",
         "props": {"chart_type": "radar", "axes": [
             {"label": "Liability", "score": 8}, {"label": "Payment", "score": 5},
             {"label": "IP", "score": 9}, {"label": "Termination", "score": 4}]}},
        {"id": "cl", "type": "checklist", "props": {"items": [
            {"text": "Review liability cap", "checked": True},
            {"text": "Confirm payment terms"},
            {"text": "Verify IP ownership clause"}]}},
        {"id": "d", "type": "diff", "props": {
            "before": "Company shall have unlimited liability for all damages.",
            "after": "Company liability shall not exceed fees paid in the prior 12 months."}},
        {"id": "conf", "type": "confirmation", "props": {
            "description": "Approve revised contract with capped liability?", "risk_level": "high"}},
        {"id": "mem", "type": "memory_card", "props": {
            "content": "User prefers conservative liability caps tied to 12-month fees", "confidence": 0.85}},
    ],
    "views": [
        {"id": "v1", "label": "Risks", "block_ids": ["h", "m1", "m2", "chart"]},
        {"id": "v2", "label": "Revision", "block_ids": ["cl", "d"]},
        {"id": "v3", "label": "Decision", "block_ids": ["conf", "mem"]},
    ],
    "follow_ups": ["Compare to industry-standard caps", "Draft a counter-proposal",
                   "Explain the IP clause risk", "Save as a review template"],
}


@router.get("/", response_class=HTMLResponse)
def welcome() -> str:
    """Zero-setup welcome page shown at the server root."""
    return _WELCOME_HTML


@router.get("/playground", response_class=HTMLResponse)
def playground() -> str:
    """Interactive playground: paste a spec → see it render instantly."""
    skills_list = "".join(
        f'<option value="{k}">{k} — {v["description"]}</option>'
        for k, v in BUILTIN_SKILLS.items()
    )
    return _PLAYGROUND_HTML.format(
        css=_CSS,
        chart_js=_CHART_JS,
        render_js=_RENDER_JS,
        sample_spec=json.dumps(_SAMPLE_SPEC, indent=2),
        skills_options=skills_list,
    )


# --------------------------------------------------------------------------- #
# Welcome page                                                                 #
# --------------------------------------------------------------------------- #

_WELCOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tilo — AI-native product runtime</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: linear-gradient(180deg, #0f172a 0%, #1e1b4b 100%); color: #e2e8f0;
       min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 24px; }
.card { max-width: 680px; width: 100%; }
.logo { font-size: 2.6rem; font-weight: 800; letter-spacing: -0.03em;
        background: linear-gradient(90deg, #818cf8, #c084fc); -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; margin-bottom: 8px; }
.tag { font-size: 1.05rem; color: #94a3b8; margin-bottom: 28px; line-height: 1.5; }
.status { display: inline-flex; align-items: center; gap: 8px; background: #16a34a22;
          border: 1px solid #16a34a55; color: #4ade80; padding: 6px 14px; border-radius: 20px;
          font-size: 0.85rem; margin-bottom: 28px; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; }
.links { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 24px; }
.link { display: block; background: #1e293b88; border: 1px solid #334155; border-radius: 12px;
        padding: 16px 18px; text-decoration: none; color: #e2e8f0; transition: .15s; }
.link:hover { border-color: #818cf8; background: #1e293bcc; transform: translateY(-1px); }
.link .t { font-weight: 600; font-size: 0.95rem; margin-bottom: 3px; }
.link .d { font-size: 0.82rem; color: #94a3b8; }
.code { background: #0f172a; border: 1px solid #334155; border-radius: 10px; padding: 16px;
        font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #c7d2fe;
        overflow-x: auto; margin-bottom: 8px; }
.code .c { color: #64748b; }
.code .k { color: #f472b6; }
.code .s { color: #86efac; }
.foot { font-size: 0.8rem; color: #64748b; margin-top: 24px; text-align: center; }
.foot a { color: #818cf8; text-decoration: none; }
</style>
</head>
<body>
<div class="card">
  <div class="logo">Tilo</div>
  <div class="tag">The AI-native product runtime. Any LLM generates a structured,
    interactive surface — rendered for both humans and agents.</div>
  <div class="status"><span class="dot"></span> Backend running</div>

  <div class="links">
    <a class="link" href="/playground">
      <div class="t">▶ Playground</div>
      <div class="d">Paste a spec, see it render live</div>
    </a>
    <a class="link" href="/docs">
      <div class="t">⚙ API Docs</div>
      <div class="d">Interactive OpenAPI reference</div>
    </a>
    <a class="link" href="/api/health">
      <div class="t">♥ Health</div>
      <div class="d">Backend status check</div>
    </a>
    <a class="link" href="https://github.com/adam2go/tilo-framework" target="_blank">
      <div class="t">★ GitHub</div>
      <div class="d">Docs, examples, source</div>
    </a>
  </div>

  <div class="code"><span class="c"># One line: any LLM → a full interactive surface</span><br>
<span class="k">import</span> tilo<br>
spec = tilo.<span class="k">generate</span>(<span class="s">"Review this contract"</span>, model=<span class="s">"gpt-4o"</span>)<br>
tilo.<span class="k">view</span>(spec)  <span class="c"># opens in your browser — no React needed</span></div>

  <div class="foot">
    <a href="https://pypi.org/project/tilo/">pip install tilo</a> ·
    <a href="https://www.npmjs.com/package/@adam2go/tilo-react">npm install @adam2go/tilo-react</a>
  </div>
</div>
</body>
</html>"""


# --------------------------------------------------------------------------- #
# Playground page                                                              #
# --------------------------------------------------------------------------- #

_PLAYGROUND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tilo Playground</title>
<style>{css}
.pg-wrap {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; height: 100vh; }}
.pg-editor {{ display: flex; flex-direction: column; border-right: 1px solid #e2e8f0; background: #0f172a; }}
.pg-toolbar {{ display: flex; align-items: center; gap: 10px; padding: 12px 16px;
               background: #1e293b; border-bottom: 1px solid #334155; }}
.pg-toolbar .brand {{ font-weight: 700; color: #c7d2fe; font-size: 0.95rem; }}
.pg-toolbar select {{ background: #0f172a; color: #e2e8f0; border: 1px solid #334155;
                      border-radius: 6px; padding: 5px 8px; font-size: 0.8rem; max-width: 220px; }}
.pg-toolbar button {{ background: #6366f1; color: white; border: none; border-radius: 6px;
                      padding: 6px 14px; font-size: 0.82rem; font-weight: 500; cursor: pointer; }}
.pg-toolbar button:hover {{ background: #4f46e5; }}
.pg-toolbar .spacer {{ flex: 1; }}
#editor {{ flex: 1; background: #0f172a; color: #e2e8f0; border: none; padding: 16px;
           font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; resize: none; outline: none;
           line-height: 1.5; }}
.pg-preview {{ overflow-y: auto; background: #f8fafc; }}
.pg-error {{ background: #fef2f2; color: #991b1b; padding: 10px 16px; font-size: 0.82rem;
             font-family: monospace; border-bottom: 1px solid #fca5a5; }}
@media (max-width: 720px) {{ .pg-wrap {{ grid-template-columns: 1fr; height: auto; }}
  .pg-editor {{ height: 50vh; }} }}
</style>
</head>
<body style="margin:0">
<div class="pg-wrap">
  <div class="pg-editor">
    <div class="pg-toolbar">
      <span class="brand">Tilo Playground</span>
      <select id="sample" onchange="loadSample()">
        <option value="">Load a skill template…</option>
        {skills_options}
      </select>
      <div class="spacer"></div>
      <button onclick="render()">▶ Render</button>
    </div>
    <textarea id="editor" spellcheck="false" oninput="debouncedRender()"></textarea>
  </div>
  <div class="pg-preview">
    <div id="error" class="pg-error" style="display:none"></div>
    <div class="container" id="app"></div>
  </div>
</div>

<script type="application/json" id="__sample__">{sample_spec}</script>
<script>{chart_js}{render_js}</script>
<script>
const SAMPLE = JSON.parse(document.getElementById('__sample__').textContent);
const editor = document.getElementById('editor');
const errorEl = document.getElementById('error');
editor.value = JSON.stringify(SAMPLE, null, 2);

let timer;
function debouncedRender() {{ clearTimeout(timer); timer = setTimeout(render, 400); }}

function render() {{
  errorEl.style.display = 'none';
  let spec;
  try {{ spec = JSON.parse(editor.value); }}
  catch(e) {{ errorEl.textContent = 'JSON error: ' + e.message; errorEl.style.display = 'block'; return; }}
  try {{ renderSpec(spec, document.getElementById('app')); }}
  catch(e) {{ errorEl.textContent = 'Render error: ' + e.message; errorEl.style.display = 'block'; }}
}}

async function loadSample() {{
  const skill = document.getElementById('sample').value;
  if (!skill) return;
  // For now, just re-load the built-in sample; skill-specific templates
  // could be fetched from /api in a future iteration.
  editor.value = JSON.stringify(SAMPLE, null, 2);
  render();
}}

render();
</script>
</body>
</html>"""
