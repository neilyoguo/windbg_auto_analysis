---
name: windows-dump-analysis
description: Windows crash dump 深度分析 skill。支持蓝屏、系统卡死、资源耗尽、驱动问题等场景。
  通过 MCP 服务执行 WinDbg/CDB 命令，采用多轮交叉验证、证据优先、深度分析方法论。
agent_created: true
disable: false
---

# Windows Dump 深度分析 Skill

## ⚠️ 核心强制规则（硬性限制，不可违反）

**1. 严禁草草了事！** 每个 DUMP 必须完成全部必须轮次才能下结论。
**2. 严禁凭表面现象下结论！** 必须多方位交叉验证，找到直接证据。
**3. 严禁跳过 PEB 分析！** 对于进程终止类蓝屏，必须检查 PEB 中的命令行参数。
**4. 报告必须包含对外回复话术！** 这是分析交付的重要产出。
**5. 分析必须深入到调用链源头！** 不能停留在"某进程被终止"就结束。
**6. 严禁只看表面现象！** 必须检查系统级阻塞（RPC、ALPC、安全软件）。
**7. 严禁忽略第三方驱动！** 必须检查所有第三方驱动的版本和状态。
**8. 严禁场景误判！** 必须准确识别场景类型，然后执行对应的分析流程。
**9. 严禁结论无证据！** 每个结论必须有 dump 输出作为直接证据，无依据时标注"证据不足"。
**10. 严禁跳过交叉验证！** 每个发现必须通过至少 2 种方式验证。
**11. 严禁忽略置信度！** 必须评估结论的置信度（高/中/低），并说明依据。
**12. 严禁证据链断裂！** 从现象到根因的证据链必须完整，不能有断裂。

## Purpose

对 Windows 蓝屏、系统卡死、资源耗尽、驱动崩溃等问题进行企业级深度分析。核心方法论：
1. **证据优先**：每个结论必须有 dump 输出作为直接证据
2. **多轮交叉验证**：不同命令的结果相互印证，提升置信度
3. **动态调整**：根据返回信息实时决定下一步分析方向
4. **深度分析**：每个 dump 都做完整分析，不走捷径
5. **PEB 深挖**：必须检查进程环境块，获取命令行、工作目录等关键信息
6. **交付导向**：报告必须包含对外回复参考话术
7. **系统级分析**：必须检查 RPC、ALPC、安全软件等系统级组件
8. **资料辅助**：遇到不确定的问题时，优先参考本 skill 的 `references/` 指南和公开技术文档

本 skill 只执行只读分析和报告生成，禁止任何修复、变更操作。

## 参考资料（重要！）

分析过程中遇到以下情况时，必须参考本 skill 的 `references/` 指南或公开技术文档：

### 何时查阅资料

1. **命令不确定**：不确定某个 WinDbg 命令的用法或参数
2. **BugCheckCode 不熟悉**：遇到不常见的蓝屏代码，需要查找分析方法
3. **驱动/组件问题**：不确定某个驱动或系统组件的作用
4. **错误信息不理解**：dump 输出中的错误信息含义不明
5. **分析方法不确定**：不确定某个场景应该如何分析
6. **系统机制不清楚**：不了解某个系统机制（如 RPC、ALPC、DWM 等）

### 推荐资料类型

- Windows Server 文档
- 驱动程序文档
- PowerShell 文档
- Sysinternals 工具文档
- Win32 API 文档
- IIS 文档
- 调试器文档（debugger.md、debuggercmds.md）

### 检索关键词建议

| 场景 | 推荐关键词 |
|------|-----------|
| RPC 问题 | `RPC`, `remote procedure call`, `rpcexts` |
| ALPC 问题 | `ALPC`, `advanced local procedure call` |
| 蓝屏问题 | `bugcheck`, `blue screen`, `crash` |
| 驱动问题 | `driver`, `kernel module` |
| 进程问题 | `process`, `thread`, `svchost` |
| 内存问题 | `memory`, `pool`, `heap` |
| 调试命令 | `WinDbg`, `debugger`, `debug command` |

**注意**：使用英文关键词搜索效果更好！

## When To Use

- 用户提供 `.dmp` 文件路径、案例 ID、蓝屏截图、系统日志时
- 用户报告系统挂起、RDP 无响应、桌面卡死、登录冻结时
- 用户报告系统变慢、进程创建失败、资源耗尽时

## Safety Rules

- 仅做只读分析。禁止修改任何系统配置、文件、注册表。
- 必须通过 MCP 服务执行分析命令，禁止本地运行 WinDbg/CDB。
- 分析结束后必须调用 `close_windbg_dump` 释放资源。
- 所有结论必须有 dump 证据支持。无依据时标注"证据不足"。

## MCP 服务

### 连接配置

```json
{
  "mcpServers": {
    "windbg": {
      "type": "http",
      "url": "http://9.134.85.174:1203/mcp",
      "disabled": false
    }
  }
}
```

### 可用工具

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `list_windbg_dumps` | 列出 dump 文件 | `directory_path`, `recursive`, `max_depth` |
| `open_windbg_dump` | 打开并分析 dump | `dump_path`, `include_stack_trace`, `include_modules`, `include_threads` |
| `run_windbg_cmd` | 执行 WinDbg 命令 | `dump_path`, `command`/`commands`, `timeout`, `background` |
| `close_windbg_dump` | 关闭 dump 释放资源 | `dump_path` |
| `get_server_status` | 查看服务器状态和活跃会话 | `include_sessions` |
| `list_tasks` | 查看后台任务进度 | `task_id`, `include_output` |

### 工具使用要点

**1. `run_windbg_cmd` 增强参数**

