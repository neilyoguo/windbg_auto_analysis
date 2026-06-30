# Windows Dump 分析场景完整指南

## 概述

本指南覆盖所有主要分析场景，提供详细的分析方法和必须执行的命令。每个场景使用 MCP 的 `commands` 参数批量执行命令，减少往返，提高分析效率。

## 分析原则

1. **先批量后单条**：用 `commands` 一次执行多条命令，减少 MCP 往返
2. **先宏观后微观**：先看整体状态（`!analyze -v`, `!vm`），再看具体细节
3. **交叉验证**：不同命令的结果必须相互印证
4. **证据优先**：每个结论必须有命令输出作为直接证据
5. **超时处理**：大 dump 用 `timeout=120-300`，避免误判为失败
6. **多轮分析**：每个场景必须完成全部必须轮次，不能草草了事

---

## 场景分类

| 场景 | BugCheckCode | 关键特征 | 用户描述关键词 |
|------|--------------|----------|----------------|
| **蓝屏（BSOD）** | 非 0x161 | 系统崩溃，自动生成 dump | 蓝屏、重启、bugcheck |
| **系统卡死** | 0x161 | 系统无响应，手动抓取 dump | 卡死、黑屏、无响应、RDP 断开 |
| **系统 Hang** | 0x161 | 系统完全冻结，无法操作 | hang、死机、完全无响应 |
| **进程终止蓝屏** | 0xEF、0xF4 | 关键进程被终止 | 进程被杀、关键服务停止 |
| **资源耗尽** | 无 | 系统变慢，进程创建失败 | 变慢、卡顿、内存不足 |
| **驱动问题** | 各种 | 驱动崩溃，设备异常 | 驱动错误、设备故障 |
| **启动问题** | 各种 | 无法启动，卡在启动 | 启动失败、黑屏、蓝屏 |
| **网络问题** | 各种 | 网络异常，连接失败 | 网络断开、连接超时 |
| **存储问题** | 各种 | 磁盘异常，IO 错误 | 磁盘错误、IO 超时 |

---

## 场景 1：蓝屏（BSOD）

### 场景特征
- BugCheckCode 非 0x161
- 系统自动生成 dump 文件
- 通常由驱动 bug、硬件故障、系统文件损坏引起

### 第 1 轮：基线信息收集

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "vertarget",
    "lm",
    "kv"
], timeout=120)
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？具体含义是什么？
- [ ] `Probably caused by` 指向哪个模块？
- [ ] 符号是否正常加载？
- [ ] 系统版本和架构？
- [ ] 系统运行了多长时间？
- [ ] 调用栈是什么？是否有异常？
- [ ] **有哪些第三方驱动加载？**

### 第 2 轮：崩溃线程分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!thread",
    "!process",
    "!process 0 0"
])
```

**必须回答的问题**：
- [ ] 崩溃线程的状态是什么？
- [ ] 崩溃进程是什么？
- [ ] 有哪些进程在运行？
- [ ] 是否有异常进程？

### 第 3 轮：可疑驱动分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <可疑驱动>",
    "!drvobj <可疑驱动> 7"
])
```

**必须回答的问题**：
- [ ] 可疑驱动的版本是什么？是否过旧？
- [ ] 驱动对象的详细信息是什么？
- [ ] 驱动是否有已知问题？

### 第 4 轮：系统级检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!vm",
    "!locks",
    "!running -it"
])
```

**必须回答的问题**：
- [ ] 内存状态如何？是否有资源耗尽？
- [ ] 锁状态如何？是否有死锁？
- [ ] CPU 状态如何？哪些 CPU 忙碌？

### 第 5 轮：安全软件检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm SysmonDrv",
    "lmvm WdFilter",
    "lmvm SbieDrv",
    "lmvm CrowdStrike",
    "lmvm CarbonBlack",
    "lmvm Cylance",
    "lmvm SentinelOne",
    "lmvm Sophos",
    "lmvm McAfee",
    "lmvm Norton",
    "lmvm Kaspersky"
])
```

**必须回答的问题**：
- [ ] 哪些安全软件驱动加载了？
- [ ] 这些驱动的版本是什么？是否过旧？
- [ ] 这些驱动是否与当前系统版本兼容？

