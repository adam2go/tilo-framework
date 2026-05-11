# Tilo Framework

<p align="center">
  <strong>面向 AI-native 产品的运行时框架：把人的决策转成后端动作和确认后的记忆。</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./docs/INTEGRATION_GUIDE.md">集成指南</a> ·
  <a href="./docs/BUILD_YOUR_FIRST_TILO_APP.md">构建 App</a> ·
  <a href="./docs/ARTIFACT_ACTION_RUNTIME.md">Action Runtime</a> ·
  <a href="./docs/MEMORY.md">Memory</a> ·
  <a href="./docs/README.md">文档</a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/adam2go/tilo-framework" />
  <img alt="Stars" src="https://img.shields.io/github/stars/adam2go/tilo-framework?style=social" />
  <img alt="Forks" src="https://img.shields.io/github/forks/adam2go/tilo-framework?style=social" />
  <img alt="Issues" src="https://img.shields.io/github/issues/adam2go/tilo-framework" />
  <img alt="Last Commit" src="https://img.shields.io/github/last-commit/adam2go/tilo-framework" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-reference_UI-black" />
</p>

<p align="center">
  <img alt="Tilo Framework 项目总览：围绕目标、界面、决策、行动和记忆构建 AI-native 产品运行时" src="./docs/assets/tilo-framework-overview.svg" />
</p>

---

## 30 秒看懂

Tilo 是一个开源框架，用于构建 **AI-native 产品流程**：Agent 可以渲染聚焦的交互界面，请人做关键决策，通过后端运行时执行动作，并且只把确认后的学习沉淀为记忆。

它不是“传统 SaaS 后台 + AI 聊天侧边栏”，而是一套运行时层：

```text
Goal -> Surface -> Decision -> Action -> Memory
目标 -> 界面 -> 决策 -> 行动 -> 记忆
```

```bash
git clone https://github.com/adam2go/tilo-framework.git && cd tilo-framework && cp .env.example .env && docker compose up --build
```

打开：

```text
http://localhost:3000/demo
```

你应该会看到一个最小合同审查 Demo：目标优先的对话、聚焦工作区、审批动作，以及可选的记忆确认。确定性本地模式不需要 API key。

---

## 什么时候用 Tilo

当你的产品需要 Agent 做这些事时，可以用 Tilo：

- 把用户目标转成聚焦的决策界面；
- 通过后端拥有语义的运行时执行关键动作；
- 留下可审计的 observation；
- 先提出记忆候选，再由人确认后进入长期记忆。

不要把 Tilo 当成通用 dashboard 模板，也不要把它当成 AI 聊天侧边栏。

---

## Tilo 的差异点

### 1. 确认式记忆，而不是自动写入记忆

很多 Agent 会自动写入记忆。这很容易污染 eval、存错偏好，也让用户失去控制感。

Tilo 把记忆设计成生命周期：

```text
Observation -> Memory Candidate -> Human Confirmation -> Confirmed Memory
观察 -> 记忆候选 -> 用户确认 -> 确认后的记忆
```

Agent 可以提出“我学到了什么”，但由用户决定什么能变成长期记忆。

### 2. 后端拥有动作语义，而不是前端按钮直接改状态

很多 AI demo 里，前端按钮会直接调用某个 API 并修改状态。这会破坏审计链路，也会让每个渠道重复实现同一套逻辑。

Tilo 把关键动作统一交给后端 Artifact Action Runtime：

```text
User action -> ArtifactActionRuntime -> UIInteractionEvent -> ConversationTurn(observation) -> safe side effect
用户动作 -> 动作运行时 -> UI 交互事件 -> 观察 turn -> 安全副作用
```

前端只渲染意图，后端拥有动作语义。

---

## 快速开始

运行本地 Demo：

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
cp .env.example .env
docker compose up --build
```

打开：

```text
http://localhost:3000/demo
```

检查后端健康状态：

```bash
curl http://localhost:8000/api/health
```

无需 API key 验证本地 Demo：

```bash
bash scripts/verify_local_demo.sh
```

预期输出：

```text
✓ backend health ok
✓ frontend /demo route ok
✓ example apps loaded
✓ conversation session created
✓ conversation-native message endpoint completed
✓ demo verification complete
```

旧的 `/demo/telegram` 路由会兼容性跳转到 `/demo`，不再是单独的公开 Demo。

---

## 开发者如何集成 Tilo

Tilo 可以渐进式接入现有产品，你不需要重写整个系统。

| 模式 | 适合场景 | 集成边界 |
|---|---|---|
| Standalone demo | 本地评估 Tilo | 运行 `/demo` |
| Backend runtime sidecar | 已经有自己的前端 | 调用 Tilo REST APIs |
| Embedded components | 想复用参考 AI-native UI | 复用 artifact/action 组件 |
| Declarative Tilo app | 想封装一个可复用 agent workflow | `app.yaml` + `interaction.policy.yaml` |

先看：[`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md)

