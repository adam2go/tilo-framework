# Tilo Framework

<p align="center">
  <strong>开源的 AI Agent 产品运行时：让 Agent 渲染决策、执行动作、沉淀经人确认的记忆。</strong>
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
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="pip install" src="https://img.shields.io/badge/pip%20install-tilo-indigo" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-009688" />
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-reference_UI-black" />
  <img alt="Dependencies" src="https://img.shields.io/badge/运行时依赖-8-green" />
</p>

---

## 为什么是 Tilo

大多数 AI Agent 框架止步于**编排 LLM 调用**——给你链、图、工具路由，然后让你自己想办法把它做成产品。

Tilo 从它们结束的地方开始。它是 Agent 推理与用户屏幕之间的**产品运行时层**：

```text
目标 → 界面 → 决策 → 行动 → 记忆
Goal → Surface → Decision → Action → Memory
```

一个接入 Tilo 的 Agent 不只是返回文本。它会**渲染聚焦的交互界面**，请人做**真实决策**，通过**后端拥有语义的运行时**执行动作，并且只把人**明确确认**的内容沉淀为记忆。

这是 AI demo 和 AI-native 产品的分水岭。

---

## 30 秒上手

```bash
pip install tilo
tilo serve
```

打开 `http://localhost:8000/api/health` 确认后端已启动。

完整体验（含参考前端）：

```bash
git clone https://github.com/adam2go/tilo-framework.git
cd tilo-framework
make install   # pip install + pnpm install
make dev       # 后端 :8000 + 前端 :3000
```

打开 `http://localhost:3000/demo`——选一个场景，看 Agent 思考、渲染、向你请示决策。

---

## 三个内置 Demo

每个 Demo 都跑在同一套运行时上。Canvas 根据 Agent 产出的 Artifact 自动适配——不需要改任何前端代码。

| 场景 | Agent 做了什么 | Canvas 视图 |
|---|---|---|
| **合同审查** 📋 | 阅读完整合同，按条款标注 8 个风险，起草保守修订意见 | 风险 · 条款 · 修订 · 记忆 |
| **销售跟进** 📊 | 分析管线，排序热门客户，建议外呼行动 | 管线 · 行动计划 |
| **竞品分析** 🏆 | 对比市场定位，识别差距和优势 | 对比 · 下一步 |

三个场景都支持**多轮对话**：第一轮完成后，会出现基于 Agent 实际产出的上下文感知的追问建议。支持中英文切换。

---

## Tilo 的差异点

### 1. 确认式记忆——不是自动写入

很多 Agent 会静默写入记忆。这会污染评估、存错偏好、让用户失去控制感。

Tilo 把记忆设计成有人类把关的生命周期：

```text
观察 → 记忆候选 → 用户确认 → 确认后的记忆
```

Agent 提出"我学到了什么"。用户决定什么能留下。

### 2. 后端拥有动作语义——不是前端按钮直接改状态

典型 AI demo 里，前端按钮直接调 API、改状态。这会打断审计链路，让每个渠道重复实现同一套逻辑。

Tilo 把每个关键动作交给后端 Artifact Action Runtime：

```text
用户点击 → 动作运行时 → UI 交互事件 → 观察记录 → 安全副作用
```

前端只渲染意图。后端拥有语义。

### 3. Artifact 驱动的 Canvas——不是写死的 UI

右侧 Canvas 不是固定面板。它读取每个 Artifact 声明的 `views`，按 block 类型渲染匹配的组件。合同审查 Agent 产出 Risks/Clauses/Revision tab，销售 Agent 产出 Pipeline/Actions tab。**Canvas 永远不变——只有 Artifact 在变。**

任何新 Agent 都可以声明自己的 views 和 block 类型，前端零改动。

### 4. 设计上的轻量

```text
后端：   8 个运行时依赖 · 103 个源文件 · pip install tilo
前端：   4 个运行时依赖 · 32 个源文件  · pnpm install
```

没有 LangChain。不强制向量数据库。没有重量级编排层。SQLite 开箱即用，准备好了再换 Postgres。

---

## 协议边界

MCP 连接工具。AG-UI 传递 Agent/UI 事件。LangGraph 编排图。A2A 路由多 Agent。

Tilo 不和它们竞争——它在它们之上一层。它拥有**产品运行时闭环**：Agent 输出变成用户面前的决策、后端动作和经确认的记忆的那段路。MCP、AG-UI、ACP、A2A 都可以做底层适配器。

