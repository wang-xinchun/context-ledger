# ContextLedger Design v1

## 1. 文档目标
本设计用于实现个人本地场景下的“无限感上下文”体验：在 LM Studio 仅有 4096 token 上下文时，用户仍可长期连续对话，且单次回复质量稳定。

## 2. 范围与非范围
### 2.1 范围
- 本地 LLM 推理（LM Studio / Ollama）
- 对话前上下文编译（检索、裁剪、合并）
- 对话后自动记忆写入（事实/决策/待办）
- 输出质量稳定（输出预留、两阶段生成、自动续写）

### 2.2 非范围（v1 不做）
- 多用户权限系统
- 云端账号体系
- 图片/语音多模态记忆

## 3. 用户使用方式（个人本地）
1. 用户在本地启动 LM Studio，并加载 Qwen32B（或其他本地模型）。
2. 用户启动 ContextLedger 服务。
3. 用户通过 CLI/Web 与 ContextLedger 对话（而不是直接连 LM Studio）。
4. 每轮流程：
   - ContextLedger 检索历史记忆并编译上下文。
   - 调用 LM Studio 生成回复。
   - 自动写入本轮记忆与决策日志。
5. 用户在新会话输入“继续项目X”，系统自动恢复关键状态。

## 4. 系统架构
```text
User UI (CLI/Web)
   -> ContextLedger API
      -> Context Compiler
      -> Memory Store (SQLite + Vector Index)
      -> Response Orchestrator
         -> LM Studio OpenAI-compatible API
```

核心模块：
- `Session Manager`: 管理会话状态与轮次。
- `Memory Ingestor`: 将对话/文件/Git 元数据转为记忆单元。
- `Retriever`: 检索相关记忆（向量 + 规则）。
- `Retrieval Quality Gate`: 检索质量评分与纠偏。
- `Context Compiler`: 在 token 预算下组装最小必要上下文。
- `Response Orchestrator`: 两阶段生成与自动续写。
- `Quality Guard`: 输出完整性检查，不达标触发补答。

## 5. Token 预算与上下文编译
## 5.1 固定预算模板（4096 示例）
- `System Rules`: 400
- `Project Snapshot`: 700
- `Recent Turns`: 900
- `Retrieved Memories`: 1200
- `User Query`: 300
- `Output Reserve`: 596

约束：`Output Reserve` 为硬预留，不允许被输入挤占。

## 5.2 超预算降级顺序
1. 先移除低相关度检索片段。
2. 再裁剪最近对话中的旧轮次。
3. 最后压缩 Project Snapshot（保留决策与约束）。
4. 永不删除：System Rules + User Query + 最小项目状态。

## 5.3 防摘要漂移机制
- 原始日志 append-only，不覆盖。
- 每 N 轮从原始日志重建状态快照，禁止“摘要套摘要”无限链式压缩。
- 所有摘要项必须带来源引用（会话轮次、文件路径或 commit id）。

## 5.4 检索质量门控
- 对检索结果计算 `retrieval_quality_score`。
- 低于阈值时触发纠偏流程：
1. query rewrite
2. 扩大检索范围（类型过滤放宽）
3. 使用 snapshot-first 答复并提示可补充上下文

## 5.5 位置感知上下文打包
- 将最高价值证据优先放在 prompt 开头和末尾，降低“中段信息被忽略”风险。
- 中间区域放次级证据和最近轮次摘要。

## 6. 回复质量稳定机制
## 6.1 两阶段生成
阶段 A：先生成结构化骨架（结论/步骤/风险/待办）。  
阶段 B：基于骨架逐段扩写成自然语言完整回答。

目的：在输出 token 被压缩时，至少保证核心信息完整，再自动补全细节。

## 6.2 自动续写（无感拼接）
触发条件：
- 模型因上下文余额不足提前结束；
- 输出不满足最小完整性（见 6.3）。

机制：
1. 记录已生成段落边界。
2. 发起 `continue` 请求（指定从第 N 段接续）。
3. 将多段结果拼接为单条最终回复返回用户。

用户层体验：只看到一条完整答案，不感知后台续写次数。

## 6.3 质量守卫（Response QA）
每轮生成后执行检查：
- 是否回答用户主问题；
- 是否包含关键步骤；
- 是否存在明显断句/未完成段落；
- 如用户问题要求依据，是否提供依据说明。