- `command`：单条命令
- `commands`：多条命令批量执行，减少往返，输出按命令分隔
- `timeout`：单命令超时（秒），大 dump 的 `!analyze -v` 建议 120-300
- `background`：后台执行，立即返回 task_id，配合 `list_tasks` 查进度

**2. 批量命令执行**（推荐，减少 MCP 往返）

```
run_windbg_cmd(dump_path=..., commands=["!analyze -v", "lm", "kb"], timeout=120)
```

**3. 大 dump 超时处理**

如果 `!analyze -v` 超时，增大 timeout 重试：
```
run_windbg_cmd(dump_path=..., command="!analyze -v", timeout=300)
```

**4. 服务器状态检查**

开始分析前先检查服务状态：
```
get_server_status()
```


---

## 场景分类与识别

### 场景类型

| 场景 | BugCheckCode | 关键特征 | 用户描述关键词 |
|------|--------------|----------|----------------|
| **蓝屏（BSOD）** | 非 0x161 | 系统崩溃，自动生成 dump | 蓝屏、重启、bugcheck |
| **系统卡死** | 0x161 | 系统无响应，手动抓取 dump | 卡死、黑屏、无响应、RDP 断开 |
| **系统 Hang** | 0x161 | 系统完全冻结，无法操作 | hang、死机、完全无响应 |
| **进程终止蓝屏** | 0xEF、0xF4 | 关键进程被终止 | 进程被杀、关键服务停止 |
| **资源耗尽** | 无 | 系统变慢，进程创建失败 | 变慢、卡顿、内存不足 |
| **驱动问题** | 各种 | 驱动崩溃，设备异常 | 驱动错误、设备故障 |
| **启动问题** | 各种 | 无法启动，卡在启动 | 启动失败、黑屏、蓝屏 |

### 场景识别流程

**第 0 步：识别场景类型（不计入轮次）**

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",    # 获取 BugCheckCode
    "vertarget",      # 系统版本和运行时间
    "lm"              # 加载的模块列表
])
```

**场景判断规则**：
1. **BugCheckCode = 0x161**：系统卡死或 Hang（手动抓取的 dump）
2. **BugCheckCode = 0xEF/0xF4**：进程终止蓝屏
3. **BugCheckCode 其他非零值**：蓝屏（BSOD）
4. **用户描述包含"变慢""卡顿"**：资源耗尽
5. **用户描述包含"启动""开机"**：启动问题

**记录用户提到的所有可疑进程/驱动/软件**（后续必须搜索）

---

## 分析流程（分层架构）

### 架构说明

```
第 0 步：场景识别
    ↓
第 1 层：基础分析（所有场景必须执行）
    ↓
第 2 层：场景特定分析（根据场景类型选择）
    ↓
第 3 层：深度验证（交叉验证 + 根因定位）
    ↓
第 4 层：结论与报告
```

### 深度分析要求

**⚠️ 以下要求必须严格遵守，违反即为分析失败！**

#### 1. 多轮分析（不能草草了事）

- **最少轮次**：每个场景必须完成全部必须轮次
- **动态调整**：根据发现动态增加分析轮次
- **深度挖掘**：每个发现都要深挖到底，不能停留在表面

#### 2. 交叉验证（确保准确度）

**每个发现必须通过至少 2 种方式验证**：

| 发现类型 | 验证方式 |
|----------|----------|
| 进程阻塞 | `!process 7` + `!thread` + 调用栈 |
| 锁等待 | `!locks` + `!thread` + 等待对象 |
| RPC 阻塞 | `!rpc` + `!alpc /l` + 线程状态 |
| 驱动问题 | `lmvm` + `!drvobj` + 调用栈 |
| 资源耗尽 | `!vm` + `!memusage` + `!poolused` |
| 安全软件 | `lmvm` + 版本检查 + 兼容性验证 |

#### 3. 证据链完整性（不能有断裂）

**证据链格式**：
```
用户现象
  -> [第一层：直接表现]（必须有命令输出支持）
  -> [第二层：根本原因]（必须有命令输出支持）
  -> [第三层：底层细节]（必须有命令输出支持）
  -> 结果
```

**证据链检查**：
- [ ] 每一层是否有命令输出作为证据？
- [ ] 证据之间是否相互印证？
- [ ] 是否有断裂或跳跃？
- [ ] 是否有遗漏的关键环节？

#### 4. 置信度评估（必须明确）

**置信度标准**：
- **高**：有直接证据支持（命令输出、具体数据），且经过交叉验证
- **中**：有间接证据或合理推测，部分验证
- **低**：只有推测，缺乏证据，未充分验证

**置信度评估要求**：
- [ ] 结论置信度是多少？
- [ ] 置信度的依据是什么？
- [ ] 是否有提升置信度的方法？
- [ ] 是否需要更多验证？

#### 5. 根因定位（必须深入）

**根因定位要求**：
- [ ] 是否找到了最底层的根因？
- [ ] 是否还有更深层的原因？
- [ ] 根因是否经过交叉验证？
- [ ] 根因是否与用户描述一致？

**常见根因层次**：
```
表面现象（如 DWM 卡死）
  -> 直接原因（如图形命令提交阻塞）
    -> 根本原因（如 RPC 被卡满）
      -> 底层原因（如 SysmonDrv 版本过旧）
```

#### 6. 反向验证（必须执行）

**反向验证要求**：
- [ ] 如果根因是 X，那么应该看到什么现象？
- [ ] 实际看到的现象是否与预期一致？
- [ ] 是否有其他可能的解释？
- [ ] 如何排除其他解释？

---

## 分析流程（分层架构）

### 架构说明

```
第 0 步：场景识别
    ↓
第 1 层：基础分析（所有场景必须执行）
    ↓
第 2 层：场景特定分析（根据场景类型选择）
    ↓
第 3 层：深度验证（交叉验证 + 根因定位）
    ↓
