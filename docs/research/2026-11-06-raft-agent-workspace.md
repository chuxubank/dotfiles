# Raft：人和多 agent 的协作工作区

**调研日期：** 2026-11-06

**对象：** Botiverse 的 [Raft](https://raft.build/)，不是分布式一致性算法或检索增强微调。

**方法：** 阅读官网、官方产品与开发者文档、公开源码镜像 README 和许可证、隐私政策与服务条款。Context7 未检索到这个产品，返回的是同名一致性算法库，因此直接采用一手资料。未安装、登录、连接本机或运行 agent；下文区分文档事实与评估建议。

## 结论

Raft 不是新的 agent 推理循环，而是已有 agent 运行时之上的**团队协作层**：把人、agent、频道、线程、任务、工具接入和运行状态放到同一个工作区。官网明确将其与 Claude Code、Codex、OpenClaw 等运行时区分开。[1][2]

**判断：** 如果痛点是多人、多机器、长期角色之间反复转述上下文，值得试用；如果只是自己同时操作几个编码会话，它会增加一套聊天入口、任务状态和服务依赖，不一定比现有工作流划算。这个判断来自其产品边界，不是性能实测。

## 工作方式

```text
人 / agent
    │ 频道、线程、DM、任务
    ▼
Raft 协作服务
    ├── Raft Computer ── 本机运行时 ── 文件、命令、模型服务
    └── 外部 agent ───── CLI / SDK ── 自己管理的运行环境
```

这里的 **Server 是团队工作区**，不是接入的那台物理服务器。Computer 才是执行 agent 的机器；可以接入多台机器，每个受管 agent 在一台机器上运行，同一工作区可以混用运行时。[2][3]

### 受管 agent 与外部 agent

| 路径 | 谁负责运行 | 适合什么情况 | 边界 |
|---|---|---|---|
| Raft Computer | 本机后台服务启动和管理 agent | 希望直接在 Raft 中分派、查看、重启 agent | 机器离线时执行暂停，恢复后接收积压消息 |
| External agent | 用户自己的进程 / 框架 | 已有 Hermes、OpenClaw 或自定义 agent | 接入仍标为实验性；Raft 不负责重启或重置，提醒功能也有差异 |

上述区别由官方 Computers 与 External agents 文档定义。[3][4]

Pi 是受支持的运行时之一；文档还区分自行安装的 Pi 和随 Computer 提供的 Built-in Pi。**支持 Pi 不代表已经验证会完整继承当前机器的扩展、MCP、认证和 provider 配置**；这些应在接入测试中单独确认。[3]

## 真正有用的机制

### 持久身份与显式记忆

每个 agent 有独立身份、职责描述、频道成员关系和本机 workspace。持久记忆依赖 workspace 中的 `MEMORY.md`，通常还有 `notes/`；上下文窗口不是永久记忆，未写入笔记的内容可能在重置或新会话后丢失。运行时自身读取的项目文件与 Raft 记忆是不同层。[5][6]

因此，“团队记得以前发生过什么”依靠**笔记、可检索会话与交接行为**，不应理解为所有 agent 自动共享一份完整上下文。[5][6]

### 消息触发与长期角色

受管 agent 会因所在频道的新消息、DM、提及、关注线程回复或自己的提醒被唤醒。官方建议给 agent 清晰的职责范围，把公共工作留在频道并按线程组织，让负责该领域的 agent 接手。[5][7]

**评估：** 这适合长期维护文档、跟进问题、定期研究、跨角色审阅。职责不清或让太多 agent 订阅嘈杂频道，可能增加无效阅读、往返讨论与模型消耗；这是需要测试的风险，不是已测量的成本结论。

### 任务领取与人类验收

任务和原消息、讨论线程关联。Claim 会设置负责人并开始任务，已被领取的任务不能再被另一成员领取；拆分工作要创建独立任务。完成工作与验收是显式状态变更，不会仅凭对话自动结束。[8]

**重要边界：** 任务独占不等于 Git 或文件系统隔离。不能据此推断 Raft 会自动阻止两个不同任务修改同一文件；独立 worktree、分支、CI 和合并门禁仍应保留，直到实际验证有等价机制。

### 自带运行时与订阅

Raft 可以使用接入机器已有的运行时和模型订阅，而不是要求全部改用一个内置模型。机器休眠会暂停其 agent；需要持续运行时，可以接入常在线机器。[1][3]

这不会消除模型费用、订阅配额或服务条款。Raft 自身计划与模型提供方收费是不同层；使用者对模型和第三方服务的合规使用负责。[3][9][15]

## 开发与 bot 接入

官方提供 CLI 和类型化 SDK，而不是仅有聊天 UI。SDK 分为程序层 `createRaftClient` 与面向模型的 agent 层 `createRaftAgent`：前者适合通知、CI、feed bot，后者提供身份、收件箱、任务、消息及模型可读的后续操作提示。导入与接口应以 SDK 文档为准，不在这里维护代码快照。[10]

外部接入的协议有几个值得注意的设计：[10][11]

- **持久 inbox 是消息事实来源**；轮询、wake hint 和 webhook 只负责通知“有东西要读”。
- **游标确认与读取分离**；进程崩溃后可能重读，业务处理必须幂等。
- webhook 提供签名验证；不能把收到通知当作已经处理完消息。
- 新消息可能让发送或任务变更返回中断结果，交给模型重新判断，而不是盲目继续旧决定。
- 外部 agent 的状态需要自身或适配器上报，不能把 Online 圆点当作任务健康证明。

**判断：** 真正接入自有 bot 时，主要工作不在“能否发送一条消息”，而在唤醒、确认、重试、幂等、状态和权限的完整闭环。SDK 仍在稳定化过程中，接入时应跟随其版本与迁移规则。[10][11]

## 数据与权限：不是“全都留在本机”

本地执行并不等于协作服务看不到内容。服务条款区分了以下数据：[15]

- 本机处理的原始命令输出和文件内容，条款称其保留在本机。
- 人或 agent 发到 Raft 的消息、附件、任务和其他工作区记录，由服务存储和处理。
- 后台服务上传的活动信息包括工具名、截断的工具输入、agent 的 thinking 和文本输出。

**含义：** 即使原始文件没有自动整体上传，工具输入、thinking、文本回复和附件仍可能包含敏感信息，不能把活动日志视为无敏感内容的纯运行指标。

官方还说明，agent 的创建者及工作区 owner/admin 可以在机器在线时浏览其 workspace 文件。不要把 agent 的记忆目录视为只对本机用户可见。[5]

MCP Apps 的调用由 Raft 代理，认证信息保留在 Raft，agent 不直接看到密钥；该入口要求公开可达的远程 MCP 服务，并不等价于直接接入当前机器的私有 stdio MCP。文档还说明添加 MCP App 后应检查各 agent 的访问授权，不能假设默认最小权限。[12]

隐私政策明确：连接的 Google 数据可能存储在 Raft，并为完成请求而共享给所用模型服务。服务条款声明托管服务位于美国。敏感项目接入前需确认组织政策、数据区域、保留与删除要求。[14][15]

以上是政策和文档声明，不是独立安全审计；本次没有验证执行沙箱、任意宿主文件访问边界、命令审批覆盖率或数据导出完整性。

## 源码与自托管

公开的 `botiverse/raft-source` 不只有 SDK，还包含服务端、Web、CLI、daemon、Computer 和共享库。README 提供了启动本地开发栈的路径。[13]

但它是 **source-available，不应简单称为宽松开源**：许可证为 FSL，包含竞争性用途限制，每个版本在未来转换为 Apache 许可；具体许可范围以 LICENSE 为准。公共仓库是从私有开发库导出的发行镜像，目前不接收外部 PR。[13][16]

**判断：** 能启动开发栈不等于已有受支持的生产自托管方案。官方把私有部署和 SSO 放在 Enterprise 联系路径，部署、升级、备份和授权支持应另行询问，不能由 README 推断。[9][13]

## 费用怎么评估

不要只比较 agent 数量。总成本包括：Raft 计划、模型订阅或 API、常在线机器，以及跨 agent 阅读和交接造成的额外消耗。计划属于工作区，付费按人和 agent 折算席位；历史可见性、文件和迁移能力也随计划变化。具体价格和限制统一看官方计划页，不在笔记复制易过期数字。[1][9]

试用时应记录：完成同一项工作的模型消耗、人工介入次数、误唤醒与重复劳动、交接成功率、离线恢复情况，以及任务完成证据是否可追溯。这些比“创建了多少个 agent”更能说明收益。

## 对现有 agent 工作流的建议

以下是试用方案，不是已完成的操作：

1. 先用非敏感仓库，不接密码库、生产密钥或高权限业务工具。
2. 以“实现 → 独立审阅 → 人工验收”测试一个真实小任务，每个角色有明确责任范围。
3. 保留现有 worktree、CI 和合并流程，让 Raft 负责协调，而不是成为新的代码事实来源。
4. 检查 Pi 的认证、provider、扩展和工具实际加载情况，避免把 Built-in Pi 当成当前配置的复制品。
5. 验证消息插入、断网重连、会话重置后的记忆恢复、重复事件和拒绝越权行为。
6. 把模型消耗与人工交接成本同现有做法比较，再决定是否迁移更多日常工作。

**采用门槛：** 确实减少人工转述，仍能保留清晰验收和权限边界。若只是把终端会话换成群聊，而管理成本更高，就没有必要迁移。

## 类似产品：按工作组织方式选择

以下是同次调研的候选列表，来自官方文档与 README，不是安装或效果实测。比较的是工作组织方式，不能据此认为各产品的权限、隔离或可靠性等价。

| 产品 | 与 Raft 相似之处 | 主要区别与试用方向 |
|---|---|---|
| [OpenAgents Workspace](https://openagents.org/docs/en/workspace/what-is-workspace) | 人和 agent 共用线程、文件、知识库与任务板，支持本地 agent 接入 | 最接近共享团队工作区的体验；文档另列工作流、定时任务与共享浏览器，适合优先比较协作入口 |
| [Multica](https://github.com/multica-ai/multica) | 复用现有 agent CLI，在用户控制的机器执行，人和 agent 共用项目与任务 | 以 issue 为中心，关联执行记录、讨论与交付，偏软件工程；README 列有 Pi 与 OMP，适合评估接入现有工具链 |
| [Paperclip](https://github.com/paperclipai/paperclip) | 管理多个不同运行时的 agent、任务、历史和人类审批 | 更偏组织控制台：目标、汇报关系、预算、审批、定时执行；README 列有 Pi，普通聊天与外部聊天连接器仍有实验性标记 |
| [Clawith](https://github.com/dataelement/Clawith) | agent 有长期身份、记忆和 workspace，可以沟通、委派并和人一起工作 | 更偏平台内数字员工体系，带组织知识动态和自主触发；需要外部模型 API，不应假定能像 Raft 一样原样驱动现有 Pi 配置 |

许可也需分别判断：[Paperclip LICENSE](https://github.com/paperclipai/paperclip/blob/master/LICENSE) 为 MIT；[Clawith LICENSE](https://github.com/dataelement/Clawith/blob/main/LICENSE) 为 Apache 2.0；[Multica LICENSE](https://github.com/multica-ai/multica/blob/main/LICENSE) 虽包含 Apache 文本，但附加了对外托管、商业嵌入等条件，应按其自定义许可理解，不能标成纯 Apache。OpenAgents 官方 Workspace 文档提供自托管路径；具体组件许可需在选定部署版本后核对，不能用网站的开源表述覆盖所有组件。

**建议顺序：** 要类似 Raft 的共享协作体验，先看 OpenAgents；要接入当前编码 CLI、围绕 issue 交付，先看 Multica；要组织、预算与审批，先看 Paperclip；要自托管的长期数字员工与业务工具接入，再看 Clawith。此顺序是场景适配判断，不是成熟度排名。

终端工作区、多 agent 编码控制台是相邻类别：它们主要解决会话、worktree 和代码审阅组织问题，不应仅因为能启动多个 agent 就当作 Raft 的直接替代。LangGraph、AutoGen、CrewAI 等底层构建框架也不在这份成品工作区清单中。

## 一手来源

1. [官网与 FAQ](https://raft.build/)
2. [Welcome：产品概念](https://docs.raft.build/welcome/)
3. [Computers：执行机器与运行时](https://docs.raft.build/features/server/computers/)
4. [External agents](https://docs.raft.build/features/agents/external/)
5. [Agents：触发与记忆](https://docs.raft.build/features/agents/)
6. [Agent-readable manual：运行时与项目文件边界](https://docs.raft.build/features/agents.md)
7. [Close the loop：自主工作方式](https://docs.raft.build/close-the-loop/)
8. [Tasks](https://docs.raft.build/features/collaboration/tasks/)
9. [Plans and billing](https://docs.raft.build/features/server/plans/)
10. [Raft SDK](https://docs.raft.build/developers/sdk/)
11. [Wake-ups, inbox acknowledgement, and status](https://docs.raft.build/developers/sdk/external-agents/wake-and-status/)
12. [MCP Apps](https://docs.raft.build/features/apps/mcp/)
13. [raft-source README](https://github.com/botiverse/raft-source/blob/main/README.md)
14. [Privacy Policy](https://raft.build/privacy/)
15. [Terms of Service，尤其 Agents and your computers](https://raft.build/terms/)
16. [raft-source LICENSE](https://github.com/botiverse/raft-source/blob/main/LICENSE)
