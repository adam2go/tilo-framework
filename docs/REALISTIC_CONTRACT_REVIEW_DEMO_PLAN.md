# Realistic Contract Review Demo Plan

This document defines how to make Tilo's Contract Review demo feel real, multi-turn, and aligned with the original product thesis:

```text
Agent by default. UI when necessary.
```

The demo should not feel like a fixed button-click walkthrough. It should feel like a user gives Tilo a real contract, the agent reviews it, works autonomously, asks for confirmation only at meaningful points, observes UI actions, continues the task, and proposes memory only when appropriate.

---

## 1. Demo Goal

The demo should prove:

1. A user can upload or paste a real-looking contract.
2. Tilo can review it using deterministic mode or real LLM mode.
3. The agent should not show UI for every step.
4. Lightweight UI appears only when a human decision is needed or important information must be shown.
5. UI clicks become observations.
6. The agent continues after observing user action.
7. Memory is proposed only after a meaningful preference signal.

---

## 2. Sample Contract

Use a realistic but fictional contract:

```text
AI 客服系统定制开发与运维服务合同（问题样例）
```

The contract should intentionally contain issues across:

- scope creep
- ambiguous acceptance
- unfair payment terms
- data/privacy compliance
- subprocessors without approval
- IP ownership ambiguity
- overly broad indemnity
- unrealistic SLA
- asymmetric termination
- unlimited free support
- vague confidentiality survival
- dispute jurisdiction imbalance

The contract file can be used as the default demo fixture.

Recommended fixture names:

```text
examples/contracts/problematic-ai-service-agreement.md
examples/contracts/problematic-ai-service-agreement.docx
```

If storing binary `.docx` in the repo is not preferred, keep the markdown source in the repo and provide a script to generate the docx.

---

## 3. Required Demo Entry

The user should be able to choose:

```text
Use sample contract
Upload contract
Paste contract text
```

For v0.1:

- `Use sample contract` is required.
- `Paste contract text` is required.
- `Upload contract` can be implemented if file handling already exists; otherwise it can be a disabled/coming soon option.

Do not block the demo on file upload.

---

## 4. Recommended Multi-turn Flow

### Turn 1: User provides contract

User message:

```text
请审查这份合同，重点关注付款、验收、数据合规、知识产权、责任限制和终止条款。
```

Attachment or selected sample:

```text
AI 客服系统定制开发与运维服务合同（问题样例）.docx
```

### Turn 2: Agent works autonomously

Agent should reply without asking for unnecessary confirmation:

```text
我已经读完合同。大部分条款可以继续自动审查，但有 1 个关键问题需要你确认处理方向：责任限制与赔偿条款存在明显冲突，可能影响后续修订策略。
```

### Turn 3: Mini UI appears only for the key decision

Render one mini surface:

```text
重要问题：责任限制与赔偿范围冲突

发现条款：8.1 与 8.2
问题：8.1 设置赔偿上限，但 8.2 又排除了大量场景，导致乙方实际责任可能接近无限。
建议：将责任例外限定为数据泄露、知识产权侵权、故意或重大过失，并排除间接损失。

[生成保守修订稿]
[改为平衡立场]
[打开完整审查]
```

### Turn 4: User clicks a UI action

User clicks:

```text
生成保守修订稿
```

System shows observation:

```text
Observation: user approved conservative revision for liability and indemnity clauses.
```

### Turn 5: Agent continues

Agent replies:

```text
收到。我会按“保守但可谈判”的方向生成修订建议，并同时保留可解释的商业理由。
```

Render compact revision preview:

```text
修订建议预览
- 赔偿上限保留为已付款金额 100%-150%
- 数据泄露、知识产权侵权、故意或重大过失作为例外
- 间接损失、商誉损失、预期利润损失默认排除
- 系统不可用按服务信用或封顶违约金处理

[继续生成完整修订稿]
[语气更温和]
[打开完整审查]
```

### Turn 6: User continues with text

User types:

```text
语气不要太强硬，适合发给客户谈判。
```

Agent replies:

```text
明白。我会把修改建议调整成更适合谈判沟通的表达，而不是直接否定对方条款。
```

### Turn 7: Memory proposal

After the user expresses a preference, Tilo can propose memory:

```text
我注意到你偏好“保守但谈判友好”的合同修订风格。以后审查合同时是否记住这个偏好？

[记住]
[编辑]
[暂不]
```

### Turn 8: User confirms memory

Observation:

```text
Observation: user confirmed contract review style preference.
```

Agent reply:

```text
已记住。以后合同审查会优先采用保守但谈判友好的修订风格。
```

---

## 5. Expected Review Findings

The sample contract should give the model enough material to find realistic issues.

Expected high/medium risk categories:

### 5.1 Scope creep

Clause examples:

- requirements can be changed at any time
- no additional fee unless client agrees
- subjective acceptance until client satisfaction

Expected finding:

```text
需求变更边界不清，乙方可能承担无限范围的免费变更义务。
```

### 5.2 Acceptance ambiguity

Clause examples:

- 3-day acceptance period
- silence means non-acceptance
- client confirmation required indefinitely

Expected finding:

```text
验收机制不确定，缺少客观验收标准和视为验收通过机制。
```

### 5.3 Payment imbalance

Clause examples:

- 10% prepayment
- 90% paid only after 180 days stable operation
- delayed payment is not breach
- provider cannot suspend service

Expected finding:

```text
付款周期过长且缺少逾期责任，服务方现金流和履约风险较高。
```