任一失败则自动补答，最多重试 2 次。

## 6.4 质量-涨幅平衡控制器（Balance Controller）
目标：在“回复质量”与“上下文涨幅”之间动态平衡，不追求绝对不涨，而是控制增长速度并维持答案完整性。

核心指标：
- `quality_score`：回答完整性与可用性评分。
- `context_growth_ratio`：本轮输入 token / 最大上下文 token。
- `continuation_rounds`：为补全答案触发的续写轮数。

控制策略：
1. 当 `quality_score` 低于阈值：提升检索预算与输出保留，允许更高涨幅。
2. 当 `context_growth_ratio` 连续高于阈值：降低 recent turns 与次级检索片段权重。
3. 当两者都紧张：进入 `guarded mode`，先答核心结论，再后台补全细节。

运行模式：
- `quality_first`：质量优先，允许更高上下文增长。
- `balanced`：默认模式，质量与涨幅同时优化。
- `growth_first`：增长抑制优先，回答更精简。

建议默认值（4096 场景）：
- `target_quality_score >= 0.78`
- `target_context_growth_ratio <= 0.72`
- 连续 3 轮超阈值触发策略切换

## 7. 记忆模型设计
## 7.1 记忆单元类型
- `fact`: 事实
- `decision`: 决策
- `constraint`: 约束
- `todo`: 待办
- `risk`: 风险

## 7.2 最小字段
- `id`
- `project_id`
- `session_id`
- `turn_id`
- `type`
- `content`
- `source_ref`（轮次/文件/commit）
- `importance`（1-5）
- `timestamp`

## 8. API 草案（v1）
## 8.1 Chat
`POST /v1/chat`
- 入参：`project_id`, `session_id`, `message`
- 行为：自动检索 + 上下文编译 + 回复生成 + 记忆写入
- 出参：`answer`, `used_memories`, `continuations`, `quality_score`

## 8.2 Resume
`POST /v1/resume`
- 入参：`project_id`
- 出参：`project_snapshot`, `open_todos`, `recent_decisions`

## 8.3 Timeline
`GET /v1/timeline?project_id=...`
- 出参：按时间排序的决策/风险/待办变更

## 9. 本地部署方案（个人版）
## 9.1 依赖组件
- LM Studio（本地模型服务）
- ContextLedger（本项目）
- SQLite（主存储）
- 本地向量索引（FAISS 或 Qdrant 本地单机）

## 9.2 配置项
- `MODEL_BASE_URL=http://127.0.0.1:1234/v1`
- `MODEL_NAME=qwen32b`
- `MAX_CONTEXT_TOKENS=4096`
- `MIN_OUTPUT_RESERVE=900`（建议在 4096 场景中提升到 900）
- `DB_PATH=./data/memory.db`
- `VECTOR_PATH=./data/vector.index`

## 9.3 启动顺序
1. 启动 LM Studio 并确认模型可调用。
2. 启动 ContextLedger。
3. 启动异步 worker（可选但推荐）：索引/摘要后台任务。
4. 首次执行项目导入（可选）：读取 README、关键文档、Git 最近提交。
5. 开始对话。

## 10. 验收标准（v1）
1. 在连续 100 轮对话后，仍可正确恢复最近关键决策。
2. 单轮输入超预算时，不报错中断，能自动裁剪并回复。
3. 回复长度稳定，无明显“半截答案”现象。
4. 新会话可在 3 秒内给出项目恢复快照。

## 11. 风险与缓解
- 风险：检索不准导致“答非所问”。  
  缓解：混合检索（向量+关键词+类型过滤）。

- 风险：摘要偏移导致历史失真。  
  缓解：定期从原始日志重建快照，并保留引用链。

- 风险：本地资源不足导致延迟高。  
  缓解：限制检索条数与并发，提供“快速模式”。

- 风险：检索质量过低导致答案质量波动。  
  缓解：检索质量门控 + 纠偏检索 + snapshot-first 降级策略。

- 风险：文件操作越界带来安全问题。  
  缓解：项目根路径白名单、删除操作保护、审计日志。

## 12. 里程碑
1. `M1`：Chat + Memory 写入 + Resume（最小闭环）
2. `M2`：上下文编译器 + 固定预算 + 降级策略
3. `M3`：两阶段生成 + 自动续写 + 质量守卫
4. `M4`：Timeline + 稳定性测试 + 文档完善