第 4 层：结论与报告
```

---

## 第 1 层：基础分析（所有场景必须执行）

**目标**：获取系统基本信息，为后续分析奠定基础

### 第 1 轮：基线信息收集

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "vertarget",
    "lm",
    "!process 0 0"
])
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？是真实蓝屏还是 hang dump？
- [ ] `Probably caused by` 指向哪个模块？
- [ ] 符号是否正常加载？
- [ ] 系统版本和架构？
- [ ] 系统运行了多长时间？
- [ ] **有哪些第三方驱动加载？**（从 `lm` 输出中识别）
- [ ] **有哪些进程在运行？**（从 `!process 0 0` 输出中识别）

**输出**：场景类型确认，第三方驱动清单，进程清单

### 第 2 轮：系统状态全景扫描

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!running -it",      # CPU 状态
    "!locks",            # 锁状态
    "!vm",               # 虚拟内存状态
    "!memusage",         # 内存使用情况
    "!poolused /t 20"    # 池使用情况
])
```

**必须回答的问题**：
- [ ] CPU 状态如何？哪些 CPU 忙碌？
- [ ] 锁状态如何？有多少锁被持有？
- [ ] 内存状态如何？是否有资源耗尽？
- [ ] 池使用情况如何？是否有泄漏？

**输出**：系统资源状态，异常点列表

### 第 3 轮：系统级阻塞分析

**⚠️ 这是最重要的轮次之一！不能跳过！**

**⚠️ 重要规则：必须检查所有第三方驱动的版本，不能只检查常见的！**

**步骤 1：从 `lm` 输出中识别所有第三方驱动**

在第 1 轮中，我们已经执行了 `lm` 命令。现在需要从输出中识别所有非微软驱动：
- 驱动路径包含 `D:\tools\`、`C:\Program Files\` 等非系统路径的
- 驱动名称包含 `Sysmon`、`Sbie`、`CrowdStrike`、`CarbonBlack`、`Cylance`、`SentinelOne` 等安全/监控软件关键词的
- 驱动时间戳明显过旧的（超过 1 年）

**步骤 2：检查所有识别出的第三方驱动版本**

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!alpc /l",                # ALPC 端口列表
    # 以下是常见的安全软件驱动（必须检查）
    "lmvm SysmonDrv",          # Sysmon 驱动版本
    "lmvm WdFilter",           # Windows Defender 驱动版本
    "lmvm SbieDrv",            # Sandboxie 驱动版本
    "lmvm CrowdStrike",        # CrowdStrike 驱动版本
    "lmvm CarbonBlack",        # Carbon Black 驱动版本
    "lmvm Cylance",            # Cylance 驱动版本
    "lmvm SentinelOne",        # SentinelOne 驱动版本
    "lmvm Sophos",             # Sophos 驱动版本
    "lmvm McAfee",             # McAfee 驱动版本
    "lmvm Norton",             # Norton 驱动版本
    "lmvm Kaspersky",          # Kaspersky 驱动版本
    # 以下是虚拟化相关驱动（必须检查）
    "lmvm viostor",            # VirtIO 存储驱动
    "lmvm netkvm",             # VirtIO 网络驱动
    "lmvm balloon",            # VirtIO 内存驱动
    "lmvm LdVBoxDrv",          # 雷电模拟器驱动
    # 以下是其他常见第三方驱动
    "lmvm npf",                # WinPcap/Npcap
    "lmvm tap0901",            # TAP 驱动
    "lmvm vmci",               # VMware 驱动
    "lmvm vmhgfs"              # VMware 共享文件夹驱动
])
```

**步骤 3：对于第 1 轮中发现的其他第三方驱动，也需要检查版本**

如果第 1 轮的 `lm` 输出中发现了其他非微软驱动，必须在本轮检查其版本。

**⚠️ RPC 分析注意事项**：
- `!rpc` 命令在内核态调试器中**不可用**
- rpcexts 扩展的命令（`!rpcexts.getthreadinfo`、`!rpcexts.getcallinfo` 等）**只能在用户态调试器中使用**
- 对于内核态 dump，需要通过**替代方法**间接分析 RPC 状态：
  1. 查看 svchost.exe 进程状态：`!process 0 0 svchost.exe`
  2. 查看 ALPC 端口状态：`!alpc /l`、`!alpc /p <端口>`
  3. 查看线程等待状态：`!thread <线程地址>`
  4. 查看锁状态：`!locks`

**必须回答的问题**：
- [ ] **ALPC 端口状态如何？是否有异常？**
- [ ] **哪些安全软件/监控软件加载了驱动？**
- [ ] **这些驱动的版本是什么？是否过旧？**
- [ ] **这些驱动是否与当前系统版本兼容？**
- [ ] **svchost.exe 进程状态是否异常？**（间接判断 RPC 状态）
- [ ] **是否有其他第三方驱动版本过旧？**

**关键检查点**：
1. **SysmonDrv.sys**：版本时间超过 1 年视为过旧
2. **WdFilter.sys**：Windows Defender 驱动，检查版本
3. **其他安全软件驱动**：检查版本和兼容性
4. **虚拟化驱动**：VirtIO、VMware、VirtualBox 等
5. **ALPC 端口**：检查是否有异常的端口或消息队列
6. **svchost.exe**：检查进程状态和线程等待情况

**版本过旧判定标准**：
- 超过 **1 年**：视为过旧，需要关注
- 超过 **3 年**：视为严重过旧，可能是根因
- 超过 **5 年**：视为极度过旧，极有可能是根因

**输出**：系统级阻塞分析结果，所有第三方驱动版本清单（标注是否过旧）

---

## 第 2 层：场景特定分析（根据场景类型选择）

### 场景 A：蓝屏（BSOD）分析

**适用场景**：BugCheckCode 非 0x161、0xEF、0xF4

