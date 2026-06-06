# Tilo Framework

<p align="center">
  <strong>把任何 LLM 变成可交互 UI。一行 Python —— 无需 React，无需前端配置。</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> ·
  <a href="./docs/tutorials/quickstart.md">5 分钟上手</a> ·
  <a href="./docs/AIP_DESIGN.md">AIP 设计文档</a> ·
  <a href="./docs/INTEGRATION_GUIDE.md">集成指南</a> ·
  <a href="./examples/integrations/">示例</a> ·
  <a href="./docs/README.md">文档</a>
</p>

<p align="center">
  <img alt="License" src="https://img.shields.io/github/license/adam2go/tilo-framework" />
  <img alt="Stars" src="https://img.shields.io/github/stars/adam2go/tilo-framework?style=social" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue" />
  <img alt="pip install" src="https://img.shields.io/badge/pip%20install-tilo-indigo" />
  <img alt="npm" src="https://img.shields.io/badge/npm-@adam2go/tilo--react-cb3837" />
</p>

---

## 30 秒生成第一个界面

```bash
pip install tilo openai
```

```python
import tilo

spec = tilo.generate(
    "审查这份 SaaS 合同的付款、责任和知识产权风险。",
    model="gpt-4o",          # 或 claude-opus-4-8，自动识别 provider
)

tilo.view(spec)              # 在浏览器中打开，就这么简单
```

LLM 不再返回一大段文字，而是生成一个**结构化、可交互的界面**：风险雷达图、
修订前后对比、检查清单、人工审批门控、记忆候选卡片，组织成多个标签页。
**零前端配置**即可渲染。

<p align="center">
  <img alt="一个 Tilo 界面：标题、指标、雷达图、diff、检查清单、确认门控和记忆卡片 —— 全部由一次 LLM 调用生成" src="./docs/assets/tilo-surface-hero.png" width="620" />
</p>

> 没有 API key？运行 `tilo demo` 即可打开这个示例界面。
> 想动手试试？`tilo serve` 然后打开 `http://localhost:8000/playground`
> —— 实时编辑器：粘贴任意 spec，立即渲染。

---

## 为什么在 LLM 越来越强时仍有价值

模型越强，文字答案越好 —— 但一大段文字终究还是一大段文字。瓶颈不在模型
**知道什么**，而在用户**如何对它采取行动**。Tilo 把模型输出变成用户可以
**点击、编辑、批准、拒绝**的东西，再把这些操作变成模型可以学习的结构化信号。

无论模型多强，三件事始终有价值：

1. **结构化 UI 胜过纯文字**：做决策时，一张风险图 + 审批门控永远胜过三段文字。
2. **人工确认是基础设施，不是功能**：模型越强 → 执行的动作风险越高 → 你需要
   *更多*结构化门控，而不是更少。
3. **确认式记忆，而非自动记忆**：一个自信的模型自动存入错误偏好是危险的。
   Tilo 提出候选，由人确认。

---

## 完整 ROAM 闭环 Demo

一次真实的 Tilo 运行 —— Agent 召回记忆、规划、调工具、生成可交互
artifact，最后把它作为可点可拖的 UI 交还给用户。**这个 demo 不需要任何 LLM key。**

https://github.com/user-attachments/assets/1afed79d-e85e-414a-954f-e0be136b9c7d

> **Plan a SF weekend** —— 完全跑在内置 fixture 上。另外两个 demo（PR 评审 ·
> 销售简报）见下文。 ↓

<p align="center">
  <img alt="Tilo AIP 架构总览：四层架构 + 生态定位" src="./docs/assets/tilo-framework-overview-zh.svg" />
</p>

---

## 与你的技术栈无缝集成

已经在用 OpenAI、Anthropic 或 LangChain？一行 import 即可。

```python
# OpenAI
from tilo.adapters.openai import generate_aip_spec
spec = generate_aip_spec(OpenAI(), "分析 Q3 销售管线", skill="sales_dashboard")

# Anthropic
from tilo.adapters.anthropic_sdk import generate_aip_spec
spec = generate_aip_spec(Anthropic(), "审查这个 PR", skill="code_review", document=diff)

# LangChain / LangGraph
from tilo.adapters.langchain import generate_aip_spec
spec = generate_aip_spec(ChatOpenAI(model="gpt-4o"), "规划一次东京之旅")
```