### 交叉验证
- `!analyze -v` 的 `Probably caused by` 是否与 `kv` 调用栈一致？
- `lmvm` 显示的驱动版本是否为已知问题版本？
- `.bugcheck` 参数与 `!analyze -v` 是否匹配？

---

## 场景 2：系统卡死（Hang）

### 场景特征
- BugCheckCode = 0x161（LIVE_SYSTEM_DUMP）
- 系统无响应，手动抓取 dump
- 通常由 RPC 卡满、安全软件阻塞、驱动死锁引起

### 第 1 轮：基线信息收集

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "vertarget",
    "lm",
    "!process 0 0"
], timeout=120)
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？（应该是 0x161）
- [ ] 系统版本和架构？
- [ ] 系统运行了多长时间？
- [ ] **有哪些第三方驱动加载？**
- [ ] **有哪些进程在运行？**

### 第 2 轮：系统状态全景扫描

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!running -it",
    "!locks",
    "!vm",
    "!memusage",
    "!poolused /t 20"
])
```

**必须回答的问题**：
- [ ] CPU 状态如何？哪些 CPU 忙碌？
- [ ] 锁状态如何？有多少锁被持有？
- [ ] 内存状态如何？是否有资源耗尽？
- [ ] 池使用情况如何？是否有泄漏？

### 第 3 轮：系统级阻塞分析

**⚠️ 这是最重要的轮次之一！不能跳过！**

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!rpc",
    "!alpc /l",
    "lmvm SysmonDrv",
    "lmvm WdFilter",
    "lmvm SbieDrv",
    "lmvm CrowdStrike",
    "lmvm CarbonBlack",
    "lmvm Cylance",
    "lmvm SentinelOne",
    "lmvm Sophos",
    "lmvm McAfee",
    "lmvm Norton",
    "lmvm Kaspersky"
])
```

**必须回答的问题**：
- [ ] **RPC 线程池状态如何？是否被卡满？**
- [ ] **ALPC 端口状态如何？是否有异常？**
- [ ] **哪些安全软件/监控软件加载了驱动？**
- [ ] **这些驱动的版本是什么？是否过旧？**
- [ ] **这些驱动是否与当前系统版本兼容？**

### 第 4 轮：关键进程分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <dwm.exe> 7",
    "!process <csrss.exe> 7",
    "!process <winlogon.exe> 7",
    "!process <svchost.exe> 7"
])
```

**必须回答的问题**：
- [ ] 关键进程（dwm.exe、csrss.exe、winlogon.exe）的状态是什么？
- [ ] 关键线程在等待什么？等待了多久？
- [ ] **是否有 RPC 相关的等待？**
- [ ] **是否有 ALPC 相关的等待？**

### 第 5 轮：可疑进程搜索

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

### 第 6 轮：ALPC/RPC 深入分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!alpc /p <端口地址>",
    "!alpc /m <消息地址>"
])
```

**必须回答的问题**：
- [ ] ALPC 端口的详细信息是什么？
- [ ] ALPC 消息的状态是什么？
- [ ] 是否有 RPC 相关的阻塞？

### 第 7 轮：驱动版本检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <所有第三方驱动>",
    "!drvobj <可疑驱动> 7"
])
```

**必须回答的问题**：
- [ ] 所有第三方驱动的版本是什么？
- [ ] 是否有过旧的驱动？
- [ ] 驱动对象的详细信息是什么？

### 交叉验证
- `!locks` 的 owner 与 `!thread` 的等待类型是否一致？
- `!process 7` 的线程状态与 `~* kvn` 是否匹配？
- `!vm` 的内存压力与进程数量是否关联？
- **RPC 线程池状态与 ALPC 端口状态是否一致？**

### 关键分析点
- **ALPC/RPC 阻塞**：线程等待 `WrLpcReply`/`WrLpcReceive`？svchost 托管哪些服务？
- **进程泄漏**：同一进程名 > 10 实例？总数 > 200？
- **资源耗尽**：可用内存 < 10%？句柄 > 10000？
- **安全软件冲突**：多个安全驱动同时加载？

---

## 场景 3：系统 Hang（完全冻结）

### 场景特征
- BugCheckCode = 0x161（LIVE_SYSTEM_DUMP）
- 系统完全冻结，无法操作
- 通常由内核态死锁、驱动死锁、硬件故障引起

### 分析流程

与场景 2（系统卡死）相同，但重点关注：

**额外关注点**：
1. **内核态死锁**：检查 `!locks` 中是否有循环等待
2. **驱动死锁**：检查驱动调用栈中是否有锁等待
3. **硬件故障**：检查是否有硬件相关的错误

### 额外命令

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!deadlock",              # 死锁检测（如果可用）
    "!irql",                  # IRQL 检查
    "!pcr",                   # 处理器控制区域
    "!prcb"                   # 处理器控制块
])
```