#### 第 4 轮：蓝屏详细分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    ".bugcheck",              # BugCheck 详细信息
    "!thread",                # 当前线程
    "!process",               # 当前进程
    "kv",                     # 调用栈
    "lmvm <可疑驱动>"         # 可疑驱动版本
])
```

**必须回答的问题**：
- [ ] BugCheckCode 的具体含义是什么？
- [ ] `Probably caused by` 指向哪个驱动？
- [ ] 调用栈是什么？是否有异常？
- [ ] 可疑驱动的版本是什么？

#### 第 5 轮：驱动深入分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!drvobj <可疑驱动> 7",   # 驱动对象详情
    "!irp <IRP地址>",         # IRP 详情（如果有）
    "!devstack <设备地址>"    # 设备栈（如果有）
])
```

**必须回答的问题**：
- [ ] 驱动对象的详细信息是什么？
- [ ] IRP 的状态是什么？
- [ ] 设备栈是否有异常？

---

### 场景 B：系统卡死/Hang 分析

**适用场景**：BugCheckCode = 0x161，用户描述"卡死""黑屏""无响应"

#### 第 4 轮：卡死深入分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <关键进程> 7",    # 关键进程详情（dwm.exe、csrss.exe 等）
    "!thread <关键线程>",       # 关键线程详情
    "!alpc /p <端口地址>"       # ALPC 端口详情（如果有异常）
])
```

**必须回答的问题**：
- [ ] 关键进程（dwm.exe、csrss.exe、winlogon.exe）的状态是什么？
- [ ] 关键线程在等待什么？等待了多久？
- [ ] ALPC 端口是否有异常？
- [ ] **是否有 RPC 相关的等待？**

#### 第 5 轮：可疑进程搜索

**⚠️ 用户提到的所有可疑进程都必须搜索！**

```
# 搜索用户提到的可疑进程
run_windbg_cmd(dump_path=<path>, commands=[
    "!process 0 0 <可疑进程1>",
    "!process 0 0 <可疑进程2>",
    "!process 0 0 <可疑进程3>",
    # ... 用户提到的所有进程都必须搜索
])

# 如果找到可疑进程，分析其线程
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <可疑进程地址> 7"
])
```

**必须回答的问题**：
- [ ] **用户提到的可疑进程是否存在？**
- [ ] **如果存在，它们的线程状态是什么？**
- [ ] **它们是否与系统卡死有关？**
- [ ] **它们的调用栈是什么？**

---

### 场景 C：进程终止蓝屏分析

**适用场景**：BugCheckCode = 0xEF（CRITICAL_PROCESS_DIED）或 0xF4（CRITICAL_OBJECT_TERMINATION）

#### 第 4 轮：进程终止分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    ".bugcheck",
    "!thread",
    "!process",
    "kv"
])
```

**必须回答的问题**：
- [ ] 哪个进程被终止了？
- [ ] 终止的原因是什么？
- [ ] 调用栈是什么？

#### 第 5 轮：PEB 深度分析（强制！）

**⚠️ 进程终止蓝屏必须执行此轮分析！**

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!peb",                           # 当前进程 PEB
    "!process <终止进程> 1",          # 获取终止进程详情
    "!process <被终止进程> 1",        # 获取被终止进程详情
    "db <ImageBaseAddress> L100"      # 检查进程映像
])
```

**必须回答的问题**：
- [ ] 终止进程的命令行参数是什么？（taskkill /F /IM xxx？）
- [ ] 终止进程的工作目录是什么？
- [ ] 终止进程是从哪个会话启动的？（Console/RDP？）
- [ ] 终止进程的父进程是谁？
- [ ] 是否有自动化脚本的痕迹？

**关键字段**：
- `CommandLine` - 完整命令行参数
- `CurrentDirectory` - 工作目录
- `SessionName` - 会话名称
- `WindowTitle` - 窗口标题
- `Environment` - 环境变量

**输出**：操作来源判定（人为/脚本/工具）

---

### 场景 D：资源耗尽分析

**适用场景**：用户描述"变慢""卡顿""内存不足"，无蓝屏

#### 第 4 轮：资源耗尽详细分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!vm",                       # 虚拟内存详情
    "!memusage",                 # 内存使用详情
    "!poolused /t 50",           # 池使用详情（Top 50）
    "!handle 0 0",               # 句柄使用情况
    "!process 0 0"               # 所有进程
])
```

**必须回答的问题**：
- [ ] 内存使用情况如何？是否有泄漏？
- [ ] 池使用情况如何？哪个池泄漏了？
- [ ] 句柄使用情况如何？是否有泄漏？
- [ ] 哪些进程占用了大量资源？

#### 第 5 轮：泄漏进程分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <可疑进程> 7",     # 可疑进程详情
    "!handle 0 0 <可疑进程>",   # 可疑进程句柄
    "!poolused /t 20 <可疑进程>" # 可疑进程池使用
])
```

**必须回答的问题**：
- [ ] 可疑进程的资源使用情况如何？
- [ ] 可疑进程是否有泄漏？
- [ ] 泄漏的类型是什么？（内存、句柄、池）

---

### 场景 E：驱动问题分析

**适用场景**：BugCheckCode 指向特定驱动，用户描述"驱动错误""设备故障"

#### 第 4 轮：驱动详细分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <可疑驱动>",           # 驱动版本详情
    "!drvobj <可疑驱动> 7",      # 驱动对象详情
    "!irp <IRP地址>",            # IRP 详情（如果有）
    "!devstack <设备地址>"       # 设备栈（如果有）
])
```

**必须回答的问题**：
- [ ] 驱动的版本是什么？是否过旧？
- [ ] 驱动对象的详细信息是什么？
- [ ] IRP 的状态是什么？
- [ ] 设备栈是否有异常？