12 个内置 **skill**（合同审查、代码评审、事故响应、会议纪要、bug 报告、行程
规划……）为你的领域定制输出 —— 也可以加载你自己的 `skill.yaml`。用
`AIPPromptBuilder` 接入任意 LLM 客户端，或转换你已有的响应。

---

## 为什么是 Tilo

**Tilo 是一个库,不是框架。** 你已经有自己的 Agent(自研循环、LangGraph、CrewAI 都行)。
Tilo 只做一件事:把模型输出变成一个**结构化、可交互的界面**——一份由带类型的块
(chart、diff、table、checklist、confirmation、memory_card)组成的声明式 spec,
一个函数就能渲染,不需要前端。

```python
spec = tilo.generate("审查这份合同", model="gpt-4o")   # → 一份 spec(数据)
tilo.view(spec)                                        # → 直接渲染,无需 React
```

精简安装就是字面意义的精简:`pip install tilo` **只装 pydantic + PyYAML**。
完整服务器运行时(会话、记忆、ROAM 闭环)是可选的 `tilo[server]`——多数人用不到。

### 与生态里其它东西互补

Tilo 不替代你的工具、编排器或 agent-UI 传输层,它只补上"产出结构化界面"这一层。

| 层 | 归属 | Tilo 的关系 |
|---|---|---|
| 工具调用 | MCP | `mcp_*` 适配器 → 把工具结果渲染成界面 |
| 编排 | LangChain / CrewAI / LangGraph | 从你的 chain 调 `generate_aip_spec(llm, …)` |
| Agent ↔ App 传输 | **AG-UI**(CopilotKit) | **互操作适配器** —— 把 Tilo 界面作为 AG-UI 事件发出 |
| Agent 间通信 | A2A / ACP | `a2a_*` / `acp_*` 适配器 → 渲染结果 |

### Tilo 和 AG-UI 是配合,不是竞争