---

## 场景 4：进程终止蓝屏

### 场景特征
- BugCheckCode = 0xEF（CRITICAL_PROCESS_DIED）或 0xF4（CRITICAL_OBJECT_TERMINATION）
- 关键进程被终止
- 通常由进程崩溃、被杀、资源耗尽引起

### 第 1 轮：基线信息收集

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "vertarget",
    "lm",
    "kv"
], timeout=120)
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？（0xEF 或 0xF4）
- [ ] `Probably caused by` 指向哪个模块？
- [ ] 系统版本和架构？
- [ ] 系统运行了多长时间？
- [ ] 调用栈是什么？

### 第 2 轮：进程终止分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!thread",
    "!process",
    "!process 0 0"
])
```

**必须回答的问题**：
- [ ] 哪个进程被终止了？
- [ ] 终止的原因是什么？
- [ ] 有哪些进程在运行？

### 第 3 轮：PEB 深度分析（强制！）

**⚠️ 进程终止蓝屏必须执行此轮分析！**

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!peb",
    "!process <终止进程> 1",
    "!process <被终止进程> 1",
    "db <ImageBaseAddress> L100"
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

### 第 4 轮：系统级检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!vm",
    "!locks",
    "!rpc",
    "!alpc /l"
])
```

**必须回答的问题**：
- [ ] 内存状态如何？是否有资源耗尽？
- [ ] 锁状态如何？是否有死锁？
- [ ] RPC 线程池状态如何？
- [ ] ALPC 端口状态如何？

### 第 5 轮：安全软件检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm SysmonDrv",
    "lmvm WdFilter",
    "lmvm SbieDrv"
])
```

**必须回答的问题**：
- [ ] 哪些安全软件驱动加载了？
- [ ] 这些驱动的版本是什么？是否过旧？
- [ ] 这些驱动是否与当前系统版本兼容？

---

## 场景 5：资源耗尽

### 场景特征
- 系统变慢，进程创建失败
- 通常由内存泄漏、句柄泄漏、线程泄漏引起

### 第 1 轮：资源概览

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!vm",
    "!memusage",
    "!poolused /t 20",
    "!process 0 0"
])
```

**必须回答的问题**：
- [ ] 内存使用情况如何？是否有泄漏？
- [ ] 池使用情况如何？哪个池泄漏了？
- [ ] 句柄使用情况如何？是否有泄漏？
- [ ] 哪些进程占用了大量资源？

### 第 2 轮：泄漏定位

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!handle",
    "!process <可疑进程> 7",
    "!poolused /t 50"
])
```

**必须回答的问题**：
- [ ] 可疑进程的资源使用情况如何？
- [ ] 可疑进程是否有泄漏？
- [ ] 泄漏的类型是什么？（内存、句柄、池）

### 第 3 轮：系统级检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!locks",
    "!running -it",
    "!rpc",
    "!alpc /l"
])
```

**必须回答的问题**：
- [ ] 锁状态如何？是否有死锁？
- [ ] CPU 状态如何？哪些 CPU 忙碌？
- [ ] RPC 线程池状态如何？
- [ ] ALPC 端口状态如何？

