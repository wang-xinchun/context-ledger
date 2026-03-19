# Extensibility And Upgrade Plan v1

## 1. 目标澄清
`LM Studio + Qwen32B` 只是本地验证场景，不是最终产品绑定方案。  
最终目标是一个可持续更新的 ContextLedger 平台，模型、检索、存储、策略都可独立升级。

## 2. 产品级目标场景
1. 单机本地场景：个人开发者，离线可用。
2. 团队私有化场景：公司内网部署，集中治理。
3. 云增强场景：本地优先，必要时接入云模型与外部系统。

## 3. 可更新性设计原则
1. Provider 解耦：模型供应商和业务逻辑分离。
2. 接口稳定：对外 API 版本化，内部实现可替换。
3. 数据可迁移：记忆数据有 schema 版本和迁移脚本。
4. 回滚友好：升级失败可快速回退。
5. 渐进发布：支持灰度和兼容窗口。

## 4. 插件化架构
## 4.1 Provider 抽象层
定义统一接口：
- `ChatProvider`: 生成回答
- `EmbeddingProvider`: 生成向量
- `RerankProvider`: 重排检索结果（可选）
- `StorageProvider`: 向量/文档存储

测试阶段：
- `ChatProvider=LMStudio`

生产阶段可切换：
- `ChatProvider=Ollama/OpenAI/Anthropic/LocalRuntime`

## 4.2 Adapter 注册机制
1. 每个 Provider 以 adapter 形式实现。
2. 通过配置文件注册，不改业务代码。
3. 通过能力探针暴露特性：
- 最大上下文长度
- 最大输出长度
- 是否支持流式输出
- 是否支持 function calling

## 5. 版本策略
## 5.1 API 版本
- `/v1/*` 保持稳定。
- 破坏性变更进入 `/v2/*`。
- 同时维护至少一个小版本兼容期。

## 5.2 数据版本
关键表带 `schema_version`：
- `memories`
- `snapshots`
- `sessions`
- `audit_logs`

迁移规则：
1. 启动时检查版本。
2. 自动执行向前迁移。
3. 保留回滚脚本。

## 6. 升级路径（从测试到产品）
1. Phase A：本地单机  
`LM Studio + SQLite + Local Vector Index`

2. Phase B：可插拔多模型  
引入 Provider Registry，不改上层 API。

3. Phase C：团队部署  
`Postgres + Qdrant + Redis + Worker Queue`

4. Phase D：治理增强  
灰度发布、审计报表、策略中心。

## 7. 配置驱动能力
核心配置示例：
- `chat_provider`
- `embedding_provider`
- `context_budget_policy`
- `quality_guard_policy`
- `continuation_policy`
- `storage_backend`

要求：
1. 配置变更优先，无需改代码。
2. 关键配置支持热加载或滚动重启。

## 8. 兼容矩阵
每个版本发布时提供矩阵：
1. 支持的模型 Provider 版本
2. 支持的数据库版本
3. 支持的向量引擎版本
4. 升级限制与已知问题

## 9. 发布与回滚策略
1. 发布前运行 Memory Regression Tests。
2. 新版本先灰度到 10% 会话。
3. 监控指标异常则自动回滚。
4. 回滚后保留失败证据用于修复。

关键监控指标：
- 平均首 token 延迟
- 自动续写触发率
- 半截答案率
- Resume 命中率
- 检索相关性评分

## 10. 对你当前场景的直接结论
1. 你现在继续用 `LM Studio + Qwen32B` 做验证完全正确。
2. 我们从设计上不绑定 LM Studio，后续可平滑换模型和后端。
3. 文档和代码将按“插件化 + 版本化 + 可回滚”路线推进，保证项目具备长期可更新性。