#### 第 5 轮：驱动调用栈分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "dps <调用栈地址> L<长度>",  # 扫描调用栈
    "!drvobj <父驱动> 7",       # 父驱动详情
    "!devobj <设备对象>"        # 设备对象详情
])
```

**必须回答的问题**：
- [ ] 调用栈的详细内容是什么？
- [ ] 父驱动是否有问题？
- [ ] 设备对象的状态是什么？

---

### 场景 F：启动问题分析

**适用场景**：用户描述"启动失败""开机黑屏""卡在启动"

#### 第 4 轮：启动问题详细分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <启动驱动>",           # 启动驱动版本
    "!drvobj <启动驱动> 7",      # 启动驱动对象详情
    "!devstack <启动设备>"       # 启动设备栈
])
```

**必须回答的问题**：
- [ ] 启动驱动的版本是什么？
- [ ] 启动驱动对象的详细信息是什么？
- [ ] 启动设备栈是否有异常？

---

## 第 3 层：深度验证（所有场景必须执行）

### 第 6 轮：交叉验证与根因定位

**目标**：多方位验证前面轮次的发现，排除误判

**验证维度**：

| 验证类型 | 命令 | 目的 |
|----------|------|------|
| 锁验证 | `!locks` + `!thread` | 锁持有者与等待者是否匹配 |
| ALPC 验证 | `!alpc /p <port>` | ALPC 端口状态与消息队列 |
| RPC 验证 | `!rpc` + 端点分析 | RPC 线程池状态 |
| 驱动验证 | `lmvm <driver>` | 可疑驱动版本和时间戳 |
| 内存验证 | `!poolused` + `!vm` | 内存/句柄泄漏检测 |
| 安全软件验证 | `lmvm <安全软件驱动>` | 安全软件版本和兼容性 |
| 进程验证 | `!process 7` + `!thread` | 进程/线程状态验证 |
| 调用栈验证 | `dps <stack> L<length>` | 调用栈完整性验证 |

**必须执行的验证命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!alpc /l",
    "!rpc",
    "lmvm <可疑驱动>",
    "!handle 0 0 <关键进程>",
    "!process <关键进程> 1",
    "dps <关键线程栈> L<长度>"
])
```

**必须回答的问题**：
- [ ] 前面轮次的发现是否有其他证据支持？
- [ ] 是否存在多个可能的根因？如何排除？
- [ ] 驱动/组件是否有已知问题？
- [ ] 等待链的源头在哪里？
- [ ] **安全软件是否是根因？**
- [ ] **调用栈是否支持结论？**
- [ ] **是否有其他可能的解释？**

**反向验证**：
- [ ] 如果根因是 X，那么应该看到什么现象？
- [ ] 实际看到的现象是否与预期一致？
- [ ] 是否有其他可能的解释？
- [ ] 如何排除其他解释？

**输出**：根因假设置信度评估（高/中/低）

### 第 6.5 轮：资料检索验证（可选但推荐）

**目标**：使用公开技术文档或本 skill 的 `references/` 指南验证分析结果，获取参考资料

**何时执行**：
- 遇到不确定的驱动或组件
- 不确定某个 BugCheckCode 的分析方法
- 需要查找已知问题或解决方案
- 命令执行结果不理解

**推荐搜索关键词**：
- 驱动名称：`SysmonDrv`, `WdFilter`, `SbieDrv` 等
- BugCheckCode：`0x0000007E`, `0x000000EF` 等
- 系统组件：`RPC`, `ALPC`, `DWM`, `csrss` 等
- 问题现象：`hang`, `crash`, `blue screen` 等

**输出**：参考资料，验证分析结果

### 第 7 轮：最终确认与证据链整理

**目标**：确认根因，整理完整证据链

**必执行命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <根因进程> 1",  # 确认进程详情
    "dps <stack> L<length>",  # 扫描栈内容
    "!drvobj <driver> 7",     # 驱动对象详情
    "!vm",                    # 内存状态确认
    "!locks"                  # 锁状态确认
])
```

**必须回答的问题**：
- [ ] 证据链是否完整？有无断裂？
- [ ] 结论置信度是多少？依据是什么？
- [ ] 是否有遗漏的分析维度？
- [ ] 修复建议是否可操作？
- [ ] **是否需要微软支持？**
- [ ] **证据链的每一层是否有命令输出支持？**
- [ ] **证据之间是否相互印证？**

**证据链完整性检查**：
```
用户现象
  -> [第一层：直接表现]（必须有命令输出支持）
    -> 命令输出：...
  -> [第二层：根本原因]（必须有命令输出支持）
    -> 命令输出：...
  -> [第三层：底层细节]（必须有命令输出支持）
    -> 命令输出：...
  -> 结果
```

**置信度评估**：
- [ ] 结论置信度是多少？（高/中/低）
- [ ] 置信度的依据是什么？
- [ ] 是否有提升置信度的方法？
- [ ] 是否需要更多验证？

**输出**：最终结论 + 证据链 + 修复建议 + 置信度评估

### 第 8 轮（可选）：深度挖掘

**目标**：如果前面轮次发现异常，继续深挖

**触发条件**：
- 发现可疑驱动但版本正常
- 发现可疑进程但状态正常
- 发现资源耗尽但原因不明
- 发现锁等待但对象不明