[AG-UI](https://docs.ag-ui.com) 是一个**事件流协议**,把 Agent 的实时活动带进
chat/copilot 界面(通过 CopilotKit)。Tilo 产出的是一份**声明式 artifact**,有没有
前端都能渲染。两者可以组合:让你的 AG-UI agent 把 Tilo 界面作为 generative UI 发出。

|                  | **AG-UI**                       | **Tilo**                               |
|------------------|---------------------------------|----------------------------------------|
| 形态             | 事件流(过程)                   | 声明式 spec(一份 artifact)           |
| 前端             | 需要客户端运行时(CopilotKit)   | 任意渲染——浏览器 / Jupyter / HTML / React |
| UI 形状          | chat / copilot                  | 结构化界面(报告、评审、看板)          |
| 集成成本         | 接入协议 + 搭前端               | `pip install tilo` + 一个函数          |

```python
from tilo.adapters.agui import tilo_spec_to_agui_events
events = tilo_spec_to_agui_events(spec)   # 注入 CopilotKit 应用
```

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
make dev       # 后端 :8000 + 前端 :4001（Ctrl-C 同时停掉）
```

两个入口：

- `http://localhost:4001/demo` —— 经典场景选择器
- `http://localhost:4001/canvas` —— **3D Agent Canvas**：实时观看 Agent 流式 trace + 在 3D 空间渲染可交互工作台

> **零配置即可跑通。** Canvas 在没有任何 LLM key 时也能工作 —— "Plan a SF Weekend" 用内置 fixture 跑完整流程。在 `.env` 中设置 `LLM_ENABLED=true` 加上 provider key 即可解锁另外两个 LLM 驱动样例。

---

## 架构：四层设计

### 第一层 — 核心 Spec + 运行时

~20 个**原语块类型**（类似 HTML 标签：`markdown`、`table`、`chart`、`diff`、`form`、`card`……），加上开放扩展机制。任何字符串都是合法的 block type——未知类型用通用 JSON 查看器兜底渲染。

三大运行时支柱：**记忆引擎**（召回 → 候选 → 确认）、**确认收件箱**（高风险动作门控）、**链路追踪器**（每步可审计）。

### 第二层 — 协议适配器

外部协议零代码桥接为 Tilo blocks：

| 适配器 | 状态 | 一行接入 |
|---|---|---|
| **OpenAI** | ✅ 已实现 | `from tilo.adapters.openai import tilo_spec_from_completion` |
| **Anthropic** | ✅ 已实现 | `from tilo.adapters.anthropic_sdk import tilo_spec_from_message` |
| **LangChain** | ✅ 已实现 | `from tilo.adapters.langchain import TiloCallbackHandler` |
| **MCP** | ✅ 已实现 | `from tilo.adapters.mcp import mcp_content_to_blocks` |
| **A2A** | ✅ 已实现 | `from tilo.adapters.a2a import a2a_task_to_spec` |
| **ACP** | ✅ 已实现 | `from tilo.adapters.acp import acp_message_to_spec` |
| **AG-UI** | ✅ 已实现 | `from tilo.adapters.agui import tilo_spec_to_agui_events`(互操作) |

### 第三层 — 渲染器 SDK

Tilo Spec JSON → 任何前端。`@adam2go/tilo-react` 是官方参考实现。开发者可以覆盖任何 block type 的渲染器，也可以为 Vue、Flutter、Web Components 或终端 CLI 构建自己的 SDK。

### 第四层 — Skill 提示 + LLM 动态组合

Skill 向 LLM 提供**提示**（推荐的块类型、视图组织方式）。LLM 有完全自主权决定最终的 views、blocks 和布局。Skill 是建议，不是约束。

---

## 三个内置 Demo

| 场景 | Agent 做了什么 | 模式 |
|---|---|---|
| **PR Review** 🔍 | 标注 PR 风险点，列出验证清单，用 confirmation 把控合并 | LLM |
| **SF Trip** ✈️ | 生成 3 天周末行程，含 timeline、酒店、打包清单和预算，全部可交互 | 离线 · 零配置 |
| **Sales Briefing** 📊 | 输出管线指标 + 推荐动作 + 待发送邮件草稿（confirmation 把关） | LLM |

SF Trip 视频在页面顶部。另外两个：

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🔍 PR Review</h4>

https://github.com/user-attachments/assets/3795a3a8-aedb-4996-ae18-42f7c3e2c45f

  <sub>Auth 改造 PR · diff + 验证清单 + 合并 confirmation。<b>53 秒</b> · <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-pr-review.mp4">高清下载 (42 MB)</a></sub>
    </td>
    <td width="50%" valign="top">
      <h4>📊 Sales Briefing</h4>

https://github.com/user-attachments/assets/1847718a-586d-4e80-b9fd-6eade1d35b35

  <sub>管线指标 + 推荐动作 + 把关后才发的外呼邮件。<b>68 秒</b> · <a href="https://github.com/adam2go/tilo-framework/releases/download/v0.1-demos/canvas-sales-briefing.mp4">高清下载 (36 MB)</a></sub>
    </td>
  </tr>
</table>

完整的 goal 文本与本地复现步骤见 [`docs/demos/`](./docs/demos/README.md)。

[demos-release]: https://github.com/adam2go/tilo-framework/releases/tag/v0.1-demos

---

## 双向闭环：具体长什么样

大多数 "Agent UI" 框架只做了一个方向：Agent → UI。Tilo 同时做两个方向，
**第二个方向才是杠杆所在**。

```text
1.  Agent 产出 AIP spec       →  blocks + views，声明式 JSON
2.  渲染器绘制 UI             →  React（参考实现）/ 你自己的 SDK
3.  用户点击 / 编辑 / 确认
4.  前端 → POST /api/interactions
5.  后端写入 UIInteractionEvent + ContextReflection 观察
6.  Agent 下一轮通过 AgentContextBuilder 拿到最近的事件
7.  Agent 推理的不是像素，而是用户实际做了什么。
```

两条设计原则保证安全：

- **确认式记忆，不是自动写入。** Agent 提出"我学到了什么"（`memory_card`）；
  用户决定什么留下。
- **后端拥有动作语义。** 前端只渲染意图；后端（`ArtifactActionRuntime`）
  决定实际发生什么 —— 高风险动作始终被 `confirmation` 块门控。

---

## 开发者如何集成

| 模式 | 适合场景 | 接触面 |
|---|---|---|
| **独立运行** | 本地评估 Tilo | `pip install tilo && tilo init myapp && tilo serve` |
| **OpenAI 适配器** | 使用 OpenAI SDK | `from tilo.adapters.openai import tilo_spec_from_completion` |
| **Anthropic 适配器** | 使用 Anthropic SDK | `from tilo.adapters.anthropic_sdk import tilo_spec_from_message` |
| **LangChain 适配器** | 使用 LangChain / LangGraph | `from tilo.adapters.langchain import TiloCallbackHandler` |
| **MCP 适配器** | 已在用 MCP 工具 | `from tilo.adapters.mcp import mcp_content_to_blocks` |
| **后端 sidecar** | 已有自己的前端 | 调用 Tilo REST APIs |
| **嵌入组件** | 想用 AI-native UI 块 | 复用 `@adam2go/tilo-react` 组件 + override |
| **Skill 作者** | 封装可复用工作流 | `skill.yaml` + `block_hints` + `view_hints` |
| **声明式 App** | 完整 Agent 工作流 | `app.yaml` + `interaction.policy.yaml` |

核心 API：

```text
POST /api/conversations                          创建会话
POST /api/conversations/{id}/messages             发送消息 → Task → Run
GET  /api/runs/{id}/trace                         实时链路追踪
GET  /api/artifacts?workspace_id=...&task_id=...  完整 Artifact（含 views）
POST /api/memories/{id}/confirm                   确认记忆候选
```

完整指南见 [`docs/INTEGRATION_GUIDE.md`](./docs/INTEGRATION_GUIDE.md) 和 [`docs/AIP_DESIGN.md`](./docs/AIP_DESIGN.md)。

---

## 仓库结构

```text
backend/       Python 包 `tilo` — FastAPI 运行时，pip 可安装
  tilo/adapters/   MCP、LangChain、A2A、ACP 协议适配器
  tilo/schemas/    AIP v1 spec：~20 个原语块类型 + 开放扩展
  tilo/services/   记忆、确认、追踪、Artifact、技能
frontend/      @adam2go/tilo-react — Next.js 参考 UI，Artifact 驱动的 Canvas
skills/        Skill YAML 定义（block_hints + view_hints）
examples/      声明式 Agent App 和合同 fixture
docs/          架构、AIP 设计、集成指南、设计原则
evals/         运行时质量检查和 baseline 指标
```

---

## 路线图

**v0.1（当前）**——完整工作闭环 + AIP 架构。

- [x] Task → Run → Trace → Artifact → Surface → Confirmation → Memory 完整闭环
- [x] 三个 Demo 场景（PR Review、SF Trip、Sales Briefing）
- [x] Agent 交互协议（AIP）：~20 个原语块类型
- [x] LLM 驱动的 UI 组合 + Skill 提示
- [x] MCP 适配器 —— `mcp_content_to_blocks`、`mcp_tool_result_to_spec`
- [x] LangChain 适配器 —— `TiloCallbackHandler` + `langchain_result_to_spec`
- [x] 三个声明式示例 App（合同审查、销售跟进、代码审查）
- [x] Alembic 驱动的 schema 版本化迁移
- [x] `pip install tilo` + `tilo serve` CLI
- [x] 多轮对话 + LLM streaming + 思考过程实时可见
- [x] chart、diff、timeline、kanban、code、tool_preview、memory_card 块完整渲染
- [x] 发布到 PyPI —— `pip install tilo` 已上线
- [x] OpenAI 适配器 —— `tilo_spec_from_completion()` + `TiloCompletionHandler`
- [x] Anthropic 适配器 —— `tilo_spec_from_message()` + `TiloMessageHandler`
- [ ] A2A / ACP 适配器完整实现
- [x] `@adam2go/tilo-react` npm 包已发布 —— `npm install @adam2go/tilo-react`
- [ ] Skill 市场 + YAML 技能加载

**未来**——多 Agent 路由、带确认门控的真实工具执行、Slack / 邮件渠道适配器、社区渲染器 SDK。

---

## 参与贡献

Tilo 还处于早期阶段，完全开源，欢迎参与。

贡献前请阅读：

- [`AGENTS.md`](./AGENTS.md) — 给 AI 编程 Agent 的开发规则
- [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- [`docs/AIP_DESIGN.md`](./docs/AIP_DESIGN.md) — Agent 交互协议设计

最重要的原则：

> **MCP 是 Agent 的手，Tilo 是 Agent 的脸 + 耳。
> 始终保留 AIP 闭环：目标 → Spec → 交互界面 → 观察 → 记忆。**

---

## License

MIT License