---

## 开发者如何集成

Tilo 为渐进式集成设计，你不需要重写产品。

| 模式 | 适合场景 | 接触面 |
|---|---|---|
| **独立运行** | 本地评估 Tilo | `pip install tilo && tilo serve` |
| **后端 sidecar** | 已有自己的前端 | 调用 Tilo REST APIs |
| **嵌入组件** | 想用 AI-native UI 构建块 | 复用 React artifact/action 组件 |
| **声明式 App** | 封装可复用的 Agent 工作流 | `app.yaml` + `interaction.policy.yaml` |

核心 API：

```text
POST /api/conversations                          创建会话
POST /api/conversations/{id}/messages             发送消息 → Task → Run
GET  /api/runs/{id}/trace                         实时链路追踪
GET  /api/runs/{id}/surface-turns                 已渲染的 Surface
GET  /api/artifacts?workspace_id=...&task_id=...  完整 Artifact（含 views）
POST /api/memories/{id}/confirm                   确认记忆候选
```

完整集成指南见 [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md)。

---

## 构建 Agent App

一个 Tilo App 是一个很小的声明式目录：

```text
my-agent/
  app.yaml                    # Agent 身份与能力声明
  interaction.policy.yaml     # 什么时候出 UI、什么时候静默
  fixtures/                   # 示例输入（可选）
  README.md
```

脚手架：

```bash
tilo init my-agent           # 或者：python scripts/create_app.py my-agent
```

三个内置示例：

```text
examples/apps/contract-review-agent/
examples/apps/sales-followup-agent/
examples/apps/competitive-analysis-agent/
```

参考文档：[`BUILD_YOUR_FIRST_TILO_APP.md`](./docs/BUILD_YOUR_FIRST_TILO_APP.md) · [`APP_MANIFEST.md`](./docs/APP_MANIFEST.md) · [`INTERACTION_POLICY.md`](./docs/INTERACTION_POLICY.md)

---

## 运行时模型

```text
用户目标
  → Task + Run
    → 记忆召回
    → 技能选择
    → 工具执行
    → LLM 生成（流式思考在 Trace 中实时可见）
    → 交互策略（逐步判断：出 Surface / 静默 / 收集输入）
    → Artifact + Views（Canvas tab 自动生成）
    → Surface Turns（对话侧决策）
    → 确认收件箱（高风险动作需人工确认）
    → 记忆候选（仅经人确认后沉淀）
```

每一步都记录在 Trace 中。每个动作都产生 UIInteractionEvent。每条记忆都需要确认。没有黑箱。

---

## 仓库结构

```text
backend/       Python 包 `tilo` — FastAPI 运行时，8 个依赖，pip 可安装
frontend/      @tilo/frontend — Next.js 参考 UI，4 个依赖，Artifact 驱动的 Canvas
examples/      声明式 Agent App 和合同 fixture
docs/          架构、协议、集成指南、设计原则
evals/         运行时质量检查和 baseline 指标
scripts/       App 脚手架、验证、本地 Demo 验证
```

---

## 路线图

**v0.1（当前）**——完整工作闭环 + 三个端到端 Demo。

- [x] 后端 + 前端本地可运行
- [x] Task → Run → Trace → Artifact → Surface → Confirmation → Memory 完整闭环
- [x] 三个 Demo 场景（合同审查、销售跟进、竞品分析）
- [x] 多轮对话 + 上下文感知的追问建议
- [x] Artifact 驱动的 Canvas + 动态 views
- [x] `pip install tilo` + `tilo serve` CLI
- [x] LLM streaming + 思考过程实时可见
- [ ] CI 流水线持续绿灯
- [ ] 发布到 PyPI
- [ ] 前端组件 npm 包

**未来**——Skill 市场、MCP 适配层、多 Agent 路由、带确认门控的真实工具执行。

---

## 参与贡献

Tilo 还处于早期阶段，完全开源，欢迎参与。

贡献前请阅读：

- [`AGENTS.md`](./AGENTS.md) — 给 AI 编程 Agent 的开发规则
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/PROJECT_CONSTITUTION.md`](./docs/PROJECT_CONSTITUTION.md)

最重要的一条：

> **不要把 Tilo 做成"SaaS + AI 侧边栏"。始终保留 AI-native 运行时闭环：目标 → 界面 → 决策 → 行动 → 记忆。**

---

## License

MIT License