核心 API：

```text
POST /api/conversations
POST /api/conversations/{session_id}/messages
GET  /api/artifacts?workspace_id=...&task_id=...
POST /api/artifacts/{artifact_id}/actions/{action_id}
POST /api/memories/{memory_id}/confirm
```

---

## 构建一个 Agent App

一个 Tilo app 是一个很小的声明式目录：

```text
app.yaml
interaction.policy.yaml
fixtures or sample inputs
optional README
```

可以从这里开始：

```text
examples/apps/contract-review-agent/
examples/apps/sales-followup-agent/
```

创建新 app：

```bash
python scripts/create_app.py my-agent
python scripts/validate_app.py examples/apps/my-agent
```

开发者参考：

- [`docs/BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md)
- [`docs/APP_MANIFEST.md`](./docs/APP_MANIFEST.md)
- [`docs/INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)
- [`examples/apps/README.md`](./examples/apps/README.md)

---

## 可以构建什么？

| 示例 | Tilo 验证了什么 |
|---|---|
| Contract Review Agent | 决策界面、审批动作、修订草稿、确认式记忆 |
| Sales Follow-up Agent | 第二个 workflow 下声明式 app 的可移植性 |
| Future examples | 不改核心 runtime 扩展更多领域 |

---

## Runtime 模型

```text
Agent App Manifest
-> Interaction Policy
-> Artifact Spec
-> Artifact Action Runtime
-> UIInteractionEvent
-> ConversationTurn(observation)
-> Memory Candidate
-> Human Confirmation
-> Confirmed Memory
```

Tilo 可以参考或兼容 MCP、AG-UI、ACP、A2A，但不会被这些协议牵着走。协议是边界适配层，Tilo 自己拥有产品运行时闭环：目标、界面、决策、行动和记忆。

Skill / Tool / MCP 边界见：[`docs/SKILL_TOOL_MCP_BOUNDARIES.md`](./docs/SKILL_TOOL_MCP_BOUNDARIES.md)。

---

## 仓库结构

```text
backend/       FastAPI 后端和 AI-native runtime contracts
frontend/      Next.js 参考 UI 和最小 /demo 实现
examples/      声明式 agent app examples 和 fixtures
docs/          稳定概念、集成指南、发布文档、历史归档
evals/         Runtime 质量检查和 baseline metrics
scripts/       App validation、scaffold、本地 demo verification
```

---

## Roadmap Focus

继续加功能之前，当前优先级是：

1. 提升 README 和 demo 转化力。
2. 让本地验证在 CI 中持续保持绿色。
3. 不改框架代码跑通第二个 example app。
4. 明确 Skill / Tool / MCP 边界。
5. 把 ArtifactSpec block 分成 core 和 extension 两层。
6. 增加 surface rendering、action completion、memory acceptance 的 baseline eval 指标。

Baseline eval：[`evals/baseline_report.md`](./evals/baseline_report.md)

---

## 文档 / 贡献

- [`docs/README.md`](./docs/README.md)
- [`docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md`](./docs/AI_NATIVE_FRAMEWORK_PRINCIPLES.md)
- [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md)
- [`docs/ARTIFACT_ACTION_RUNTIME.md`](./docs/ARTIFACT_ACTION_RUNTIME.md)
- [`docs/MEMORY.md`](./docs/MEMORY.md)
- [`docs/SKILL_TOOL_MCP_BOUNDARIES.md`](./docs/SKILL_TOOL_MCP_BOUNDARIES.md)
- [`docs/RELEASE_V1_0.md`](./docs/RELEASE_V1_0.md)

Tilo 还很早期，欢迎参与贡献。

贡献前请阅读：

- [`AGENTS.md`](./AGENTS.md)
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)
- [`docs/QUALITY_BAR.md`](./docs/QUALITY_BAR.md)

最重要的一条：

> 不要把 Tilo 做成 SaaS + AI。请始终保留 AI-native runtime loop：Goal -> Surface -> Decision -> Action -> Memory。

---

## License

Apache License 2.0