### 第 4 轮：安全软件检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm SysmonDrv",
    "lmvm WdFilter",
    "lmvm SbieDrv"
])
```

**必须回答的问题**：
- [ ] 哪些安全软件驱动加载了？
- [ ] 这些驱动的版本是什么？是否过旧？
- [ ] 这些驱动是否与当前系统版本兼容？

### 交叉验证
- `!vm` 的可用内存与 `!process 0 0` 的进程数是否关联？
- `!poolused` 中哪个 pool 类型消耗最多？
- `!handle` 中哪个进程持有最多句柄？

---

## 场景 6：驱动问题

### 场景特征
- BugCheckCode 指向特定驱动
- 驱动崩溃，设备异常
- 通常由驱动 bug、版本过旧、硬件故障引起

### 第 1 轮：驱动信息

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "lm",
    "lmvm <可疑驱动>",
    "!drvobj <可疑驱动> 7"
])
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？
- [ ] `Probably caused by` 指向哪个驱动？
- [ ] 可疑驱动的版本是什么？是否过旧？
- [ ] 驱动对象的详细信息是什么？

### 第 2 轮：驱动行为分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!devobj <设备对象>",
    "!irp <IRP地址>",
    "!devstack <设备对象>"
])
```

**必须回答的问题**：
- [ ] 设备对象的详细信息是什么？
- [ ] IRP 的状态是什么？
- [ ] 设备栈是否有异常？

### 第 3 轮：调用栈分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "dps <调用栈地址> L<长度>",
    "!drvobj <父驱动> 7"
])
```

**必须回答的问题**：
- [ ] 调用栈的详细内容是什么？
- [ ] 父驱动是否有问题？
- [ ] 是否有已知的驱动问题？

### 第 4 轮：系统级检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!vm",
    "!locks",
    "!running -it"
])
```

**必须回答的问题**：
- [ ] 内存状态如何？
- [ ] 锁状态如何？
- [ ] CPU 状态如何？

### 交叉验证
- `lmvm` 的版本信息与 `!drvobj` 的驱动行为是否一致？
- `!irp` 的 IRP 类型与设备栈路径是否匹配？

---

## 场景 7：启动问题

### 场景特征
- 无法启动，卡在启动阶段
- 通常由启动驱动失败、磁盘故障、注册表损坏引起

### 第 1 轮：启动信息

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "vertarget",
    "lm"
], timeout=120)
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？
- [ ] 系统版本和架构？
- [ ] 有哪些驱动加载？

### 第 2 轮：启动驱动分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <启动驱动>",
    "!drvobj <启动驱动> 7",
    "!devstack <磁盘设备>"
])
```

**必须回答的问题**：
- [ ] 启动驱动的版本是什么？
- [ ] 启动驱动对象的详细信息是什么？
- [ ] 启动设备栈是否有异常？

### 第 3 轮：磁盘检查

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!devobj <磁盘设备>",
    "!irp <IRP地址>",
    "!drvobj <磁盘驱动> 7"
])
```

**必须回答的问题**：
- [ ] 磁盘设备的详细信息是什么？
- [ ] IRP 的状态是什么？
- [ ] 磁盘驱动是否有问题？

---

## 场景 8：网络问题

### 场景特征
- 网络异常，连接失败
- 通常由网络驱动 bug、防火墙阻塞、资源耗尽引起

### 第 1 轮：网络状态

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "lm",
    "lmvm tcpip",
    "lmvm ndis",
    "lmvm netkvm"
])
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？
- [ ] 网络相关驱动的版本是什么？
- [ ] 是否有网络相关的错误？

### 第 2 轮：网络驱动分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!drvobj <网络驱动> 7",
    "!devobj <网络设备>",
    "!irp <IRP地址>"
])
```

**必须回答的问题**：
- [ ] 网络驱动的详细信息是什么？
- [ ] 网络设备的详细信息是什么？
- [ ] IRP 的状态是什么？

---

## 场景 9：存储问题

### 场景特征
- 磁盘异常，IO 错误
- 通常由存储驱动 bug、磁盘故障、资源耗尽引起

### 第 1 轮：存储状态

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "lm",
    "lmvm storport",
    "lmvm disk",
    "lmvm viostor"
])
```

**必须回答的问题**：
- [ ] BugCheckCode 是什么？
- [ ] 存储相关驱动的版本是什么？
- [ ] 是否有存储相关的错误？