**必执行命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!drvobj <可疑驱动> 7",     # 驱动对象详情
    "!devobj <设备对象>",       # 设备对象详情
    "!irp <IRP地址>",           # IRP 详情
    "!devstack <设备对象>",     # 设备栈详情
    "dps <调用栈> L<长度>"      # 调用栈详情
])
```

**必须回答的问题**：
- [ ] 可疑驱动的详细信息是什么？
- [ ] 设备对象的状态是什么？
- [ ] IRP 的状态是什么？
- [ ] 设备栈是否有异常？
- [ ] 调用栈的详细内容是什么？

**输出**：深度挖掘结果，可能的新发现

---

## 第 4 层：结论与报告

### ⚠️ 核心原则：不预设结论，从事实出发

**严禁**：
- 带着"微软说是 X"的预设去验证
- 只罗列发现，不串联因果
- 跳过链路还原，直接给结论

**必须**：
- 从 dump 事实出发
- 还原完整的卡死/崩溃链路
- 用"谁做了什么→导致什么→影响什么→最终怎样"的逻辑串联

### 卡死链路还原模板

对于卡死/Hang 场景，必须还原完整的因果链路：

```
【现象层】用户看到什么
  - RDP 黑屏 / VNC 无响应 / Ctrl+Alt+Delete 无效
  
【直接原因层】系统中发生了什么
  - 哪个进程/线程卡住了？卡在哪里？
  - 调用栈是什么？
  
【根本原因层】为什么会卡住
  - 是什么导致了这个卡住？
  - 是驱动问题？资源耗尽？锁竞争？RPC 阻塞？
  
【影响源层】是谁/什么导致的根本原因
  - 哪个软件/驱动在做什么操作？
  - 这个操作为什么会导致问题？
  - 版本是否过旧？是否与系统不兼容？
  
【结论】完整链路
  - XX软件/驱动 → 做了XX操作 → 导致XX问题 → 影响XX组件 → 最终导致XX现象
```

### 卡死链路还原示例

```
【现象层】
  用户 RDP 登录黑屏，VNC 无响应，Ctrl+Alt+Delete 无效

【直接原因层】
  dwm.exe 线程 0498 卡在 dxgkrnl!DxgkSubmitCommand（图形命令提交）
  调用栈：dxgkrnl!DxgkSubmitCommand -> dxgmms2!VidSchSubmitCommand

【根本原因层】
  DWM 作为桌面合成核心进程，图形命令提交卡住导致整个桌面子系统无响应
  但图形驱动（dxgkrnl/dxgmms2）版本正常，说明不是图形驱动本身的问题
  问题在于：是什么阻塞了图形命令提交的路径？

【影响源层】
  系统中存在多个严重过旧的内核过滤器驱动：
  - LegacyFilter.sys（2019年，7年前）- 第三方安全工具的系统监控驱动
  - SysmonDrv.sys（2021年，5年前）- Sysmon 系统监控驱动
  - SbieDrv.sys（2022年，4年前）- Sandboxie 沙箱驱动
  
  这些驱动作为内核过滤器，会拦截系统调用
  版本过旧可能导致与当前系统版本不兼容，在拦截系统调用时出现异常

【结论】
  第三方安全软件驱动版本过旧
  → 在内核层拦截系统调用时出现异常
  → 异常可能导致系统级阻塞（RPC/ALPC/锁等）
  → DWM 无法完成图形命令提交
  → 桌面无法更新，RDP/VNC 黑屏
