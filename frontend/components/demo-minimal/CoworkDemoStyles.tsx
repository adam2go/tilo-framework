export function CoworkDemoStyles() {
  return (
    <style>{`
      .cowork-demo-page {
        min-height: 100vh;
        background:
          radial-gradient(circle at 18% 8%, rgba(23, 111, 122, 0.08), transparent 26%),
          radial-gradient(circle at 88% 12%, rgba(72, 96, 140, 0.08), transparent 28%),
          #f7f7f5;
        color: #171a1f;
      }

      .cowork-topbar {
        align-items: center;
        display: flex;
        height: 58px;
        justify-content: space-between;
        margin: 0 auto;
        max-width: 1240px;
        padding: 0 22px;
      }

      .cowork-brand {
        align-items: center;
        display: flex;
        gap: 10px;
      }

      .cowork-brand small {
        color: #707987;
        display: block;
        font-size: 12px;
        margin-top: 1px;
      }

      .brand-dot {
        align-items: center;
        background: #151a20;
        border-radius: 11px;
        color: white;
        display: inline-flex;
        font-size: 13px;
        font-weight: 800;
        height: 32px;
        justify-content: center;
        width: 32px;
      }

      .cowork-topbar nav {
        align-items: center;
        display: flex;
        gap: 8px;
      }

      .cowork-topbar nav button {
        background: rgba(255, 255, 255, 0.72);
        border: 1px solid rgba(22, 26, 32, 0.1);
        border-radius: 999px;
        color: #4e5968;
        cursor: pointer;
        font-size: 13px;
        min-height: 32px;
        padding: 7px 11px;
      }

      .cowork-topbar nav button.active,
      .cowork-topbar nav button:hover {
        background: white;
        color: #176f7a;
      }

      .cowork-shell {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(340px, 430px);
        gap: 18px;
        margin: 0 auto;
        max-width: 1240px;
        min-height: calc(100vh - 74px);
        padding: 10px 22px 22px;
      }

      .cowork-conversation {
        display: flex;
        flex-direction: column;
        gap: 18px;
        min-height: calc(100vh - 96px);
        padding: 34px min(5vw, 54px) 18px;
      }

      .cowork-intro {
        margin: 24px 0 4px;
        max-width: 760px;
      }

      .cowork-intro h1 {
        font-size: clamp(36px, 6vw, 68px);
        letter-spacing: -0.045em;
        line-height: 0.98;
        margin: 8px 0 14px;
      }

      .cowork-intro p {
        color: #687284;
        font-size: 17px;
        line-height: 1.65;
        margin: 0;
        max-width: 660px;
      }

      .cowork-message {
        align-items: flex-start;
        display: grid;
        gap: 12px;
        grid-template-columns: 42px minmax(0, 680px);
      }

      .cowork-message.user {
        justify-content: end;
      }

      .cowork-message.user .avatar {
        background: #e8ecef;
        color: #2d3540;
      }

      .cowork-message.assistant .avatar {
        background: #171a1f;
        color: white;
      }

      .avatar {
        align-items: center;
        border-radius: 999px;
        display: inline-flex;
        font-size: 12px;
        font-weight: 800;
        height: 42px;
        justify-content: center;
        width: 42px;
      }

      .bubble {
        background: white;
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 20px;
        box-shadow: 0 16px 45px rgba(25, 31, 40, 0.06);
        display: grid;
        gap: 14px;
        line-height: 1.58;
        padding: 16px 18px;
      }

      .cowork-message.user .bubble {
        background: #171a1f;
        color: white;
      }

      .bubble p {
        margin: 0;
      }

      .bubble.muted,
      .bubble.memory {
        color: #5c6675;
      }

      .bubble.muted span {
        align-items: center;
        display: flex;
        gap: 8px;
      }

      .bubble.memory {
        align-items: flex-start;
        grid-template-columns: 22px 1fr;
      }

      .inline-decision,
      .inline-draft,
      .workspace-evidence {
        background: #f8f8f6;
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 16px;
        display: grid;
        gap: 8px;
        padding: 13px;
      }

      .inline-decision strong,
      .inline-draft strong,
      .workspace-evidence strong {
        font-size: 16px;
      }

      .inline-decision p,
      .inline-draft p,
      .workspace-evidence p {
        color: #5f6a79;
        line-height: 1.55;
        margin: 0;
      }

      .cowork-actions {
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 9px;
      }

      .cowork-primary,
      .cowork-secondary,
      .cowork-send,
      .cowork-chip-row button,
      .workspace-open {
        align-items: center;
        border-radius: 999px;
        display: inline-flex;
        gap: 7px;
        min-height: 36px;
        padding: 9px 13px;
        text-decoration: none;
      }

      .cowork-primary,
      .cowork-send {
        background: #176f7a;
        border: 1px solid #176f7a;
        color: white;
        cursor: pointer;
        font-weight: 800;
      }

      .cowork-primary:disabled,
      .cowork-send:disabled,
      .cowork-composer textarea:disabled {
        cursor: not-allowed;
        opacity: 0.55;
      }

      .cowork-secondary,
      .cowork-chip-row button,
      .workspace-open {
        background: white;
        border: 1px solid rgba(22, 26, 32, 0.1);
        color: #2d3540;
        cursor: pointer;
        font-weight: 700;
      }

      .cowork-composer {
        background: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(22, 26, 32, 0.1);
        border-radius: 24px;
        box-shadow: 0 24px 70px rgba(25, 31, 40, 0.09);
        display: grid;
        gap: 12px;
        margin-top: auto;
        padding: 12px;
        position: sticky;
        bottom: 16px;
        z-index: 3;
      }

      .cowork-composer textarea {
        background: transparent;
        border: 0;
        color: #171a1f;
        font: inherit;
        line-height: 1.55;
        min-height: 82px;
        outline: none;
        padding: 8px 10px;
        resize: vertical;
        width: 100%;
      }

      .composer-footer {
        align-items: center;
        display: flex;
        justify-content: space-between;
        gap: 12px;
      }

      .cowork-chip-row {
        align-items: center;
        display: flex;
        flex-wrap: wrap;
        gap: 7px;
      }

      .cowork-chip-row button {
        color: #637083;
        font-size: 13px;
        min-height: 32px;
        padding: 7px 10px;
      }

      .cowork-workspace {
        align-self: stretch;
        background: rgba(255, 255, 255, 0.66);
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 28px;
        box-shadow: 0 24px 80px rgba(25, 31, 40, 0.08);
        margin: 16px 0 0;
        min-height: calc(100vh - 104px);
        overflow: hidden;
        padding: 14px;
        position: sticky;
        top: 72px;
      }

      .workspace-empty,
      .workspace-card {
        background: white;
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 22px;
        box-shadow: 0 18px 50px rgba(25, 31, 40, 0.06);
      }

      .workspace-empty {
        align-content: center;
        color: #687284;
        display: grid;
        gap: 10px;
        min-height: 100%;
        padding: 28px;
        text-align: center;
      }

      .workspace-empty strong {
        color: #171a1f;
        font-size: 19px;
      }

      .workspace-empty span,
      .action-result-chip {
        background: #edf6f7;
        border-radius: 999px;
        color: #176f7a;
        display: inline-flex;
        font-size: 12px;
        font-weight: 800;
        justify-self: center;
        padding: 6px 9px;
      }

      .workspace-card {
        display: grid;
        gap: 16px;
        padding: 18px;
      }

      .workspace-header h2 {
        font-size: 26px;
        letter-spacing: -0.025em;
        line-height: 1.1;
        margin: 6px 0 8px;
      }

      .workspace-header p {
        color: #687284;
        line-height: 1.55;
        margin: 0;
      }

      .workspace-section {
        display: grid;
        gap: 12px;
      }

      .workspace-metrics {
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .workspace-metrics span {
        background: #f8f8f6;
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 16px;
        color: #687284;
        padding: 12px;
      }

      .workspace-metrics strong {
        color: #171a1f;
        display: block;
        font-size: 28px;
        line-height: 1;
        margin-bottom: 5px;
      }

      .workspace-evidence.draft {
        background: #fbfcfd;
      }

      .workspace-open {
        justify-content: center;
      }

      .eyebrow {
        color: #687284;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.04em;
        text-transform: uppercase;
      }

      .cowork-error {
        background: #fff3f2;
        border: 1px solid #f4b7b2;
        border-radius: 16px;
        color: #b42318;
        line-height: 1.45;
        padding: 12px 14px;
      }

      .cowork-drawer-overlay {
        background: rgba(20, 28, 40, 0.18);
        bottom: 0;
        display: flex;
        justify-content: flex-end;
        left: 0;
        position: fixed;
        right: 0;
        top: 0;
        z-index: 50;
      }

      .cowork-drawer {
        background: white;
        border-left: 1px solid rgba(22, 26, 32, 0.1);
        box-shadow: -18px 0 60px rgba(25, 31, 40, 0.16);
        max-width: 430px;
        min-height: 100vh;
        overflow-y: auto;
        padding: 18px;
        width: min(430px, 100vw);
      }

      .cowork-drawer header {
        align-items: center;
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 18px;
      }

      .cowork-drawer h2 {
        font-size: 24px;
        margin: 4px 0 0;
      }

      .cowork-drawer header button {
        align-items: center;
        background: white;
        border: 1px solid rgba(22, 26, 32, 0.1);
        border-radius: 999px;
        cursor: pointer;
        display: inline-flex;
        height: 34px;
        justify-content: center;
        width: 34px;
      }

      .drawer-stack {
        display: grid;
        gap: 9px;
      }

      .drawer-stack p,
      .drawer-stack span {
        background: #f8f8f6;
        border: 1px solid rgba(22, 26, 32, 0.08);
        border-radius: 14px;
        color: #566273;
        line-height: 1.45;
        margin: 0;
        overflow-wrap: anywhere;
        padding: 10px;
      }

      .spin {
        animation: spin 0.9s linear infinite;
      }

      @keyframes spin {
        to { transform: rotate(360deg); }
      }

      @media (max-width: 980px) {
        .cowork-shell {
          grid-template-columns: 1fr;
        }

        .cowork-workspace {
          min-height: auto;
          position: static;
        }

        .cowork-conversation {
          padding: 24px 4px 18px;
        }
      }

      @media (max-width: 640px) {
        .cowork-topbar {
          align-items: flex-start;
          height: auto;
          padding: 14px;
        }

        .cowork-topbar nav {
          flex-wrap: wrap;
          justify-content: flex-end;
        }

        .cowork-shell {
          padding: 4px 12px 16px;
        }

        .cowork-message {
          grid-template-columns: 1fr;
        }

        .avatar {
          display: none;
        }

        .composer-footer {
          align-items: stretch;
          display: grid;
        }

        .cowork-send {
          justify-content: center;
        }
      }
    `}</style>
  );
}