### 第 2 轮：存储驱动分析

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!drvobj <存储驱动> 7",
    "!devobj <存储设备>",
    "!irp <IRP地址>",
    "!devstack <存储设备>"
])
```

**必须回答的问题**：
- [ ] 存储驱动的详细信息是什么？
- [ ] 存储设备的详细信息是什么？
- [ ] IRP 的状态是什么？
- [ ] 设备栈是否有异常？

---

## 常见 BugCheckCode 详细分析

### 0x0000007E - SYSTEM_THREAD_EXCEPTION_NOT_HANDLED

**常见原因**：
- 驱动 bug
- 系统文件损坏
- 硬件故障

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "kv",
    "lmvm <可疑驱动>",
    "!drvobj <可疑驱动> 7"
])
```

### 0x0000007B - INACCESSIBLE_BOOT_DEVICE

**常见原因**：
- 存储驱动问题
- 磁盘故障
- 注册表损坏

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "lmvm storport",
    "lmvm disk",
    "!devstack <磁盘设备>"
])
```

### 0x0000000A - IRQL_NOT_LESS_OR_EQUAL

**常见原因**：
- 驱动访问无效内存
- 驱动 bug
- 硬件故障

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "kv",
    "lmvm <可疑驱动>",
    "!irql"
])
```

### 0x00000050 - PAGE_FAULT_IN_NONPAGED_AREA

**常见原因**：
- 内存错误
- 驱动 bug
- 硬件故障

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "kv",
    "!vm",
    "!poolused /t 20"
])
```

### 0x000000D1 - DRIVER_IRQL_NOT_LESS_OR_EQUAL

**常见原因**：
- 驱动 bug
- 硬件故障

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "kv",
    "lmvm <可疑驱动>",
    "!drvobj <可疑驱动> 7"
])
```

### 0x000000EF - CRITICAL_PROCESS_DIED

**常见原因**：
- 关键进程被终止
- 进程崩溃
- 资源耗尽

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "!peb",
    "!process <终止进程> 1"
])
```

### 0x000000F4 - CRITICAL_OBJECT_TERMINATION

**常见原因**：
- 关键进程崩溃/被杀
- 资源耗尽
- 驱动 bug

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    ".bugcheck",
    "!peb",
    "!process <终止进程> 1"
])
```

### 0x161 - LIVE_SYSTEM_DUMP

**常见原因**：
- 系统卡死/Hang
- 手动抓取的 dump

**必须执行的命令**：
```
run_windbg_cmd(dump_path=<path>, commands=[
    "!analyze -v",
    "!running -it",
    "!locks",
    "!vm",
    "!rpc",
    "!alpc /l",
    "lmvm SysmonDrv",
    "lmvm WdFilter"
])
```

---

## 常见分析陷阱

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

---

## RPC 调试扩展命令 (RpcExts.dll)

**⚠️ 重要限制：这些命令只能在用户模式 WinDbg 或 CDB 中运行，不能在内核态调试器 (kd) 中使用！**

### rpcexts 扩展命令列表

| 命令 | 描述 |
|------|------|
| `!rpcexts.help` | 显示所有 Rpcexts.dll 扩展命令的帮助文本 |
| `!rpcexts.eeinfo <EEInfoAddress>` | 显示扩展错误信息链 |
| `!rpcexts.eerecord <Address>` | 显示单个扩展错误信息记录 |
| `!rpcexts.getcallinfo` | 搜索系统 RPC 状态信息，显示服务器端调用 (SCALL) 信息 |
| `!rpcexts.getclientcallinfo` | 搜索系统 RPC 状态信息，显示客户端调用 (CCALL) 信息 |
| `!rpcexts.getdbgcell <PID> <CellID>` | 获取指定 RPC 单元格的详细信息 |
| `!rpcexts.getendpointinfo [EndpointName]` | 显示 RPC 端点信息（可指定端点编号） |
| `!rpcexts.getthreadinfo <PID> [ThreadID]` | 显示 RPC 线程信息 |
| `!rpcexts.rpcreadstack <ThreadStackPointer>` | 读取 RPC 客户端堆栈，检索调用信息 |
| `!rpcexts.rpctime` | 显示当前 RPC 时间（用于计算调用耗时） |
| `!rpcexts.thread <TEB>` | 显示指定线程的 RPC 信息（包括扩展错误信息地址） |

### rpcexts 扩展模式切换

```
!rpcexts.mode rpcrt4    # 切换到 rpcrt4 模式（默认）
!rpcexts.mode msrpc     # 切换到 msrpc 模式
!rpcexts.mode rhttpaa   # 切换到 rhttpaa 模式
```

