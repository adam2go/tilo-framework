"""Tilo AIP Viewer — preview any spec in a browser with zero setup.

Usage:
    import tilo

    spec = tilo.generate("Review this contract", model="gpt-4o", api_key="sk-...")

    # Open in browser (no React install needed)
    tilo.view(spec)

    # Save as standalone HTML file
    tilo.save_html(spec, "report.html")

    # Display inline in Jupyter / Colab
    tilo.notebook(spec)

    # Get HTML string
    html = tilo.to_html(spec)
"""

from __future__ import annotations

import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


# --------------------------------------------------------------------------- #
# HTML renderer (self-contained, no external deps)                             #
# --------------------------------------------------------------------------- #

_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       background: #f8fafc; color: #1e293b; line-height: 1.5; }
.container { max-width: 900px; margin: 0 auto; padding: 24px 16px 64px; }
.header { margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e2e8f0; }
.header h1 { font-size: 1.5rem; font-weight: 700; color: #0f172a; }
.header .meta { font-size: 0.8rem; color: #94a3b8; margin-top: 4px; }
.views { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.view-tab { padding: 6px 14px; border-radius: 20px; border: 1px solid #e2e8f0;
            background: white; font-size: 0.82rem; cursor: pointer;
            color: #64748b; transition: all .15s; }
.view-tab:hover { border-color: #6366f1; color: #6366f1; }
.view-tab.active { background: #6366f1; border-color: #6366f1; color: white; }
.view-content { display: none; }
.view-content.active { display: block; }
.blocks { display: flex; flex-direction: column; gap: 12px; }
/* Block styles */
.block-heading { display: flex; align-items: center; gap: 8px; border-radius: 8px;
                 border: 1px solid; padding: 10px 14px; }
.block-heading h3 { font-size: 1rem; font-weight: 600; }
.sev-info  { border-color: #e2e8f0; background: white; color: #1e293b; }
.sev-low   { border-color: #6ee7b7; background: #f0fdf4; color: #065f46; }
.sev-med   { border-color: #fcd34d; background: #fffbeb; color: #92400e; }
.sev-high  { border-color: #fca5a5; background: #fef2f2; color: #991b1b; }
.block-text { padding: 2px 4px; font-size: 0.9rem; color: #475569; white-space: pre-wrap; }
.block-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px;
              padding: 14px 16px; }
.block-card .card-title { font-size: 0.82rem; font-weight: 600; color: #64748b;
                           text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 6px; }
.block-card .card-body  { font-size: 0.9rem; color: #1e293b; }
.metrics-row { display: flex; gap: 12px; flex-wrap: wrap; }
.metric-card { background: white; border: 1px solid #e2e8f0; border-radius: 10px;
               padding: 14px 18px; flex: 1; min-width: 120px; }
.metric-label { font-size: 0.78rem; color: #64748b; text-transform: uppercase;
                letter-spacing: 0.05em; }
.metric-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; margin-top: 2px; }
.metric-delta { font-size: 0.78rem; color: #16a34a; margin-top: 2px; }
.block-table { overflow-x: auto; }
.block-table table { width: 100%; border-collapse: collapse; font-size: 0.88rem;
                     background: white; border-radius: 10px; overflow: hidden;
                     border: 1px solid #e2e8f0; }
.block-table th { background: #f1f5f9; color: #64748b; font-weight: 600;
                  padding: 9px 14px; text-align: left; font-size: 0.8rem; }
.block-table td { padding: 9px 14px; border-top: 1px solid #f1f5f9; color: #374151; }
.block-list ul { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.block-list li { display: flex; align-items: flex-start; gap: 8px; font-size: 0.9rem; }
.block-list li::before { content: "·"; color: #94a3b8; margin-top: 1px; }
.block-code { border-radius: 8px; overflow: hidden; }
.code-lang { background: #1e293b; color: #94a3b8; padding: 6px 14px; font-size: 0.78rem; font-family: mono; }
.code-body { background: #0f172a; color: #e2e8f0; padding: 14px; font-family: 'JetBrains Mono',monospace;
             font-size: 0.82rem; overflow-x: auto; white-space: pre; }
.block-diff { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.diff-before, .diff-after { border-radius: 8px; overflow: hidden; font-size: 0.82rem; }
.diff-label { padding: 5px 12px; font-weight: 600; font-size: 0.78rem; }
.diff-before .diff-label { background: #fee2e2; color: #991b1b; }
.diff-after  .diff-label { background: #dcfce7; color: #166534; }
.diff-code   { font-family: mono; white-space: pre-wrap; padding: 10px 12px; }
.diff-before .diff-code  { background: #fef2f2; color: #7f1d1d; }
.diff-after  .diff-code  { background: #f0fdf4; color: #14532d; }
.diff-unified { border-radius: 8px; overflow: hidden; font-family: mono; font-size: 0.82rem; }
.diff-line { padding: 2px 10px; }
.diff-add  { background: #dcfce7; color: #166534; }
.diff-del  { background: #fee2e2; color: #991b1b; }
.diff-ctx  { color: #64748b; }
.diff-hunk { background: #eff6ff; color: #3b82f6; }
.block-timeline { position: relative; margin-left: 8px; border-left: 2px solid #e2e8f0; padding-left: 20px; display: flex; flex-direction: column; gap: 16px; }
.tl-item { position: relative; }
.tl-dot  { position: absolute; left: -27px; top: 4px; width: 12px; height: 12px;
           border-radius: 50%; background: #6366f1; border: 2px solid white; }
.tl-time { font-size: 0.78rem; color: #94a3b8; }
.tl-title{ font-size: 0.9rem; font-weight: 600; margin-top: 2px; }
.tl-desc { font-size: 0.85rem; color: #64748b; margin-top: 2px; }
.block-kanban { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.kanban-col { min-width: 160px; flex: 1; background: #f8fafc; border: 1px solid #e2e8f0;
              border-radius: 10px; padding: 12px; }
.kanban-col-title { font-size: 0.72rem; font-weight: 700; color: #94a3b8;
                    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.kanban-card { background: white; border: 1px solid #e2e8f0; border-radius: 6px;
               padding: 8px 10px; margin-bottom: 6px; }
.kanban-card p { font-size: 0.84rem; font-weight: 500; color: #1e293b; }
.kanban-card small { font-size: 0.78rem; color: #94a3b8; }
.block-chart { background: white; border: 1px solid #e2e8f0; border-radius: 10px;
               padding: 16px; }
.block-chart canvas { display: block; }
.chart-title { font-size: 0.88rem; font-weight: 600; color: #374151; margin-bottom: 12px; }
.block-confirmation { background: white; border: 2px solid #e2e8f0; border-radius: 10px;
                      padding: 16px; display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.conf-high { border-color: #fca5a5; background: #fef2f2; }
.conf-med  { border-color: #fcd34d; background: #fffbeb; }
.block-confirmation p { font-size: 0.9rem; color: #374151; }
.block-confirmation .risk-badge { font-size: 0.72rem; font-weight: 700; padding: 3px 8px;
                                   border-radius: 4px; white-space: nowrap; }
.risk-high { background: #fca5a5; color: #991b1b; }
.risk-med  { background: #fde68a; color: #92400e; }
.risk-low  { background: #6ee7b7; color: #065f46; }
.block-memory { background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 10px; padding: 14px; }
.memory-label { font-size: 0.72rem; font-weight: 700; color: #6366f1; text-transform: uppercase;
                letter-spacing: 0.06em; margin-bottom: 6px; }
.memory-content { font-size: 0.9rem; color: #3730a3; }
.memory-sal { font-size: 0.78rem; color: #818cf8; margin-top: 4px; }
.block-checklist ul { list-style: none; display: flex; flex-direction: column; gap: 7px; }
.block-checklist li { display: flex; gap: 10px; align-items: flex-start; }
.block-checklist label { font-size: 0.88rem; cursor: pointer; color: #374151; }
.block-checklist input { margin-top: 3px; accent-color: #6366f1; }
.block-rating { display: flex; align-items: center; gap: 12px; }
.block-rating .stars span { font-size: 1.4rem; cursor: pointer; }
.block-rating .stars span.lit { color: #f59e0b; }
.block-rating .stars span.dim { color: #d1d5db; }
.block-rating label { font-size: 0.88rem; color: #374151; }
.block-btns { display: flex; flex-wrap: wrap; gap: 8px; }
.btn-primary { background: #1e293b; color: white; border: none; border-radius: 7px;
               padding: 9px 18px; font-size: 0.88rem; font-weight: 500; cursor: pointer; transition: .15s; }
.btn-primary:hover { background: #0f172a; }
.btn-default { background: white; color: #374151; border: 1px solid #d1d5db; border-radius: 7px;
               padding: 9px 18px; font-size: 0.88rem; font-weight: 500; cursor: pointer; transition: .15s; }
.btn-default:hover { border-color: #6366f1; color: #6366f1; }
.block-tool { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 14px; }
.tool-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.tool-name  { font-size: 0.88rem; font-weight: 600; color: #374151; }
.badge-ok  { background: #dcfce7; color: #166534; }
.badge-err { background: #fee2e2; color: #991b1b; }
.tool-badge { font-size: 0.72rem; font-weight: 600; padding: 2px 7px; border-radius: 4px; font-family: mono; }
.tool-output { font-family: mono; font-size: 0.82rem; color: #475569;
               white-space: pre-wrap; overflow-x: auto; }
.block-progress-bar { padding: 4px 0; }
.prog-track { height: 6px; background: #e2e8f0; border-radius: 9999px; overflow: hidden; }
.prog-fill  { height: 100%; background: #6366f1; border-radius: 9999px; transition: width .3s; }
.prog-label { font-size: 0.78rem; color: #94a3b8; margin-top: 4px; }
.follow-ups { margin-top: 28px; padding: 16px 20px; background: white;
              border: 1px solid #e2e8f0; border-radius: 10px; }
.follow-ups h4 { font-size: 0.8rem; font-weight: 700; color: #94a3b8;
                 text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 10px; }
.follow-ups ul { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.follow-ups li { font-size: 0.88rem; color: #6366f1; cursor: pointer; padding: 6px 10px;
                 border-radius: 6px; transition: .1s; border: 1px solid transparent; }
.follow-ups li:hover { background: #eef2ff; border-color: #c7d2fe; }
.follow-ups li::before { content: "→ "; }
.block-fallback { background: #f8fafc; border: 1px dashed #e2e8f0; border-radius: 8px;
                  padding: 12px; color: #94a3b8; font-size: 0.85rem; }
.block-form { background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }
.form-field { margin-bottom: 12px; }
.form-label { display: block; font-size: 0.82rem; font-weight: 500; color: #374151; margin-bottom: 4px; }
.form-input { width: 100%; border: 1px solid #d1d5db; border-radius: 6px;
              padding: 7px 10px; font-size: 0.88rem; color: #1e293b; }
.form-input:focus { outline: none; border-color: #6366f1; }
"""

_CHART_JS = """
function renderChart(el, props) {
  const type = (props.chart_type || 'bar').toLowerCase();
  const axes = props.axes || [];
  if (!axes.length && props.labels && props.datasets) {
    // Recharts format fallback
    const labels = props.labels;
    const ds = (props.datasets || [])[0] || {};
    const data = (ds.data || []).map((v, i) => ({ label: labels[i] || i, score: v }));
    renderBarChart(el, data);
    return;
  }
  if (type === 'radar') renderRadar(el, axes);
  else if (type === 'pie') renderPie(el, axes);
  else renderBarChart(el, axes);
}

function COLORS() { return ['#6366f1','#22c55e','#f59e0b','#ef4444','#06b6d4','#a855f7']; }

function renderBarChart(el, axes) {
  const max = Math.max(...axes.map(a => +a.score || 0), 1);
  const w = 360, h = 180, pad = 36;
  const bw = Math.max(10, (w - 2*pad) / axes.length - 6);
  let svg = `<svg viewBox="0 0 ${w} ${h}" width="100%" style="max-width:${w}px">`;
  // y-axis
  svg += `<line x1="${pad}" y1="10" x2="${pad}" y2="${h-pad}" stroke="#e2e8f0"/>`;
  svg += `<line x1="${pad}" y1="${h-pad}" x2="${w-10}" y2="${h-pad}" stroke="#e2e8f0"/>`;
  axes.forEach((ax, i) => {
    const x = pad + i * ((w-pad-10)/axes.length) + ((w-pad-10)/axes.length - bw) / 2;
    const barH = ((+ax.score||0) / max) * (h - pad - 10);
    const y = h - pad - barH;
    svg += `<rect x="${x}" y="${y}" width="${bw}" height="${barH}" rx="3" fill="${COLORS()[i%COLORS().length]}"/>`;
    const label = String(ax.label || '').substring(0,10);
    svg += `<text x="${x+bw/2}" y="${h-4}" text-anchor="middle" font-size="9" fill="#94a3b8">${label}</text>`;
    svg += `<text x="${x+bw/2}" y="${y-3}" text-anchor="middle" font-size="9" fill="#64748b">${ax.score}</text>`;
  });
  svg += '</svg>';
  el.innerHTML = svg;
}

function renderRadar(el, axes) {
  const n = axes.length; if (!n) return;
  const cx=180, cy=100, r=70;
  const max = Math.max(...axes.map(a => +a.score||0), 1);
  function pt(i, val) {
    const a = (i * 2 * Math.PI / n) - Math.PI/2;
    const rv = (val/max)*r;
    return [cx + rv*Math.cos(a), cy + rv*Math.sin(a)];
  }
  let svg = `<svg viewBox="0 0 360 200" width="100%" style="max-width:360px">`;
  // grid
  [0.25,0.5,0.75,1].forEach(f => {
    const pts = axes.map((_,i) => pt(i,f*max).join(',')).join(' ');
    svg += `<polygon points="${pts}" fill="none" stroke="#f1f5f9"/>`;
  });
  // axes
  axes.forEach((_,i) => {
    const [x,y] = pt(i,max);
    svg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#e2e8f0"/>`;
  });
  // data
  const pts = axes.map((a,i) => pt(i,+a.score||0).join(',')).join(' ');
  svg += `<polygon points="${pts}" fill="#6366f133" stroke="#6366f1" stroke-width="2"/>`;
  // labels
  axes.forEach((a,i) => {
    const [x,y] = pt(i,max*1.2);
    const label = String(a.label||'').substring(0,12);
    svg += `<text x="${x}" y="${y}" text-anchor="middle" font-size="9" fill="#64748b">${label}</text>`;
  });
  svg += '</svg>';
  el.innerHTML = svg;
}

function renderPie(el, axes) {
  const total = axes.reduce((s,a)=>s+(+a.score||0),0)||1;
  const cx=100, cy=100, r=80;
  let svg = `<svg viewBox="0 0 260 200" width="100%" style="max-width:260px">`;
  let angle = -Math.PI/2;
  axes.forEach((ax,i) => {
    const slice = ((+ax.score||0)/total)*Math.PI*2;
    const x1=cx+r*Math.cos(angle), y1=cy+r*Math.sin(angle);
    angle += slice;
    const x2=cx+r*Math.cos(angle), y2=cy+r*Math.sin(angle);
    const large = slice > Math.PI ? 1 : 0;
    svg += `<path d="M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large},1 ${x2},${y2} Z" fill="${COLORS()[i%COLORS().length]}"/>`;
    // legend
    svg += `<rect x="185" y="${14+i*18}" width="10" height="10" rx="2" fill="${COLORS()[i%COLORS().length]}"/>`;
    svg += `<text x="200" y="${23+i*18}" font-size="9" fill="#64748b">${String(ax.label||'').substring(0,12)}</text>`;
  });
  svg += '</svg>';
  el.innerHTML = svg;
}
"""

_RENDER_JS = """
function renderBlock(block) {
  const el = document.createElement('div');
  const props = block.props || block.data || {};
  const type = block.type;

  if (type === 'heading') {
    el.className = 'block-heading sev-' + (props.severity || 'info');
    el.innerHTML = `<h3>${esc(props.text || block.title || '')}</h3>`;
  } else if (type === 'markdown') {
    el.className = 'block-text';
    el.textContent = props.content || '';
  } else if (type === 'card') {
    el.className = 'block-card sev-' + (props.severity || 'info');
    el.innerHTML = `<div class="card-title">${esc(props.title || block.title || '')}</div>
                    <div class="card-body">${esc(props.content || '')}</div>`;
  } else if (type === 'metric') {
    el.className = 'metric-card';
    el.innerHTML = `<div class="metric-label">${esc(props.label || block.title || '')}</div>
                    <div class="metric-value">${esc(String(props.value || ''))}</div>
                    ${props.delta ? `<div class="metric-delta">${esc(props.delta)}</div>` : ''}`;
    return el; // returned raw for grouping
  } else if (type === 'table') {
    el.className = 'block-table';
    const cols = (props.columns || []).map(c => typeof c === 'string' ? {key:c,label:c} : c);
    const rows = props.rows || [];
    let t = `<table><thead><tr>${cols.map(c=>`<th>${esc(c.label)}</th>`).join('')}</tr></thead><tbody>`;
    rows.forEach(row => {
      t += '<tr>' + cols.map((c,ci) => `<td>${esc(Array.isArray(row) ? row[ci] : row[c.key] || '')}</td>`).join('') + '</tr>';
    });
    t += '</tbody></table>';
    el.innerHTML = t;
  } else if (type === 'list') {
    el.className = 'block-list';
    const items = props.items || [];
    el.innerHTML = '<ul>' + items.map(it => {
      const text = typeof it === 'string' ? it : it.text || '';
      return `<li>${esc(text)}</li>`;
    }).join('') + '</ul>';
  } else if (type === 'code') {
    el.className = 'block-code';
    el.innerHTML = `<div class="code-lang">${esc(props.language || props.lang || 'text')}</div>
                    <pre class="code-body">${esc(props.content || props.code || '')}</pre>`;
  } else if (type === 'diff') {
    el.className = 'block-diff-wrapper';
    if (props.diff) {
      el.className = 'diff-unified';
      const lines = String(props.diff || '').split('\\n');
      el.innerHTML = lines.map(l => {
        let cls = 'diff-ctx';
        if (l.startsWith('+++') || l.startsWith('---')) cls = 'diff-hunk';
        else if (l.startsWith('+')) cls = 'diff-add';
        else if (l.startsWith('-')) cls = 'diff-del';
        else if (l.startsWith('@@')) cls = 'diff-hunk';
        return `<div class="diff-line ${cls}">${esc(l || ' ')}</div>`;
      }).join('');
    } else {
      el.className = 'block-diff';
      el.innerHTML = `
        <div class="diff-before"><div class="diff-label">Before</div><pre class="diff-code">${esc(props.before||'')}</pre></div>
        <div class="diff-after"><div class="diff-label">After</div><pre class="diff-code">${esc(props.after||'')}</pre></div>`;
    }
  } else if (type === 'timeline') {
    el.className = 'block-timeline';
    (props.items || []).forEach(item => {
      const li = document.createElement('div');
      li.className = 'tl-item';
      li.innerHTML = `<div class="tl-dot"></div>
        <div class="tl-time">${esc(item.time||'')}</div>
        <div class="tl-title">${esc(item.title||'')}</div>
        ${item.description ? `<div class="tl-desc">${esc(item.description)}</div>` : ''}`;
      el.appendChild(li);
    });
  } else if (type === 'kanban') {
    el.className = 'block-kanban';
    (props.columns || []).forEach(col => {
      const colEl = document.createElement('div');
      colEl.className = 'kanban-col';
      colEl.innerHTML = `<div class="kanban-col-title">${esc(col.title||'')}</div>`;
      (col.cards || []).forEach(card => {
        const c = document.createElement('div');
        c.className = 'kanban-card';
        c.innerHTML = `<p>${esc(card.title||'')}</p>${card.description?`<small>${esc(card.description)}</small>`:''}`;
        colEl.appendChild(c);
      });
      el.appendChild(colEl);
    });
  } else if (type === 'chart') {
    el.className = 'block-chart';
    if (block.title) el.innerHTML = `<div class="chart-title">${esc(block.title)}</div>`;
    const canvas = document.createElement('div');
    el.appendChild(canvas);
    setTimeout(() => renderChart(canvas, props), 0);
  } else if (type === 'confirmation') {
    const rl = props.risk_level || 'low';
    el.className = `block-confirmation conf-${rl === 'high' ? 'high' : rl === 'medium' ? 'med' : ''}`;
    el.innerHTML = `<p>${esc(props.description || block.title || 'Confirmation required')}</p>
                    <span class="risk-badge risk-${rl === 'high' ? 'high' : rl === 'medium' ? 'med' : 'low'}">${esc(rl)}</span>`;
  } else if (type === 'memory_card') {
    el.className = 'block-memory';
    el.innerHTML = `<div class="memory-label">Memory candidate</div>
                    <div class="memory-content">${esc(props.content || props.summary || block.title || '')}</div>
                    ${props.confidence != null ? `<div class="memory-sal">confidence ${Math.round(+props.confidence * 100)}%</div>` : ''}`;
  } else if (type === 'checklist') {
    el.className = 'block-checklist';
    let ul = '<ul>';
    (props.items || []).forEach((item, i) => {
      const text = typeof item === 'string' ? item : item.text || '';
      const checked = typeof item === 'object' && item.checked ? 'checked' : '';
      ul += `<li><input type="checkbox" id="cl_${block.id}_${i}" ${checked}>
               <label for="cl_${block.id}_${i}">${esc(text)}</label></li>`;
    });
    el.innerHTML = ul + '</ul>';
  } else if (type === 'rating') {
    el.className = 'block-rating';
    const max = +props.max || 5;
    const val = +props.value || 0;
    let stars = '<div class="stars">';
    for (let i = 1; i <= max; i++) {
      stars += `<span class="${i <= val ? 'lit' : 'dim'}" onclick="updateRating(this,${i})">${i <= val ? '★' : '☆'}</span>`;
    }
    el.innerHTML = `${stars}</div><label>${esc(props.label || block.title || '')}</label>`;
  } else if (type === 'button_group') {
    el.className = 'block-btns';
    (props.buttons || []).forEach(btn => {
      const b = document.createElement('button');
      b.className = btn.variant === 'primary' ? 'btn-primary' : 'btn-default';
      b.textContent = btn.label || '';
      el.appendChild(b);
    });
  } else if (type === 'progress') {
    el.className = 'block-progress-bar';
    const pct = Math.max(0, Math.min(100, +(props.percent || 0)));
    el.innerHTML = `<div class="prog-track"><div class="prog-fill" style="width:${pct}%"></div></div>
                    <div class="prog-label">${pct}%</div>`;
  } else if (type === 'tool_preview') {
    el.className = 'block-tool';
    const ok = props.status !== 'error';
    el.innerHTML = `<div class="tool-header">
                      <span class="tool-name">${esc(props.tool_name || block.title || 'Tool')}</span>
                      <span class="tool-badge ${ok ? 'badge-ok' : 'badge-err'}">${esc(props.status || 'success')}</span>
                    </div>
                    ${props.output != null ? `<pre class="tool-output">${esc(String(props.output).substring(0,500))}</pre>` : ''}`;
  } else if (type === 'form') {
    el.className = 'block-form';
    let f = '';
    (props.fields || []).forEach(field => {
      f += `<div class="form-field"><label class="form-label">${esc(field.label || field.name || '')}</label>
             <input class="form-input" type="${field.kind === 'number' ? 'number' : field.kind === 'date' ? 'date' : 'text'}"
                    placeholder="${esc(field.placeholder || '')}"></div>`;
    });
    el.innerHTML = f + `<button class="btn-primary" style="margin-top:4px">Submit</button>`;
  } else {
    el.className = 'block-fallback';
    el.innerHTML = `<strong>${esc(block.type)}</strong> — ${esc(block.title || '')}`;
  }
  return el;
}

function esc(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function updateRating(star, val) {
  const stars = star.parentElement.children;
  for (let i = 0; i < stars.length; i++) {
    stars[i].textContent = i < val ? '★' : '☆';
    stars[i].className = i < val ? 'lit' : 'dim';
    stars[i].onclick = () => updateRating(stars[i], i+1);
  }
}

function renderSpec(spec, container) {
  container.innerHTML = '';
  const header = document.createElement('div');
  header.className = 'header';
  header.innerHTML = `<h1>${esc(spec.title || 'Tilo Surface')}</h1>
    <div class="meta">tilo/aip/v1 · ${(spec.blocks||[]).length} blocks · ${(spec.views||[]).length} views</div>`;
  container.appendChild(header);

  const blocks = spec.blocks || [];
  const views = spec.views || [];

  if (views.length === 0) {
    const bd = document.createElement('div');
    bd.className = 'blocks';
    // Group consecutive metrics
    renderBlockList(blocks, bd);
    container.appendChild(bd);
  } else {
    const tabs = document.createElement('div');
    tabs.className = 'views';
    const contents = [];
    views.forEach((view, vi) => {
      const tab = document.createElement('button');
      tab.className = 'view-tab' + (vi === 0 ? ' active' : '');
      tab.textContent = view.label || view.id;
      const vc = document.createElement('div');
      vc.className = 'view-content' + (vi === 0 ? ' active' : '');
      const bd = document.createElement('div');
      bd.className = 'blocks';
      const viewBlocks = (view.block_ids || []).map(id => blocks.find(b => b.id === id)).filter(Boolean);
      renderBlockList(viewBlocks, bd);
      vc.appendChild(bd);
      contents.push({ tab, vc });
      tab.onclick = () => {
        contents.forEach(c => { c.tab.classList.remove('active'); c.vc.classList.remove('active'); });
        tab.classList.add('active'); vc.classList.add('active');
      };
      tabs.appendChild(tab);
      container.appendChild(vc);
    });
    container.insertBefore(tabs, container.querySelector('.view-content'));
  }

  if ((spec.follow_ups || []).length) {
    const fu = document.createElement('div');
    fu.className = 'follow-ups';
    fu.innerHTML = '<h4>Follow-up suggestions</h4><ul>' +
      (spec.follow_ups || []).map(f => `<li>${esc(f)}</li>`).join('') + '</ul>';
    container.appendChild(fu);
  }
}

function renderBlockList(blocks, container) {
  let i = 0;
  while (i < blocks.length) {
    if (blocks[i].type === 'metric') {
      // Group consecutive metrics into a row
      const row = document.createElement('div');
      row.className = 'metrics-row';
      while (i < blocks.length && blocks[i].type === 'metric') {
        row.appendChild(renderBlock(blocks[i]));
        i++;
      }
      container.appendChild(row);
    } else {
      container.appendChild(renderBlock(blocks[i]));
      i++;
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const specEl = document.getElementById('__tilo_spec__');
  if (!specEl) return;
  try {
    const spec = JSON.parse(specEl.textContent);
    renderSpec(spec, document.getElementById('app'));
  } catch(e) {
    document.getElementById('app').innerHTML = '<p style="color:red">Failed to parse spec: ' + e.message + '</p>';
  }
});
"""

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<script type="application/json" id="__tilo_spec__">{spec_json}</script>
<div class="container" id="app"></div>
<script>{chart_js}{render_js}</script>
</body>
</html>"""


def to_html(
    spec: Any,
    title: str | None = None,
) -> str:
    """Convert a Tilo AIP spec to a standalone HTML string.

    The HTML is fully self-contained — no external CDN, no JS frameworks.
    Renders all 20 AIP block types with interactive elements (checkboxes,
    ratings, charts, diffs, timelines, kanban boards, etc.).

    Args:
        spec:  An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        title: Optional page title (defaults to spec.title).

    Returns:
        A complete HTML document as a string. Can be saved to a .html file
        or served via HTTP.

    Example:
        html = tilo.to_html(spec)
        Path("report.html").write_text(html)
    """
    spec_dict = _to_dict(spec)
    page_title = title or spec_dict.get("title", "Tilo Surface")
    spec_json = json.dumps(spec_dict, ensure_ascii=False)
    return _HTML_TEMPLATE.format(
        title=page_title,
        css=_CSS,
        spec_json=spec_json,
        chart_js=_CHART_JS,
        render_js=_RENDER_JS,
    )


def save_html(
    spec: Any,
    path: str | Path,
    title: str | None = None,
) -> Path:
    """Save a Tilo AIP spec as a standalone HTML file.

    Args:
        spec:  An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        path:  Output file path (e.g. "report.html").
        title: Optional page title.

    Returns:
        The resolved Path of the saved file.

    Example:
        tilo.save_html(spec, "contract-review.html")
        # → opens contract-review.html in your browser
    """
    p = Path(path)
    p.write_text(to_html(spec, title=title), encoding="utf-8")
    return p.resolve()


def save_spec(spec: Any, path: str | Path) -> Path:
    """Save a Tilo AIP spec as a JSON file (round-trippable with ``load_spec``).

    Unlike ``save_html`` (which is for viewing), this saves the raw spec so you
    can reload, edit, or re-render it later — e.g. to keep a review template.

    Args:
        spec: An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        path: Output file path (e.g. "review.json").

    Returns:
        The resolved Path of the saved file.

    Example:
        tilo.save_spec(spec, "contract-template.json")
        later = tilo.load_spec("contract-template.json")
    """
    p = Path(path)
    p.write_text(json.dumps(_to_dict(spec), indent=2, ensure_ascii=False), encoding="utf-8")
    return p.resolve()


def load_spec(path: str | Path) -> Any:
    """Load a Tilo AIP spec from a JSON file saved with ``save_spec``.

    Returns a validated ``ArtifactSpecV1`` when the schema is available,
    otherwise the raw dict. The result is accepted by ``view`` / ``to_html``.

    Args:
        path: Path to a spec JSON file.

    Returns:
        An ``ArtifactSpecV1`` (validated) or a dict.
    """
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        from tilo.schemas.artifact import ArtifactSpecV1
        return ArtifactSpecV1.model_validate(data)
    except Exception:  # noqa: BLE001 — fall back to the raw dict
        return data


def view(
    spec: Any,
    title: str | None = None,
    port: int = 0,
    auto_close_seconds: int = 300,
) -> None:
    """Preview a Tilo AIP spec in the default browser.

    Starts a temporary local HTTP server, serves the rendered spec,
    opens the browser, and shuts down after the timeout.

    Args:
        spec:               An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        title:              Optional page title.
        port:               Port to listen on (0 = auto-assign).
        auto_close_seconds: Seconds before the server shuts down (default: 300).

    Example:
        import tilo

        spec = tilo.generate("Review this contract", model="gpt-4o", api_key="sk-...")
        tilo.view(spec)   # opens browser immediately, no React needed
    """
    html = to_html(spec, title=title)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        def log_message(self, format, *args):
            pass  # suppress access log

    server = HTTPServer(("127.0.0.1", port), Handler)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}"

    def _shutdown():
        time.sleep(auto_close_seconds)
        server.shutdown()

    threading.Thread(target=_shutdown, daemon=True).start()
    print(f"  Tilo viewer  →  {url}")
    webbrowser.open(url)
    server.serve_forever()


def notebook(spec: Any, title: str | None = None) -> None:
    """Display a Tilo AIP spec inline in a Jupyter or Colab notebook.

    Args:
        spec:  An ``ArtifactSpecV1`` instance, a dict, or a JSON string.
        title: Optional display title.

    Example:
        from tilo import generate, notebook

        spec = generate("Plan a Tokyo trip", model="gpt-4o")
        notebook(spec)   # renders inline in Jupyter / Colab
    """
    try:
        from IPython.display import HTML, display
    except ImportError:
        raise ImportError("IPython is required: pip install ipython")

    html_str = to_html(spec, title=title)
    # Wrap in an iframe to isolate styles
    iframe_html = (
        '<iframe srcdoc="{src}" style="width:100%;height:600px;border:none;border-radius:8px;" '
        'allowfullscreen></iframe>'
    ).format(src=html_str.replace('"', "&quot;").replace("'", "&#39;"))
    display(HTML(iframe_html))


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _to_dict(spec: Any) -> dict:
    if isinstance(spec, str):
        return json.loads(spec)
    if isinstance(spec, dict):
        return spec
    # ArtifactSpecV1 or similar Pydantic model
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    if hasattr(spec, "dict"):
        return spec.dict()
    raise TypeError(f"Cannot convert {type(spec)} to AIP dict")
