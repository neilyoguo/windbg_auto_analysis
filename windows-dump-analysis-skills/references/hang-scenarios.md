# 系统卡死（Hang）深度分析指南

## 概述

系统卡死是最常见的分析场景。当用户报告"登录卡死"、"RDP 黑屏"、"桌面无响应"时，按本指南执行。

## Hang 场景识别

- 系统未蓝屏，但无响应
- 用户界面冻结，无法输入
- RDP 连接后黑屏
- 任务管理器无法打开
- BugCheckCode 为 0x161（LIVE_SYSTEM_DUMP）

## 分析流程

### 第 1 轮：基础状态（必须执行）

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!running -it",
    "!locks",
    "!vm",
    "!process 0 0"
])
```

**分析要点**：
- CPU 是否全部 idle？→ 可能是 I/O 等待或锁阻塞
- `!locks` 是否有 ERESOURCE 被独占？→ 锁持有者在做什么？
- `!vm` 可用内存是否 < 10%？→ 内存压力
- `!process 0 0` 进程数是否 > 200？→ 进程泄漏

### 第 2 轮：关键进程分析（必须执行）

根据第 1 轮 `!process 0 0` 输出中的 PID：

```
run_windbg_cmd(dump_path=<path>, commands=[
    "!process <LogonUI_pid> 7",
    "!process <dwm_pid> 7",
    "!process <csrss_pid> 7",
    "!process <svchost_pid> 7"
])
```

**分析要点**：
- LogonUI.exe 线程是否全部 WAIT？→ 登录流程阻塞
- dwm.exe 线程状态？→ 桌面渲染阻塞
- csrss.exe 线程状态？→ 客户端/服务器运行时阻塞
- svchost.exe 托管哪些服务？→ ProfSvc/UserManager/Appinfo/Schedule/WMI

### 第 3 轮：线程与通信分析（必须执行）

```
run_windbg_cmd(dump_path=<path>, commands=[
    "~* kvn",
    "!rpc",
    "!alpc /l"
])
```

**分析要点**：
- 线程是否等待 `WrLpcReply`/`WrLpcReceive`？→ ALPC 通信阻塞
- RPC worker 是否被卡满？
- ALPC 端口是否有大量未完成连接？

### 第 4 轮：驱动与服务分析（必须执行）

```
run_windbg_cmd(dump_path=<path>, commands=[
    "lmvm <suspect_driver>",
    "!drvobj <driver> 7"
])
```

**分析要点**：
- 是否有多个安全/监控驱动同时加载？
- 文件系统过滤驱动是否争用 IRP？
- 驱动版本是否有已知问题？

## 交叉验证矩阵

| 验证点 | 验证方法 | 预期一致性 |
|--------|----------|-----------|
| 进程阻塞 | `!process 7` vs `~* kvn` | 线程 WAIT 状态匹配 |
| 通信阻塞 | `!thread` vs `!rpc` | WrLpcReply 与 RPC 状态匹配 |
| 进程泄漏 | `!process 0 0` vs `!vm` | 进程数与资源消耗匹配 |
| 锁竞争 | `!locks` vs `!thread` | 锁 owner 与线程等待匹配 |
| 驱动冲突 | `lm` vs `!drvobj` | 驱动列表与驱动行为匹配 |

## 证据链模板

```
用户现象: [具体现象，如登录卡死、RDP 黑屏]

[第一层: 直接表现]
[关键进程] 所有线程被阻塞
  -> 等待类型: [WrLpcReply/WrResource/WrQueue]
  -> 等待时间: [具体时长]

[第二层: 根因]
[阻塞原因] ALPC 通信阻塞 / 锁竞争 / 资源耗尽
  -> 调用目标: [目标进程/服务]
  -> 未响应原因: [RPC worker 卡满/服务死锁/内存耗尽]

[第三层: 加重因素]
[进程泄漏/安全软件冲突/资源耗尽]
  -> 具体进程: [进程名和数量]
  -> 影响: [消耗的资源类型]

结果: 系统服务层全面阻塞，用户界面无法响应
```

## 置信度判断

| 级别 | 标准 |
|------|------|
| 高 | 确认具体服务卡死 + 有直接证据（RPC worker 占满、锁 owner 明确） |
| 中 | 确认具体服务卡死，但缺乏直接证据 |
| 低 | 只有推测，未确认具体服务 |

## 常见根因

1. **ALPC/RPC 通信阻塞**：svchost 服务死锁、RPC worker 占满
2. **进程泄漏**：安装脚本循环调用、更新程序死循环
3. **安全软件冲突**：多个安全驱动争用 IRP
4. **资源耗尽**：内存/句柄/线程耗尽
5. **I/O stall**：存储驱动阻塞、磁盘无响应