```

### 置信度标准

- **高**：有直接证据支持（命令输出、具体数据），且经过交叉验证
- **中**：有间接证据或合理推测，部分验证
- **低**：只有推测，缺乏证据，未充分验证

### 报告格式

必须使用 PDF 格式输出，包含：
1. **场景类型**（蓝屏/卡死/Hang/进程终止/资源耗尽/驱动问题/启动问题）
2. **结论级别**（直接卡点、受影响线程、底层路径、最可能诱因）
3. **关键证据**（命令输出摘录 + 分析）
4. **证据链图**
5. **最终结论**（按置信度排序的嫌疑列表）
6. **修复建议**（仅建议，不执行）
7. **关联资料**
8. **分析轮次记录**（每轮做了什么、发现什么）
9. **对外回复参考话术**（必须包含！简洁版 + 详细版 + 交接版）

### 对外回复话术要求（必须包含）

报告中必须包含以下三种话术：

**话术一：简洁版**（用于直接回复用户）
- 一句话说明问题原因
- 一句话说明是否为系统缺陷
- 一句话给出建议

**话术二：详细版**（用于正式回复）
- 问题信息（代码、时间、系统版本）
- 根因分析（详细技术说明）
- 结论（是否为系统缺陷）
- 建议（后续处理建议）

**话术三：交接版**（用于问题交接）
- 案例编号
- 问题类型
- BugCheckCode（如果有）
- 根因
- 结论
- 处理建议
- DUMP 文件
- 分析要点

---

## 场景速查表

| 场景 | 关键特征 | 必执行命令 |
|------|----------|-----------|
| **蓝屏** | BugCheckCode 非 0x161 | `!analyze -v`, `.bugcheck`, `kv`, `lmvm`, `!drvobj` |
| **进程终止蓝屏** | **0xEF, 0xF4** | **`!peb`, `!process <pid> 1`, `db <ImageBase> L100`** |
| **系统卡死** | 0x161, CPU idle | `!running -it`, `!locks`, `!vm`, `!process 0 0`, **`!rpc`, `!alpc /l`, `lmvm SysmonDrv`** |
| **系统 Hang** | 0x161, 完全无响应 | 同系统卡死，重点检查死锁 |
| **资源耗尽** | 系统变慢, 进程创建失败 | `!vm`, `!memusage`, `!poolused`, `!process 0 0`, `!handle` |
| **驱动问题** | 驱动崩溃, 设备异常 | `lmvm`, `!drvobj`, `!irp`, `!devstack` |
| **启动问题** | 无法启动, 卡在启动 | `!analyze -v`, `lmvm <boot_driver>`, `!devstack` |
| **网络问题** | 网络异常, 连接失败 | `lmvm tcpip`, `lmvm ndis`, `lmvm netkvm` |
| **存储问题** | 磁盘异常, IO 错误 | `lmvm storport`, `lmvm disk`, `lmvm viostor` |
| **应用崩溃** | 应用闪退, 访问违规 | `!process <pid> 7`, `!thread`, `.exr` |

## 深度验证速查表

| 验证类型 | 命令 | 目的 | 必须执行场景 |
|----------|------|------|--------------|
| **RPC 验证** | `!rpc` | RPC 线程池状态 | 卡死、Hang |
| **ALPC 验证** | `!alpc /l` | ALPC 端口状态 | 卡死、Hang |
| **安全软件验证** | `lmvm SysmonDrv` 等 | 安全软件版本 | 所有场景 |
| **锁验证** | `!locks` + `!thread` | 锁状态验证 | 卡死、Hang、资源耗尽 |
| **内存验证** | `!vm` + `!memusage` | 内存状态验证 | 资源耗尽、蓝屏 |
| **驱动验证** | `lmvm` + `!drvobj` | 驱动版本验证 | 驱动问题、蓝屏 |
| **进程验证** | `!process 7` + `!thread` | 进程状态验证 | 所有场景 |
| **调用栈验证** | `dps <stack> L<length>` | 调用栈验证 | 所有场景 |

## 常见 BugCheckCode

| 代码 | 名称 | 常见原因 | 必执行额外命令 |
|------|------|----------|----------------|
| 0x0000007E | SYSTEM_THREAD_EXCEPTION_NOT_HANDLED | 驱动 bug, 系统文件损坏 | `lmvm`, `!drvobj` |
| 0x0000007B | INACCESSIBLE_BOOT_DEVICE | 存储驱动, 磁盘故障 | `lmvm storport`, `!devstack` |
| 0x0000000A | IRQL_NOT_LESS_OR_EQUAL | 驱动访问无效内存 | `!irp`, `lmvm` |
| 0x00000050 | PAGE_FAULT_IN_NONPAGED_AREA | 内存错误, 驱动 bug | `!poolused`, `!vm` |
| 0x000000D1 | DRIVER_IRQL_NOT_LESS_OR_EQUAL | 驱动 bug, 硬件故障 | `lmvm`, `!drvobj` |
| **0x000000EF** | **CRITICAL_PROCESS_DIED** | **关键进程被终止** | **`!peb`, `!process <pid> 1`** |
| **0x000000F4** | **CRITICAL_OBJECT_TERMINATION** | **关键进程崩溃/被杀** | **`!peb`, `!process <pid> 1`** |
| 0x161 | LIVE_SYSTEM_DUMP | 在线 dump, 非真实蓝屏 | **`!rpc`, `!alpc /l`, `lmvm SysmonDrv`** |

## 关键词提取（用于资料检索）

从 dump 分析结果中提取：
- BugCheckCode（如 `0x0000007E`）
- BugCheck 名称（如 `PAGE_FAULT_IN_NONPAGED_AREA`）
- 关键模块名（如 `nvlddmkm.sys`, `storport.sys`）
- 调用栈中的函数名
- 用户描述的现象词

## 报告模板

参考 `references/report-template.md`，必须包含：
1. 结论级别（直接卡点、受影响线程、底层路径、最可能诱因）
2. 关键证据（命令输出摘录 + 分析）
3. 证据链图
4. 最终结论（按置信度排序的嫌疑列表）
5. 修复建议（仅建议，不执行）
6. 关联资料

## 详细场景指南

**⚠️ 必须阅读以下参考资料后再开始分析！**

- **完整场景指南**：`references/analysis-scenarios.md`（覆盖所有场景的详细分析方法）
- 系统 Hang 深度分析：`references/hang-scenarios.md`

### 参考资料内容

`references/analysis-scenarios.md` 包含：
1. **9 种场景的详细分析流程**（蓝屏、卡死、Hang、进程终止、资源耗尽、驱动问题、启动问题、网络问题、存储问题）
2. **每种场景的必须执行命令**
3. **每种场景必须回答的问题**
4. **常见 BugCheckCode 的详细分析方法**（0x7E、0x7B、0x0A、0x50、0xD1、0xEF、0xF4、0x161）
5. **10 个常见分析陷阱**
6. **WinDbg 命令速查表**

---

## ⚠️ 常见分析陷阱（必须避免）

### 陷阱 1：只看表面现象
**错误**：看到 DWM 卡在图形命令提交，就认为是图形驱动问题
**正确**：必须深挖为什么图形命令会卡住（可能是 RPC 被卡满、安全软件阻塞等）

### 陷阱 2：忽略安全软件
**错误**：看到 SysmonDrv 但不检查版本
**正确**：必须检查所有安全软件驱动的版本，版本超过 1 年视为过旧

### 陷阱 3：不检查 RPC
**错误**：不执行 `!rpc` 命令
**正确**：卡死场景必须检查 RPC 线程池状态

### 陷阱 4：不搜索可疑进程
**错误**：用户提到 win-Agent-install.exe 但不搜索
**正确**：用户提到的所有可疑进程都必须搜索

### 陷阱 5：分析流程不完整
**错误**：只分析 1-2 轮就下结论
**正确**：必须完成全部必须轮次才能下结论

### 陷阱 6：场景误判
**错误**：把蓝屏当卡死分析
**正确**：必须准确识别场景类型，然后执行对应的分析流程

### 陷阱 7：忽略调用栈
**错误**：只看 BugCheckCode 就下结论
**正确**：必须分析完整调用栈，找到根因

### 陷阱 8：不检查驱动版本
**错误**：只看驱动名称，不检查版本
**正确**：必须检查所有第三方驱动的版本，版本过旧可能是根因

### 陷阱 9：不检查 ALPC
**错误**：不执行 `!alpc /l` 命令
**正确**：卡死场景必须检查 ALPC 端口状态

### 陷阱 10：不检查系统级阻塞
**错误**：只关注进程和线程，不检查系统级阻塞
**正确**：必须检查 RPC、ALPC、安全软件等系统级组件

### 陷阱 11：结论无证据
**错误**：给出结论但没有命令输出支持
**正确**：每个结论必须有 dump 输出作为直接证据

### 陷阱 12：不进行交叉验证
**错误**：只通过一种方式验证就下结论
**正确**：每个发现必须通过至少 2 种方式验证

### 陷阱 13：忽略置信度评估
**错误**：不评估结论的置信度
**正确**：必须评估结论的置信度（高/中/低），并说明依据

### 陷阱 14：证据链断裂
**错误**：从现象到根因的证据链有断裂
**正确**：证据链必须完整，每一层都要有命令输出支持

### 陷阱 15：不进行反向验证
**错误**：不验证结论是否与现象一致
**正确**：必须进行反向验证，确保结论与现象一致

---

## PDF 生成方法

使用 Python fpdf2 库直接生成 PDF（已验证可用，比 reportlab 更稳定）。

**前置条件**：
```bash
# 确保 fpdf2 已安装（必须）
pip install fpdf2
```

**⚠️ 运行环境注意事项**：
- 当前环境 Bash 工具可能因 PortableGit 缺失而不可用
- **优先使用 Agent 工具执行 Python 脚本**（subagent_type: general-purpose）
- 备选：PowerShell 中执行 `python generate_report.py`
- Python 路径优先级：系统 python > managed python

**生成脚本模板**（已验证可用的 v2 版本）：
创建 `generate_report.py` 文件：

```python
# -*- coding: utf-8 -*-
from fpdf import FPDF
import os
from datetime import datetime