### 5.4 Data/privacy compliance

Clause examples:

- customer phone/address/purchase records
- use data for internal model training
- no separate data processing agreement
- subprocessors without consent

Expected finding:

```text
个人信息处理、训练用途、子处理方和数据安全责任缺少明确约束。
```

### 5.5 IP ownership conflict

Clause examples:

- client owns customized work only after full payment
- provider must deliver source code even if unpaid
- client can share with third parties

Expected finding:

```text
知识产权归属、付款条件、源代码交付和第三方使用权之间存在冲突。
```

### 5.6 SLA unrealistic

Clause examples:

- 99.99% availability
- 10-minute response
- 30-minute full fix
- 20% penalty after one hour

Expected finding:

```text
服务等级过高且违约金过重，缺少排除项和服务信用机制。
```

### 5.7 Liability contradiction

Clause examples:

- liability cap equals paid amount
- many exceptions remove cap
- indirect losses included

Expected finding:

```text
责任上限与例外范围冲突，可能导致实质无限责任。
```

### 5.8 Asymmetric termination

Clause examples:

- client can terminate with 3 days notice for any reason
- provider needs 90 days and client consent
- provider still provides 180 days free transition

Expected finding:

```text
解除权高度不对等，乙方退出机制和后续义务过重。
```

---

## 6. UI Requirements

### 6.1 Default UI

The page is a Telegram-like conversation.

Do not show a full dashboard by default.

### 6.2 Mini surfaces only when needed

Default mini surfaces:

- ImportantIssueCard
- ApprovalCard
- RevisionPreviewCard
- MemoryCandidateCard

### 6.3 Rich surface escalation

`Open Full Review` should open or reveal a rich review artifact with:

- full list of findings
- clause references
- evidence excerpts
- suggested revisions
- grouped risk categories

The rich surface is not the default view.

### 6.4 File realism

Show selected file in the conversation:

```text
Attached: AI 客服系统定制开发与运维服务合同（问题样例）.docx
```

If upload is not implemented, show sample selection as a file-like chip.

---

## 7. Backend Requirements

### 7.1 Contract text input

The LLM prompt should include:

- user instruction
- contract text or extracted file text
- previous conversation turns
- UI observations
- confirmed memories if available

### 7.2 File handling v0.1

If full `.docx` parsing is not implemented yet, use one of these approaches:

1. Store markdown/plain-text fixture and use it for sample contract.
2. Allow pasted contract text.
3. Add `.docx` extraction later using a library such as `python-docx`.

### 7.3 Multi-turn context

Follow-up user messages should include:

- current artifact id
- current run id
- active issue id
- recent observations
- user instruction

### 7.4 Durable observations

Actions must persist:

- approval clicked
- open full review clicked
- revision tone adjusted
- memory confirmed

---

## 8. LLM Requirements

Contract review prompt should instruct the model to:

1. Read the full contract.
2. Identify issues by clause number.
3. Prioritize only the most decision-relevant issue for mini UI.
4. Generate complete findings for full review artifact.
5. Ask for confirmation only when human direction matters.
6. Avoid creating UI for every finding.
7. Generate memory only after user preference is expressed.

### Output shape

Recommended high-level output:

```json
{
  "summary": "...",
  "primary_issue": {
    "title": "责任限制与赔偿范围冲突",
    "clauses": ["8.1", "8.2"],
    "risk_level": "high",
    "why_it_matters": "...",
    "recommended_action": "..."
  },
  "all_findings": [],
  "recommended_revision": "...",
  "needs_user_confirmation": true,
  "memory_candidate": null
}
```

---

## 9. Acceptance Criteria

The demo is acceptable when:

1. It uses a real-looking sample contract.
2. The user can choose sample contract or paste text.
3. The agent appears to read and review the contract autonomously.
4. Only one key mini surface appears by default.
5. The mini surface is tied to a real clause/risk.
6. User action becomes visible observation.
7. Agent continues after observation.
8. Follow-up text changes the revision direction.
9. Memory proposal appears only after a meaningful preference signal.
10. Full review is available through `Open Full Review`.
11. Deterministic mode and LLM mode both work.

---

## 10. Codex Prompt

```text
Read docs/REALISTIC_CONTRACT_REVIEW_DEMO_PLAN.md and docs/INTERACTION_MINIMALISM_AND_AGENT_AUTONOMY.md.

Upgrade /demo/telegram into a realistic multi-turn contract review demo.

The demo must use a real-looking problematic sample contract, not just a fixed prompt.

Requirements:
1. Add sample contract mode using examples/contracts/problematic-ai-service-agreement.md or equivalent fixture.
2. Add paste contract text mode.
3. Show the selected contract as an attachment/file chip in the chat.
4. Agent should review autonomously and then show only one important mini surface by default.
5. Use the liability/indemnity conflict as the primary mini-surface issue.
6. User action such as Approve Revision must create visible observation and persist UIInteractionEvent where supported.
7. Agent should continue after approval and render a compact revision preview.
8. Support a follow-up text message such as “语气不要太强硬，适合发给客户谈判”.
9. After the follow-up preference, propose a memory card.
10. Open Full Review should reveal or open a rich artifact with all findings.
11. Preserve deterministic and LLM modes.
12. Do not render UI for every finding. UI appears only when confirmation or important information is needed.

Goal:
The demo should feel like a real agent reviewing a real contract and asking for human input only at meaningful moments.
```
