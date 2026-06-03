"use client";

/**
 * Self-contained CSS for the ACP-style Cowork demo.
 *
 * Modeled after Manus/Cowork conversation+inspector layouts. Kept in
 * CSS-in-style so the demo is portable and we don't fight Tailwind's
 * preflight on these specific selectors.
 *
 * NOTE: We inject the CSS via `dangerouslySetInnerHTML` rather than as
 * children of <style>. React's hydration compares <style> text content
 * between SSR and client, and a long template-literal CSS body has been
 * observed to mismatch (server renders empty string, client fills the
 * body) under Next.js 14 streaming SSR. Using raw HTML side-steps that
 * text-diff entirely.
 */
const CSS = `
      .acp-shell {
        min-height: 100vh;
        background:
          radial-gradient(1200px 600px at 10% -10%, rgba(99, 102, 241, 0.06), transparent 50%),
          radial-gradient(900px 500px at 90% 0%, rgba(34, 197, 94, 0.05), transparent 50%),
          #fafafa;
        color: #111827;
        display: flex;
        flex-direction: column;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Inter",
          "Helvetica Neue", system-ui, sans-serif;
      }

      .acp-topbar {
        align-items: center;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: saturate(140%) blur(8px);
        border-bottom: 1px solid #ececec;
        display: flex;
        height: 56px;
        justify-content: space-between;
        padding: 0 20px;
        position: sticky;
        top: 0;
        z-index: 30;
      }

      .acp-brand { align-items: center; display: flex; gap: 10px; }
      .acp-brand-dot {
        align-items: center;
        background: #111827;
        border-radius: 9px;
        color: #fff;
        display: inline-flex;
        font-weight: 700;
        height: 28px;
        justify-content: center;
        width: 28px;
      }
      .acp-brand strong { font-size: 14px; }
      .acp-brand small { color: #6b7280; display: block; font-size: 11px; margin-top: 1px; }

      .acp-topbar-tools { align-items: center; display: flex; gap: 8px; }

      .acp-mode-badge {
        align-items: center;
        background: #f3f4f6;
        border: 1px solid #e5e7eb;
        border-radius: 999px;
        color: #374151;
        display: inline-flex;
        font-size: 11px;
        gap: 6px;
        padding: 4px 10px;
      }
      .acp-mode-badge .acp-dot {
        background: #9ca3af;
        border-radius: 999px;
        height: 7px;
        width: 7px;
      }
      .acp-mode-badge.live { background: #ecfdf5; border-color: #a7f3d0; color: #065f46; }
      .acp-mode-badge.live .acp-dot { background: #10b981; box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18); }

      .acp-icon-button {
        align-items: center;
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        color: #374151;
        cursor: pointer;
        display: inline-flex;
        font-size: 12px;
        gap: 6px;
        padding: 6px 10px;
        transition: background 120ms;
      }
      .acp-icon-button:hover { background: #f9fafb; }
      .acp-icon-button.active { background: #111827; border-color: #111827; color: #fff; }

      .acp-main {
        display: grid;
        flex: 1;
        gap: 0;
        grid-template-columns: 1fr;
        max-width: 1320px;
        min-height: calc(100vh - 56px);
        padding: 0 20px 32px;
        width: 100%;
        margin: 0 auto;
      }
      .acp-main.with-inspector {
        grid-template-columns: minmax(0, 1fr) 560px;
        gap: 24px;
      }

      .acp-conversation {
        display: flex;
        flex-direction: column;
        min-height: 0;
      }
      .acp-conversation-scroll {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 14px;
        min-height: 0;
        overflow-y: auto;
        padding: 24px 4px;
      }

      .acp-intro {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 14px;
        padding: 20px 22px;
      }
      .acp-eyebrow {
        color: #6b7280;
        font-size: 11px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .acp-intro h1 {
        font-size: 22px;
        font-weight: 600;
        line-height: 1.3;
        margin: 6px 0 8px;
      }
      .acp-intro p { color: #374151; font-size: 14px; line-height: 1.6; }
      .acp-intro-points {
        color: #4b5563;
        display: flex;
        flex-direction: column;
        font-size: 13px;
        gap: 6px;
        list-style: none;
        margin: 14px 0 0;
        padding: 0;
      }
      .acp-intro-points li { align-items: center; display: flex; gap: 8px; }
      .acp-intro-points strong { color: #111827; }

      .acp-bubble {
        align-items: flex-start;
        animation: acp-fade-in 200ms ease-out;
        display: flex;
        gap: 10px;
      }
      .acp-bubble.user { justify-content: flex-end; }
      .acp-bubble.user .acp-bubble-body {
        background: #111827;
        border-radius: 14px 14px 4px 14px;
        color: #fff;
        max-width: 80%;
        padding: 12px 14px;
      }
      .acp-bubble.assistant .acp-bubble-body {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 4px 14px 14px 14px;
        flex: 1;
        padding: 12px 14px;
      }
      .acp-bubble.assistant.muted .acp-bubble-body {
        background: #f9fafb;
        color: #6b7280;
      }
      .acp-bubble.error {
        background: #fef2f2;
        border: 1px solid #fecaca;
        border-radius: 10px;
        color: #991b1b;
        font-size: 13px;
        padding: 10px 12px;
      }

      .acp-avatar {
        align-items: center;
        background: #f3f4f6;
        border-radius: 999px;
        color: #4b5563;
        display: inline-flex;
        flex-shrink: 0;
        height: 28px;
        justify-content: center;
        margin-top: 2px;
        width: 28px;
      }
      .acp-avatar.surface {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #fff;
      }

      .acp-bubble-body.activity { padding: 4px 6px; }
      .acp-activity-summary {
        align-items: center;
        background: transparent;
        border: 0;
        cursor: pointer;
        display: flex;
        gap: 8px;
        padding: 8px 10px;
        text-align: left;
        width: 100%;
      }
      .acp-activity-summary strong { color: #111827; font-size: 13px; }
      .acp-activity-summary small { color: #6b7280; font-size: 11px; margin-left: auto; }
      .acp-chevron { color: #9ca3af; }
      .acp-activity-list {
        border-top: 1px solid #f1f1f1;
        display: flex;
        flex-direction: column;
        list-style: none;
        margin: 0;
        padding: 6px 10px 10px;
        gap: 4px;
      }
      .acp-activity-step {
        align-items: center;
        border-radius: 8px;
        color: #6b7280;
        display: flex;
        font-size: 12px;
        gap: 8px;
        padding: 6px 8px;
      }
      .acp-activity-step.active { background: #f5f3ff; color: #4338ca; }
      .acp-activity-step.done { color: #374151; }
      .acp-activity-step.failed { background: #fef2f2; color: #991b1b; }
      .acp-activity-step.pending { color: #9ca3af; font-style: italic; }
      .acp-activity-step-icon {
        align-items: center;
        background: #f3f4f6;
        border-radius: 999px;
        display: inline-flex;
        height: 22px;
        justify-content: center;
        width: 22px;
        flex-shrink: 0;
      }
      .acp-activity-step.active .acp-activity-step-icon { background: #ddd6fe; }
      .acp-activity-step.failed .acp-activity-step-icon { background: #fee2e2; }
      .acp-activity-step.done .acp-activity-step-icon { background: #ecfdf5; color: #047857; }
      .acp-activity-step-body strong { color: inherit; display: block; font-size: 12px; font-weight: 500; }
      .acp-activity-step-body span { color: #9ca3af; font-size: 11px; }

      .acp-thinking-stream {
        background: linear-gradient(180deg, #faf5ff 0%, #f5f3ff 100%);
        border: 1px solid #e9d5ff;
        border-radius: 8px;
        margin-top: 6px;
        max-height: 160px;
        overflow-y: auto;
        padding: 8px 10px 10px;
      }
      .acp-thinking-label {
        align-items: center;
        color: #6b21a8;
        display: flex;
        font-size: 10px;
        font-weight: 600;
        gap: 4px;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
        text-transform: uppercase;
      }
      .acp-thinking-text {
        color: #4c1d95;
        font-family: -apple-system, "SF Pro Text", "Inter", system-ui, sans-serif;
        font-size: 12px;
        line-height: 1.55;
        white-space: pre-wrap;
        word-break: break-word;
      }
      .acp-thinking-caret {
        animation: acp-blink 1s step-end infinite;
        background: #7c3aed;
        display: inline-block;
        height: 12px;
        margin-left: 2px;
        vertical-align: middle;
        width: 6px;
      }
      @keyframes acp-blink {
        50% { opacity: 0; }
      }

      .acp-bubble.surface .acp-bubble-body {
        padding: 12px 14px;
      }
      .acp-surface-meta {
        align-items: center;
        display: flex;
        gap: 10px;
        margin-bottom: 10px;
      }
      .acp-intent-pill {
        background: #ede9fe;
        border-radius: 999px;
        color: #5b21b6;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 3px 9px;
        text-transform: uppercase;
      }
      .acp-surface-meta small { color: #9ca3af; font-size: 11px; }
      .acp-surface-meta .acp-chip.open-canvas {
        background: #eef2ff;
        color: #4338ca;
        font-size: 11px;
        margin-left: auto;
        padding: 3px 9px;
      }
      .acp-surface-meta .acp-chip.open-canvas:hover { background: #c7d2fe; }

      .acp-action-done {
        align-items: center;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 8px;
        color: #065f46;
        display: flex;
        font-size: 12px;
        gap: 8px;
        padding: 10px 14px;
      }
      .acp-action-done strong { color: #047857; }
      .acp-surface-card {
        background: #fafafa;
        border: 1px solid #ececec;
        border-radius: 10px;
        padding: 14px 16px;
      }
      .acp-surface-card .surface-block { margin-top: 10px; }
      .acp-surface-card .surface-block:first-child { margin-top: 0; }

      .acp-bubble.assistant.muted .acp-bubble-body {
        align-items: flex-start;
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .acp-bubble.assistant.muted strong { color: #111827; font-size: 13px; }
      .acp-bubble.assistant.muted small { color: #6b7280; font-size: 12px; }

      .acp-composer {
        background: #fff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
        margin-top: 16px;
        padding: 12px 14px;
      }
      .acp-composer textarea {
        background: transparent;
        border: 0;
        color: #111827;
        font: inherit;
        outline: none;
        padding: 4px 0 8px;
        resize: none;
        width: 100%;
      }
      .acp-composer textarea::placeholder { color: #9ca3af; }
      .acp-sample-chips {
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 0 0 6px;
      }
      .acp-sample-label {
        color: #9ca3af;
        font-size: 11px;
        margin-right: 2px;
      }
      .acp-chip.followup {
        background: #f5f3ff;
        color: #4338ca;
      }
      .acp-chip.followup:hover { background: #ede9fe; }
      .acp-composer-row {
        align-items: center;
        display: flex;
        gap: 8px;
        justify-content: space-between;
      }
      .acp-chip {
        align-items: center;
        background: #f3f4f6;
        border: 0;
        border-radius: 999px;
        color: #4b5563;
        cursor: pointer;
        display: inline-flex;
        font-size: 12px;
        gap: 6px;
        padding: 6px 12px;
      }
      .acp-chip:hover { background: #e5e7eb; }
      .acp-chip:disabled { cursor: not-allowed; opacity: 0.5; }
      .acp-send {
        align-items: center;
        background: linear-gradient(135deg, #4338ca, #6366f1);
        border: 0;
        border-radius: 999px;
        color: #fff;
        cursor: pointer;
        display: inline-flex;
        font-size: 13px;
        font-weight: 500;
        gap: 6px;
        padding: 8px 16px;
      }
      .acp-send:hover { filter: brightness(1.05); }
      .acp-send:disabled { cursor: not-allowed; opacity: 0.5; }

      .acp-inspector {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 14px;
        display: flex;
        flex-direction: column;
        margin-top: 24px;
        max-height: calc(100vh - 96px);
        overflow: hidden;
        position: sticky;
        top: 76px;
      }
      .acp-inspector-tabs {
        border-bottom: 1px solid #ececec;
        display: flex;
        padding: 8px;
      }
      .acp-inspector-tab {
        align-items: center;
        background: transparent;
        border: 0;
        border-radius: 8px;
        color: #6b7280;
        cursor: pointer;
        display: flex;
        flex: 1;
        font-size: 12px;
        font-weight: 500;
        gap: 6px;
        justify-content: center;
        padding: 8px 4px;
        transition: background 120ms;
      }
      .acp-inspector-tab:hover { background: #f9fafb; }
      .acp-inspector-tab.active { background: #111827; color: #fff; }
      .acp-inspector-tab em {
        background: rgba(0, 0, 0, 0.06);
        border-radius: 999px;
        font-size: 10px;
        font-style: normal;
        padding: 1px 7px;
      }
      .acp-inspector-tab.active em { background: rgba(255, 255, 255, 0.18); }

      .acp-inspector-empty {
        align-items: center;
        color: #9ca3af;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 36px 22px;
        text-align: center;
      }
      .acp-inspector-empty strong { color: #4b5563; font-size: 14px; }
      .acp-inspector-empty p { color: #6b7280; font-size: 12px; line-height: 1.5; margin: 0; }
      .acp-inspector-empty small { color: #9ca3af; font-size: 11px; margin-top: 6px; }

      .acp-inspector-list {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 10px;
        overflow-y: auto;
        padding: 14px 14px 18px;
      }
      .acp-inspector-list h4 {
        color: #6b7280;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.06em;
        margin: 6px 4px 0;
        text-transform: uppercase;
      }
      .acp-inspector-card {
        background: #fafafa;
        border: 1px solid #ececec;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 10px 12px;
      }
      .acp-inspector-card.candidate { border-color: #fde68a; background: #fffbeb; }
      .acp-inspector-card.confirmed { border-color: #a7f3d0; background: #ecfdf5; }
      .acp-inspector-card-head {
        align-items: center;
        display: flex;
        justify-content: space-between;
      }
      .acp-inspector-card code {
        background: rgba(15, 23, 42, 0.04);
        border-radius: 6px;
        color: #1f2937;
        font-size: 11px;
        padding: 2px 6px;
        word-break: break-all;
      }
      .acp-inspector-card small { color: #6b7280; font-size: 11px; }
      .acp-inspector-card p { color: #374151; font-size: 12px; line-height: 1.5; margin: 0; }
      .acp-event-type { color: #4338ca; font-family: ui-monospace, monospace; font-size: 11px; }
      .acp-inspector-link {
        color: #4338ca;
        font-size: 12px;
        margin-top: 6px;
        text-decoration: none;
      }
      .acp-inspector-link:hover { text-decoration: underline; }

      .acp-drawer-overlay {
        background: rgba(15, 23, 42, 0.45);
        bottom: 0;
        display: flex;
        justify-content: flex-end;
        left: 0;
        position: fixed;
        right: 0;
        top: 0;
        z-index: 60;
      }
      .acp-drawer {
        background: #fff;
        box-shadow: -16px 0 40px rgba(15, 23, 42, 0.12);
        display: flex;
        flex-direction: column;
        height: 100%;
        max-width: 440px;
        width: 100%;
      }
      .acp-drawer header {
        align-items: flex-start;
        border-bottom: 1px solid #ececec;
        display: flex;
        justify-content: space-between;
        padding: 18px 22px;
      }
      .acp-drawer h2 { font-size: 18px; margin: 4px 0 0; }
      .acp-drawer header button {
        align-items: center;
        background: #f3f4f6;
        border: 0;
        border-radius: 8px;
        cursor: pointer;
        display: inline-flex;
        height: 30px;
        justify-content: center;
        width: 30px;
      }
      .acp-drawer-body { display: flex; flex-direction: column; gap: 14px; overflow-y: auto; padding: 18px 22px; }
      .acp-drawer-body p { color: #374151; font-size: 13px; line-height: 1.6; margin: 0; }
      .acp-drawer-body code { background: #f3f4f6; border-radius: 4px; padding: 1px 5px; }
      .acp-drawer-stat {
        align-items: center;
        background: linear-gradient(135deg, #f5f3ff, #eef2ff);
        border-radius: 10px;
        display: flex;
        gap: 12px;
        padding: 14px 16px;
      }
      .acp-drawer-stat strong { color: #4338ca; font-size: 26px; line-height: 1; }
      .acp-drawer-stat span { color: #4b5563; font-size: 12px; }
      .acp-drawer-points {
        color: #4b5563;
        display: flex;
        flex-direction: column;
        font-size: 12px;
        gap: 6px;
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .acp-drawer-points li { align-items: center; display: flex; gap: 8px; }

      .spin { animation: acp-spin 700ms linear infinite; }

      @keyframes acp-fade-in {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes acp-spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }

      @media (max-width: 1024px) {
        .acp-main.with-inspector {
          grid-template-columns: 1fr;
        }
        .acp-inspector {
          margin-top: 16px;
          max-height: 60vh;
          position: static;
        }
      }

      @media (max-width: 640px) {
        .acp-topbar-tools .acp-icon-button span { display: none; }
        .acp-bubble.user .acp-bubble-body { max-width: 90%; }
      }

      /* --------------------------------------------------------------- */
      /*  Contract Canvas (right-hand workbench)                         */
      /* --------------------------------------------------------------- */
      .canvas-root {
        display: flex;
        flex-direction: column;
        height: 100%;
        min-height: 0;
      }
      .canvas-tabs {
        border-bottom: 1px solid #ececec;
        display: flex;
        gap: 2px;
        padding: 8px 8px 0;
        background: linear-gradient(180deg, #ffffff 0%, #fafafa 100%);
      }
      .canvas-tab {
        align-items: center;
        background: transparent;
        border: 1px solid transparent;
        border-bottom: 0;
        border-radius: 8px 8px 0 0;
        color: #6b7280;
        cursor: pointer;
        display: inline-flex;
        font-size: 12px;
        font-weight: 500;
        gap: 6px;
        padding: 8px 12px 9px;
        transition: background 120ms, color 120ms;
      }
      .canvas-tab:hover { color: #111827; background: rgba(99, 102, 241, 0.05); }
      .canvas-tab.active {
        background: #fff;
        border-color: #ececec;
        color: #111827;
        margin-bottom: -1px;
        padding-bottom: 10px;
      }
      .canvas-tab em {
        background: rgba(79, 70, 229, 0.12);
        border-radius: 999px;
        color: #4338ca;
        font-size: 10px;
        font-style: normal;
        font-weight: 600;
        padding: 1px 7px;
      }
      .canvas-tab.active em { background: #4338ca; color: #fff; }

      .canvas-body {
        display: flex;
        flex-direction: column;
        flex: 1;
        gap: 14px;
        min-height: 0;
        overflow-y: auto;
        padding: 16px 16px 20px;
      }
      .canvas-body.split {
        display: grid;
        gap: 0;
        grid-template-columns: 240px minmax(0, 1fr);
        overflow: hidden;
        padding: 0;
      }

      .canvas-empty {
        align-items: center;
        color: #6b7280;
        display: flex;
        flex: 1;
        flex-direction: column;
        font-size: 13px;
        gap: 8px;
        justify-content: center;
        padding: 48px 24px;
        text-align: center;
      }
      .canvas-empty-icon {
        background: #f5f3ff;
        border-radius: 14px;
        color: #6d28d9;
        display: inline-flex;
        padding: 12px;
      }
      .canvas-empty strong { color: #111827; font-size: 14px; }
      .canvas-empty p { color: #6b7280; font-size: 12px; line-height: 1.5; margin: 0; }
      .canvas-empty small { color: #9ca3af; font-size: 11px; }

      /* ----- KPIs ----- */
      .canvas-kpis {
        display: grid;
        gap: 8px;
        grid-template-columns: repeat(4, minmax(0, 1fr));
      }
      .canvas-kpi {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        padding: 10px 12px;
      }
      .canvas-kpi strong { color: #111827; font-size: 20px; line-height: 1; }
      .canvas-kpi-label { color: #6b7280; font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; }
      .canvas-kpi.high { background: #fef2f2; border-color: #fecaca; }
      .canvas-kpi.high strong { color: #b91c1c; }
      .canvas-kpi.medium { background: #fffbeb; border-color: #fde68a; }
      .canvas-kpi.medium strong { color: #b45309; }
      .canvas-kpi.low { background: #ecfdf5; border-color: #a7f3d0; }
      .canvas-kpi.low strong { color: #047857; }
      .canvas-kpi.confidence { background: #eef2ff; border-color: #c7d2fe; }
      .canvas-kpi.confidence strong { color: #4338ca; font-size: 16px; padding-top: 3px; }

      /* ----- Distribution ----- */
      .canvas-distribution {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 12px 14px;
      }
      .canvas-distribution-label {
        color: #6b7280;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }
      .canvas-distribution-bar {
        background: #f3f4f6;
        border-radius: 999px;
        display: flex;
        height: 10px;
        overflow: hidden;
      }
      .canvas-distribution-bar .seg.high { background: linear-gradient(180deg, #ef4444, #b91c1c); }
      .canvas-distribution-bar .seg.medium { background: linear-gradient(180deg, #f59e0b, #b45309); }
      .canvas-distribution-bar .seg.low { background: linear-gradient(180deg, #10b981, #047857); }
      .canvas-distribution-summary {
        color: #4b5563;
        font-size: 12px;
        line-height: 1.55;
        margin: 0;
      }

      /* ----- Risks table ----- */
      .canvas-table-wrap {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        overflow: hidden;
      }
      .canvas-table-toolbar {
        align-items: center;
        border-bottom: 1px solid #f1f1f1;
        display: flex;
        gap: 10px;
        justify-content: space-between;
        padding: 10px 14px;
      }
      .canvas-table-title {
        align-items: center;
        color: #111827;
        display: flex;
        font-size: 12px;
        font-weight: 600;
        gap: 6px;
      }
      .canvas-table-sort {
        align-items: center;
        color: #6b7280;
        display: flex;
        font-size: 11px;
        gap: 4px;
      }
      .canvas-table-sort .chip {
        background: #f3f4f6;
        border: 0;
        border-radius: 999px;
        color: #4b5563;
        cursor: pointer;
        font-size: 11px;
        padding: 4px 10px;
      }
      .canvas-table-sort .chip.active { background: #111827; color: #fff; }

      .canvas-risk-table {
        border-collapse: collapse;
        font-size: 12px;
        width: 100%;
      }
      .canvas-risk-table th {
        background: #f9fafb;
        border-bottom: 1px solid #f1f1f1;
        color: #6b7280;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.06em;
        padding: 9px 12px;
        text-align: left;
        text-transform: uppercase;
      }
      .canvas-risk-table td {
        border-bottom: 1px solid #f6f6f6;
        color: #374151;
        padding: 10px 12px;
        vertical-align: top;
      }
      .canvas-risk-table tbody tr { cursor: pointer; transition: background 120ms; }
      .canvas-risk-table tbody tr:hover { background: #fafafa; }
      .canvas-risk-table tbody tr.selected { background: #eef2ff; }
      .canvas-risk-table .clause-cell {
        color: #111827;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 11px;
        white-space: nowrap;
      }
      .canvas-risk-table .issue-cell { color: #374151; line-height: 1.5; }
      .canvas-risk-table .open-cell { width: 1%; white-space: nowrap; }
      .canvas-risk-table .open-link {
        align-items: center;
        color: #4338ca;
        display: inline-flex;
        font-size: 11px;
        font-weight: 500;
        gap: 3px;
      }

      .pill {
        border-radius: 999px;
        display: inline-flex;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 2px 9px;
        text-transform: uppercase;
      }
      .pill-high { background: #fef2f2; color: #b91c1c; }
      .pill-medium { background: #fffbeb; color: #b45309; }
      .pill-low { background: #ecfdf5; color: #047857; }

      /* ----- Clauses split ----- */
      .canvas-clauses-list {
        background: #fafafa;
        border-right: 1px solid #ececec;
        display: flex;
        flex-direction: column;
        min-height: 0;
        overflow-y: auto;
      }
      .canvas-clauses-list > header {
        align-items: center;
        border-bottom: 1px solid #ececec;
        color: #6b7280;
        display: flex;
        font-size: 11px;
        font-weight: 600;
        gap: 6px;
        letter-spacing: 0.06em;
        padding: 10px 12px;
        position: sticky;
        text-transform: uppercase;
        top: 0;
        background: #fafafa;
      }
      .canvas-clauses-list > header em {
        background: rgba(79, 70, 229, 0.12);
        border-radius: 999px;
        color: #4338ca;
        font-size: 10px;
        font-style: normal;
        margin-left: auto;
        padding: 1px 7px;
      }
      .canvas-clauses-list ul {
        display: flex;
        flex-direction: column;
        gap: 2px;
        list-style: none;
        margin: 0;
        padding: 6px;
      }
      .canvas-clauses-list li.empty {
        color: #9ca3af;
        font-size: 12px;
        padding: 14px 10px;
        text-align: center;
      }
      .clause-entry {
        align-items: flex-start;
        background: transparent;
        border: 0;
        border-radius: 8px;
        color: #374151;
        cursor: pointer;
        display: flex;
        gap: 8px;
        padding: 8px 10px;
        text-align: left;
        transition: background 120ms;
        width: 100%;
      }
      .clause-entry:hover { background: #fff; }
      .clause-entry.active { background: #fff; box-shadow: inset 0 0 0 1px #c7d2fe; }
      .clause-entry > div strong {
        color: #111827;
        display: block;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 11px;
      }
      .clause-entry > div small {
        color: #6b7280;
        display: block;
        font-size: 11px;
        line-height: 1.45;
        margin-top: 2px;
      }

      .canvas-reader {
        display: flex;
        flex-direction: column;
        min-height: 0;
      }
      .canvas-reader-head {
        align-items: center;
        background: #fff;
        border-bottom: 1px solid #ececec;
        color: #111827;
        display: flex;
        font-size: 12px;
        font-weight: 600;
        gap: 8px;
        justify-content: space-between;
        padding: 10px 14px;
      }
      .canvas-reader-head > div {
        align-items: center;
        display: flex;
        gap: 6px;
        min-width: 0;
      }
      .canvas-reader-head > div strong {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .canvas-reader-target {
        background: #fffbeb;
        border-radius: 999px;
        color: #b45309;
        font-size: 10px;
        font-weight: 500;
        padding: 3px 9px;
      }

      .canvas-reader-callout {
        background: #eef2ff;
        border-bottom: 1px solid #c7d2fe;
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 16px;
      }
      .canvas-reader-callout .callout-head {
        align-items: center;
        display: flex;
        gap: 8px;
      }
      .canvas-reader-callout .callout-head strong {
        color: #111827;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 12px;
      }
      .canvas-reader-callout p {
        align-items: flex-start;
        color: #374151;
        display: flex;
        font-size: 12px;
        gap: 6px;
        line-height: 1.55;
        margin: 0;
      }
      .canvas-reader-callout p svg { flex-shrink: 0; margin-top: 3px; }
      .canvas-reader-callout .callout-issue { color: #b91c1c; }
      .canvas-reader-callout .callout-revision { color: #047857; }
      .canvas-reader-callout .callout-evidence { color: #6b7280; font-style: italic; }

      .canvas-reader-body {
        flex: 1;
        min-height: 0;
        overflow-y: auto;
        padding: 16px 20px 28px;
      }
      .canvas-reader-placeholder {
        align-items: center;
        color: #9ca3af;
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 32px 10px;
        text-align: center;
      }
      .clause-md { color: #1f2937; font-size: 13px; line-height: 1.7; }
      .clause-md h2 { font-size: 16px; font-weight: 600; margin: 12px 0 6px; color: #111827; }
      .clause-md h3 { font-size: 14px; font-weight: 600; margin: 10px 0 4px; color: #111827; }
      .clause-md h4 { font-size: 13px; font-weight: 600; margin: 8px 0 2px; color: #1f2937; }
      .clause-md p { margin: 4px 0; }
      .clause-md li { list-style: disc; margin-left: 18px; }
      .clause-md code {
        background: #f3f4f6;
        border-radius: 4px;
        font-size: 12px;
        padding: 1px 5px;
      }
      .clause-md .highlighted {
        background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%);
        border-left: 3px solid #f59e0b;
        border-radius: 0 6px 6px 0;
        margin-left: -10px;
        padding: 2px 10px;
        scroll-margin-top: 16px;
      }
      .clause-md h2.highlighted,
      .clause-md h3.highlighted,
      .clause-md h4.highlighted {
        background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%);
        border-left: 3px solid #f59e0b;
        border-radius: 0 6px 6px 0;
        margin-left: -10px;
        padding: 4px 10px;
      }

      /* ----- Revision tab ----- */
      .revision-head {
        align-items: center;
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        color: #4338ca;
        display: flex;
        gap: 10px;
        padding: 12px 14px;
      }
      .revision-head > div { display: flex; flex-direction: column; gap: 2px; }
      .revision-head strong { color: #111827; font-size: 14px; }
      .revision-head small { color: #6b7280; font-size: 11px; }

      .revision-grid {
        display: grid;
        gap: 12px;
        grid-template-columns: minmax(0, 1fr) 220px;
      }
      @media (max-width: 900px) {
        .revision-grid { grid-template-columns: 1fr; }
      }

      .revision-draft, .revision-highlights {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        padding: 14px 16px;
      }
      .section-label {
        align-items: center;
        color: #6b7280;
        display: flex;
        font-size: 10px;
        font-weight: 600;
        gap: 6px;
        letter-spacing: 0.06em;
        margin-bottom: 10px;
        text-transform: uppercase;
      }
      .revision-body p {
        color: #1f2937;
        font-size: 13px;
        line-height: 1.75;
        margin: 0 0 10px;
      }
      .revision-body p:last-child { margin-bottom: 0; }
      .revision-highlights ul {
        display: flex;
        flex-direction: column;
        gap: 8px;
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .revision-highlights li {
        align-items: flex-start;
        color: #065f46;
        display: flex;
        font-size: 12px;
        gap: 6px;
        line-height: 1.5;
      }
      .revision-highlights li svg { flex-shrink: 0; margin-top: 3px; }
      .revision-highlights li.muted { color: #9ca3af; }

      /* ----- System tab (former inspector internals) ----- */
      .system-group {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        padding: 12px 14px;
      }
      .system-group .system-note { color: #9ca3af; font-size: 11px; margin-left: 6px; }
      .system-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .system-list .muted { color: #9ca3af; font-size: 12px; margin: 0; }
      .system-list .muted.tight {
        color: #6b7280;
        font-size: 11px;
        letter-spacing: 0.04em;
        margin: 4px 0 0;
        text-transform: uppercase;
      }
      .system-card {
        background: #fafafa;
        border: 1px solid #ececec;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 8px 10px;
      }
      .system-card .row {
        align-items: center;
        display: flex;
        justify-content: space-between;
      }
      .system-card code {
        background: rgba(15, 23, 42, 0.04);
        border-radius: 6px;
        color: #1f2937;
        font-size: 11px;
        padding: 2px 6px;
        word-break: break-all;
      }
      .system-card small { color: #6b7280; font-size: 11px; }
      .system-card .intent-pill {
        background: #ede9fe;
        border-radius: 999px;
        color: #5b21b6;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 2px 7px;
        text-transform: uppercase;
      }
      .system-card .event-type { color: #4338ca; font-family: ui-monospace, monospace; font-size: 11px; }
      .system-card.candidate { background: #fffbeb; border-color: #fde68a; }
      .system-card.confirmed { background: #ecfdf5; border-color: #a7f3d0; }
      .system-link { color: #4338ca; font-size: 12px; padding: 6px 2px 2px; text-decoration: none; }
      .system-link:hover { text-decoration: underline; }

      @media (max-width: 1024px) {
        .canvas-body.split { grid-template-columns: 1fr; }
        .canvas-clauses-list { border-bottom: 1px solid #ececec; border-right: 0; max-height: 180px; }
      }

      /* --------------------------------------------------------------- */
      /*  ArtifactBlocks (ab-*) — renderers for artifact block types     */
      /* --------------------------------------------------------------- */
      .ab-card {
        background: #fff;
        border: 1px solid #ececec;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        padding: 12px 14px;
      }
      .ab-card.high { border-color: #fecaca; background: #fef2f2; }
      .ab-card.candidate { border-color: #fde68a; background: #fffbeb; }
      .ab-card-head {
        align-items: center;
        display: flex;
        gap: 8px;
        justify-content: space-between;
      }
      .ab-card-head strong { color: #111827; font-size: 13px; }
      .ab-card-head small { color: #6b7280; font-size: 11px; }
      .ab-card p { color: #374151; font-size: 12px; line-height: 1.55; margin: 0; }
      .ab-card-json {
        background: #f9fafb;
        border-radius: 6px;
        color: #374151;
        font-family: ui-monospace, monospace;
        font-size: 11px;
        line-height: 1.5;
        max-height: 180px;
        overflow: auto;
        padding: 8px;
        white-space: pre-wrap;
      }
      .ab-type-pill {
        background: #f3f4f6;
        border-radius: 999px;
        color: #4b5563;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.04em;
        padding: 2px 8px;
        text-transform: uppercase;
      }
      .ab-empty { color: #9ca3af; font-size: 12px; padding: 16px 0; text-align: center; }
      .ab-summary-text { color: #4b5563; font-size: 12px; line-height: 1.55; margin: 0; }

      /* Risk summary */
      .ab-risk-summary { display: flex; flex-direction: column; gap: 12px; }
      .ab-kpis { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); }
      .ab-kpi {
        background: #fff; border: 1px solid #ececec; border-radius: 10px;
        display: flex; flex-direction: column; gap: 2px; padding: 10px 12px;
      }
      .ab-kpi strong { color: #111827; font-size: 20px; line-height: 1; }
      .ab-kpi small { color: #6b7280; font-size: 10px; }
      .ab-kpi-label { color: #6b7280; font-size: 10px; letter-spacing: 0.06em; text-transform: uppercase; }
      .ab-kpi.high { background: #fef2f2; border-color: #fecaca; }
      .ab-kpi.high strong { color: #b91c1c; }
      .ab-kpi.medium { background: #fffbeb; border-color: #fde68a; }
      .ab-kpi.medium strong { color: #b45309; }
      .ab-kpi.low { background: #ecfdf5; border-color: #a7f3d0; }
      .ab-kpi.low strong { color: #047857; }
      .ab-kpi.conf { background: #eef2ff; border-color: #c7d2fe; }
      .ab-kpi.conf strong { color: #4338ca; font-size: 16px; padding-top: 3px; }
      .ab-distribution { background: #fff; border: 1px solid #ececec; border-radius: 10px; display: flex; flex-direction: column; gap: 8px; padding: 12px 14px; }
      .ab-dist-label { color: #6b7280; font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
      .ab-dist-bar { background: #f3f4f6; border-radius: 999px; display: flex; height: 10px; overflow: hidden; }
      .ab-dist-bar .seg.high { background: linear-gradient(180deg, #ef4444, #b91c1c); }
      .ab-dist-bar .seg.medium { background: linear-gradient(180deg, #f59e0b, #b45309); }
      .ab-dist-bar .seg.low { background: linear-gradient(180deg, #10b981, #047857); }

      /* Risk table */
      .ab-risk-table-wrap { background: #fff; border: 1px solid #ececec; border-radius: 10px; overflow: hidden; }
      .ab-table-toolbar { align-items: center; border-bottom: 1px solid #f1f1f1; display: flex; gap: 10px; justify-content: space-between; padding: 10px 14px; }
      .ab-table-title { align-items: center; color: #111827; display: flex; font-size: 12px; font-weight: 600; gap: 6px; }
      .ab-table-sort { align-items: center; color: #6b7280; display: flex; font-size: 11px; gap: 4px; }
      .ab-table-sort .chip { background: #f3f4f6; border: 0; border-radius: 999px; color: #4b5563; cursor: pointer; font-size: 11px; padding: 4px 10px; }
      .ab-table-sort .chip.active { background: #111827; color: #fff; }
      .ab-risk-table { border-collapse: collapse; font-size: 12px; width: 100%; }
      .ab-risk-table th { background: #f9fafb; border-bottom: 1px solid #f1f1f1; color: #6b7280; font-size: 10px; font-weight: 600; letter-spacing: 0.06em; padding: 9px 12px; text-align: left; text-transform: uppercase; }
      .ab-risk-table td { border-bottom: 1px solid #f6f6f6; color: #374151; padding: 10px 12px; vertical-align: top; }
      .ab-risk-table tbody tr { cursor: default; transition: background 120ms; }
      .ab-risk-table tbody tr:hover { background: #fafafa; }
      .ab-risk-table .clause-cell { color: #111827; font-family: ui-monospace, monospace; font-size: 11px; white-space: nowrap; }
      .ab-risk-table .issue-cell { color: #374151; line-height: 1.5; }

      /* Risk radar */
      .ab-radar { background: #fff; border: 1px solid #ececec; border-radius: 10px; padding: 14px 16px; }
      .ab-radar-title { align-items: center; color: #111827; display: flex; font-size: 12px; font-weight: 600; gap: 6px; margin-bottom: 12px; }
      .ab-radar-bars { display: flex; flex-direction: column; gap: 8px; }
      .ab-radar-row { align-items: center; display: flex; gap: 10px; }
      .ab-radar-label { color: #374151; font-size: 11px; min-width: 90px; text-align: right; }
      .ab-radar-track { background: #f3f4f6; border-radius: 999px; flex: 1; height: 10px; overflow: hidden; }
      .ab-radar-fill { border-radius: 999px; height: 100%; transition: width 300ms ease; }
      .ab-radar-fill.high { background: linear-gradient(90deg, #ef4444, #b91c1c); }
      .ab-radar-fill.medium { background: linear-gradient(90deg, #f59e0b, #b45309); }
      .ab-radar-fill.low { background: linear-gradient(90deg, #10b981, #047857); }
      .ab-radar-score { color: #6b7280; font-family: ui-monospace, monospace; font-size: 11px; min-width: 20px; text-align: right; }

      /* Clause reader */
      .ab-clause-reader { display: grid; grid-template-columns: 220px minmax(0, 1fr); height: 100%; min-height: 0; overflow: hidden; }
      .ab-clause-list { background: #fafafa; border-right: 1px solid #ececec; display: flex; flex-direction: column; min-height: 0; overflow-y: auto; }
      .ab-clause-list > header { align-items: center; border-bottom: 1px solid #ececec; color: #6b7280; display: flex; font-size: 11px; font-weight: 600; gap: 6px; letter-spacing: 0.06em; padding: 10px 12px; position: sticky; text-transform: uppercase; top: 0; background: #fafafa; }
      .ab-clause-list > header em { background: rgba(79, 70, 229, 0.12); border-radius: 999px; color: #4338ca; font-size: 10px; font-style: normal; margin-left: auto; padding: 1px 7px; }
      .ab-clause-list ul { display: flex; flex-direction: column; gap: 2px; list-style: none; margin: 0; padding: 6px; }
      .ab-clause-body { display: flex; flex-direction: column; min-height: 0; }
      .ab-clause-callout { background: #eef2ff; border-bottom: 1px solid #c7d2fe; display: flex; flex-direction: column; gap: 6px; padding: 12px 16px; }
      .ab-clause-callout .callout-head { align-items: center; display: flex; gap: 8px; }
      .ab-clause-callout .callout-head strong { color: #111827; font-family: ui-monospace, monospace; font-size: 12px; }
      .ab-clause-callout p { align-items: flex-start; color: #374151; display: flex; font-size: 12px; gap: 6px; line-height: 1.55; margin: 0; }
      .ab-clause-callout p svg { flex-shrink: 0; margin-top: 3px; }
      .ab-clause-callout .callout-issue { color: #b91c1c; }
      .ab-clause-callout .callout-revision { color: #047857; }
      .ab-clause-callout .callout-evidence { color: #6b7280; font-style: italic; }
      .ab-clause-md { color: #1f2937; flex: 1; font-size: 13px; line-height: 1.7; min-height: 0; overflow-y: auto; padding: 16px 20px 28px; }
      .ab-clause-md h2 { font-size: 16px; font-weight: 600; margin: 12px 0 6px; }
      .ab-clause-md h3 { font-size: 14px; font-weight: 600; margin: 10px 0 4px; }
      .ab-clause-md h4 { font-size: 13px; font-weight: 600; margin: 8px 0 2px; }
      .ab-clause-md p { margin: 4px 0; }
      .ab-clause-md .highlighted { background: linear-gradient(90deg, #fef3c7 0%, #fde68a 100%); border-left: 3px solid #f59e0b; border-radius: 0 6px 6px 0; margin-left: -10px; padding: 2px 10px; scroll-margin-top: 16px; }
      @media (max-width: 900px) { .ab-clause-reader { grid-template-columns: 1fr; } .ab-clause-list { border-bottom: 1px solid #ececec; border-right: 0; max-height: 160px; } }

      /* Revision diff */
      .ab-revision-diff { display: flex; flex-direction: column; gap: 14px; }
      .ab-rev-summary { background: #fff; border: 1px solid #ececec; border-radius: 10px; padding: 14px 16px; }
      .ab-rev-summary strong { color: #111827; font-size: 14px; }
      .ab-rev-summary p { color: #374151; font-size: 12px; line-height: 1.7; margin: 6px 0 0; }
      .ab-rev-highlights { display: flex; flex-direction: column; gap: 6px; list-style: none; margin: 10px 0 0; padding: 0; }
      .ab-rev-highlights li { align-items: center; color: #065f46; display: flex; font-size: 12px; gap: 6px; }
      .ab-rev-hunks { display: flex; flex-direction: column; gap: 10px; }
      .ab-rev-hunk { background: #fff; border: 1px solid #ececec; border-radius: 10px; overflow: hidden; }
      .ab-rev-hunk.high { border-color: #fecaca; }
      .ab-rev-hunk.medium { border-color: #fde68a; }
      .ab-rev-hunk .hunk-head { align-items: center; border-bottom: 1px solid #f1f1f1; display: flex; gap: 8px; padding: 10px 14px; }
      .ab-rev-hunk .hunk-head strong { color: #111827; font-family: ui-monospace, monospace; font-size: 12px; }
      .ab-rev-hunk .hunk-grid { display: grid; grid-template-columns: 1fr 1fr; }
      .ab-rev-hunk .hunk-before { background: #fef2f2; border-right: 1px solid #f1f1f1; padding: 10px 14px; }
      .ab-rev-hunk .hunk-after { background: #ecfdf5; padding: 10px 14px; }
      .ab-rev-hunk .hunk-label { color: #6b7280; font-size: 10px; font-weight: 600; letter-spacing: 0.04em; margin-bottom: 4px; text-transform: uppercase; }
      .ab-rev-hunk p { color: #374151; font-size: 12px; line-height: 1.6; margin: 0; }

      /* Doc preview */
      .ab-doc-content { color: #374151; font-size: 12px; line-height: 1.7; margin: 0; white-space: pre-wrap; }
      .ab-doc-highlights { display: flex; flex-direction: column; gap: 4px; list-style: none; margin: 6px 0 0; padding: 0; }
      .ab-doc-highlights li { align-items: center; color: #065f46; display: flex; font-size: 11px; gap: 5px; }

      /* Metrics / insights */
      .ab-metrics { display: flex; flex-direction: column; gap: 12px; }
      .ab-insights { color: #4b5563; display: flex; flex-direction: column; font-size: 12px; gap: 4px; list-style: disc; margin: 0; padding-left: 18px; }

      /* Action queue */
      .ab-action-queue { display: flex; flex-direction: column; gap: 6px; }
      .ab-action-item { align-items: center; background: #fff; border: 1px solid #ececec; border-radius: 8px; display: flex; gap: 10px; padding: 10px 12px; }
      .ab-action-item strong { color: #111827; flex: 1; font-size: 12px; }
      .ab-action-item small { color: #6b7280; font-size: 11px; }
      .ab-action-status { background: #f3f4f6; border-radius: 999px; color: #6b7280; font-size: 10px; font-weight: 600; padding: 2px 8px; text-transform: uppercase; }
      .ab-action-item.ready .ab-action-status { background: #ecfdf5; color: #047857; }
      .ab-action-item.waiting .ab-action-status { background: #fffbeb; color: #b45309; }

      /* Comparison matrix */
      .ab-comparison { overflow-x: auto; }
      .ab-comparison table { border-collapse: collapse; font-size: 12px; width: 100%; }
      .ab-comparison th { background: #f9fafb; border-bottom: 1px solid #ececec; color: #6b7280; font-size: 10px; font-weight: 600; letter-spacing: 0.04em; padding: 8px 12px; text-align: left; text-transform: uppercase; }
      .ab-comparison td { border-bottom: 1px solid #f6f6f6; color: #374151; padding: 8px 12px; }

      /* Markdown */
      .ab-markdown p { color: #374151; font-size: 13px; line-height: 1.6; margin: 0; }
`;

export function CoworkDemoStyles() {
  return <style dangerouslySetInnerHTML={{ __html: CSS }} />;
}