class PDF(FPDF):
    def header(self):
        self.set_font('SimHei', '', 14)
        self.cell(0, 10, 'Windows DUMP 分析报告', new_x="LMARGIN", new_y="NEXT", align='C')
        self.set_font('SimSun', '', 10)
        self.cell(0, 8, f'案例编号：{self.case_id}', new_x="LMARGIN", new_y="NEXT", align='C')
        self.ln(5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('SimSun', '', 8)
        self.cell(0, 10, f'技术支持 | 报告生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")} | 第 {self.page_no()}/{{nb}} 页', new_x="LMARGIN", new_y="NEXT", align='C')

    def section_title(self, title):
        self.set_font('SimHei', '', 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def sub_title(self, title):
        self.set_font('SimHei', '', 10)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        # ⚠️ 关键：必须检查 text 是否为空，否则空内容会导致 PDF 空白
        if text:
            self.set_font('SimSun', '', 9)
            self.multi_cell(0, 5, text)
            self.ln(2)

def generate_report(case_id, sections, output_file):
    """
    生成 PDF 分析报告

    Args:
        case_id: 案例编号
        sections: 报告内容字典（key=标题, value=内容）
        output_file: 输出文件路径
    """
    pdf = PDF()
    pdf.case_id = case_id
    pdf.alias_nb_pages()

    # 添加中文字体
    pdf.add_font('SimHei', '', r'C:\Windows\Fonts\simhei.ttf')
    pdf.add_font('SimSun', '', r'C:\Windows\Fonts\simsun.ttc')

    pdf.add_page()

    # 按 sections 字典生成内容
    for section_name, content in sections.items():
        if section_name.startswith('##'):
            pdf.section_title(section_name.replace('## ', ''))
        elif section_name.startswith('###'):
            pdf.sub_title(section_name.replace('### ', ''))

        # ⚠️ 关键：无论标题类型如何，都要输出内容（body_text 已处理空字符串）
        pdf.body_text(content)

    pdf.output(output_file)
    print(f'PDF 已生成：{output_file}')

# ========== 报告内容 ==========
# sections 格式：{ "标题": "内容" }
# - "## X.Y" 开头 → 一级标题（灰色背景）
# - "### X.Y" 开头 → 二级标题
# - 内容为空字符串时，只输出标题不输出内容
sections = {
    "## 1. 场景类型": "蓝屏/卡死/Hang/进程终止/资源耗尽/驱动问题/启动问题",

    "## 2. 结论级别": "直接卡点：...\n受影响线程：...\n底层路径：...\n最可能诱因：...",

    "## 3. 关键证据": "",

    "### 3.1 系统基本信息": "• 操作系统：...\n• 系统运行时间：...\n• 处理器数量：...",

    # ... 更多章节 ...

    "## 9. 对外回复参考话术": "",

    "### 话术一：简洁版（用于直接回复客户）": "您好，经过分析...",
}

# 生成报告
generate_report("案例编号", sections, "输出文件名.pdf")
```

**sections 字典格式说明**：
- key 为标题，value 为内容
- `##` 开头的 key → 渲染为一级标题（灰色背景填充）
- `###` 开头的 key → 渲染为二级标题
- **value 为空字符串 `""` 时**：只输出标题，不输出内容（用于章节分组标题）
- **value 非空时**：先输出标题，再输出内容
- `\n` 在内容中表示换行

**运行方法**（优先级从高到低）：
```bash
# 方法1：使用 Agent 工具执行（推荐，最稳定）
# 在 Agent prompt 中说明：运行 Python 脚本生成 PDF

# 方法2：Bash 工具（如果可用）
python generate_report.py

# 方法3：PowerShell
python.exe generate_report.py
```

**注意**：
- 中文字体路径：`C:\Windows\Fonts\simsun.ttc`（宋体）、`C:\Windows\Fonts\simhei.ttf`（黑体）
- 确保输出目录有写入权限
- **sections 字典中不要用 set（集合），必须用 dict（字典）**
- **body_text 必须处理空字符串，否则 PDF 会空白**