### 卡住调用 (Stuck Call) 排查流程

**场景**：RPC 调用卡住，需要定位问题

**步骤 1：获取线程堆栈指针**
```
!rpcexts.rpcreadstack 0x68fba0
```
查看输出中的 `Status` 字段：
- `Status: Dispatched` - 调用已离开 RPC 运行时
- `Status: Pending` - 调用仍在等待

**步骤 2：获取当前 RPC 时间**
```
!rpcexts.rpctime
```
比较当前时间与最后更新时间，判断调用是否卡住。

**步骤 3：获取调用信息**
```
!rpcexts.getcallinfo <PID>
```
查看 `Servicing thread identifier` 字段，确定服务线程。

**步骤 4：获取线程信息**
```
!rpcexts.getthreadinfo <PID> <ThreadID>
```
进一步分析线程状态。

### RPC 分析注意事项

1. **只能在用户模式下运行**：rpcexts 扩展的命令需要在 CDB/NTSD 或用户态 WinDbg 中运行
2. **需要目标应用程序**：调试器需要有一个目标应用程序（例如 `windbg notepad`），可用 Ctrl+C 中断目标以进入命令窗口
3. **远程调试**：如果要分析远程计算机的 RPC 状态，应在本机启动用户态调试器，然后使用远程调试功能连接
4. **内核态 dump 限制**：对于内核态 dump，rpcexts 命令无法直接使用，需要通过其他方式间接分析

### 替代分析方法（内核态 dump）

当无法使用 rpcexts 扩展时，可以通过以下方式间接分析 RPC 状态：

1. **查看 svchost.exe 进程状态**：RPC 服务通常运行在 svchost.exe 中
   ```
   !process 0 0 svchost.exe
   !process <svchost地址> 7
   ```

2. **查看 ALPC 端口状态**：RPC 底层使用 ALPC（Advanced Local Procedure Call）
   ```
   !alpc /l
   !alpc /p <端口地址>
   ```

3. **查看线程等待状态**：检查是否有线程在等待 RPC 相关的对象
   ```
   !thread <线程地址>
   ```

4. **查看锁状态**：检查是否有锁被 RPC 相关的线程持有
   ```
   !locks
   ```

## WinDbg 命令速查

### 基础命令
- `!analyze -v` - 自动分析
- `.bugcheck` - BugCheck 详细信息
- `vertarget` - 系统版本
- `lm` - 加载的模块列表
- `kv` - 调用栈

### 进程/线程命令
- `!process 0 0` - 所有进程
- `!process <地址> 7` - 进程详情
- `!thread` - 当前线程
- `!thread <地址>` - 线程详情

### 内存命令
- `!vm` - 虚拟内存
- `!memusage` - 内存使用
- `!poolused /t 20` - 池使用

### 锁命令
- `!locks` - 锁状态
- `!deadlock` - 死锁检测

### 驱动命令
- `lmvm <驱动>` - 驱动版本
- `!drvobj <驱动> 7` - 驱动对象
- `!devobj <设备>` - 设备对象
- `!irp <IRP>` - IRP 详情
- `!devstack <设备>` - 设备栈

### 系统级命令
- `!rpc` - RPC 线程池（不可用，需要 rpcexts）
- `!alpc /l` - ALPC 端口列表
- `!alpc /p <端口>` - ALPC 端口详情
- `!irql` - IRQL 检查
- `!pcr` - 处理器控制区域
- `!prcb` - 处理器控制块

### rpcexts 扩展命令（用户态）
- `!rpcexts.help` - 显示帮助
- `!rpcexts.getthreadinfo <PID>` - 获取 RPC 线程信息
- `!rpcexts.getendpointinfo` - 获取 RPC 端点信息
- `!rpcexts.getcallinfo <PID>` - 获取 RPC 调用信息
- `!rpcexts.rpcreadstack <StackPointer>` - 读取 RPC 堆栈
- `!rpcexts.rpctime` - 获取 RPC 时间
- `!rpcexts.mode <模式>` - 切换模式（rpcrt4/msrpc/rhttpaa）

### 其他命令
- `!peb` - 进程环境块
- `!handle` - 句柄
- `dps <地址> L<长度>` - 扫描栈
