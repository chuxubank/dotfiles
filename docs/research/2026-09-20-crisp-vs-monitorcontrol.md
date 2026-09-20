# Crisp vs. MonitorControl：是否集成 Crisp

**日期：** 2026-09-20  
**结论：** 目前**不需要把 Crisp 集成进 chezmoi**。继续保留 MonitorControl；如果以后明确需要 Crisp 独有的显示管理功能，再做一次互斥试用，并在验证后以 Crisp **替换** MonitorControl，而不是让两者常驻。

## 本机现状

- `home/.chezmoidata/packages/brew/casks.toml` 当前无条件管理 `monitorcontrol`。
- 当前机器是 Apple M5 MacBook Pro、macOS 27.0；正在使用两台外接屏：
  - LG HDR 4K：3840×2160，界面缩放为 1920×1080 @ 60 Hz；
  - L27qe：4096×2304，界面缩放为 2048×1152 @ 100 Hz。
- 两块屏目前都处在精确 2× 的 HiDPI 模式，没有从系统状态中看到“文字模糊或尺寸不合适”的直接证据。
- MonitorControl 正在运行，当前 App bundle 已是 4.4.0。其偏好记录表明两台外屏都使用过 DDC 亮度/音量控制；亮度同步与亮度键接管目前未启用。

## 功能对比

| 能力 | MonitorControl 4.4.0 | Crisp 1.6.0 | 对当前配置的意义 |
|---|---|---|---|
| 外屏硬件亮度、音量 | 有，DDC | 有，DDC | 高度重叠 |
| DDC 硬件对比度 | 有 | UI 主打 gamma 图像调整，不等同于显示器硬件对比度 | MonitorControl 更专门 |
| 软件调暗、低于硬件最低亮度 | 有 | 有 | 重叠 |
| 多屏联动、键盘媒体键、OSD | 有 | 有 | 同时运行会争用快捷键并重复发送控制 |
| HiDPI / 灵活缩放 / 分辨率与刷新率管理 | 无 | 有 | 当前两屏已经是 2× HiDPI；除非想要更细的缩放档位，否则收益有限 |
| 保存亮度、分辨率、排列预设 | 无 | 有 | 只有经常切换桌面/拓扑时才明显有用 |
| 屏幕排列、主屏切换、物理屏断开 | 无 | 有（断开仅 Apple Silicon） | 有明确工作流时才值得迁移 |
| 虚拟显示器 | 无 | 有 | 远程桌面、录屏或特殊多屏工作流才需要 |
| HDR/XDR Extra Brightness、HDR 开关、ICC/颜色工具 | 无或有限 | 有 | 如果确实需要 HDR 增亮/颜色工具，这是最强迁移动机之一 |
| CLI 自动化 | 无官方 CLI | 有 `crispctl` | 如果要把亮度、HDR、显示器连接状态写入脚本，这是 Crisp 的明确优势 |
| macOS 27 明确兼容声明 | 4.4.0 release 和 README 明确覆盖 | README 只声明 macOS 14+；1.6.0 重点描述 macOS 26 | 当前系统上 MonitorControl 风险更低 |

来源：[MonitorControl README](https://github.com/MonitorControl/MonitorControl)、[MonitorControl 4.4.0](https://github.com/MonitorControl/MonitorControl/releases/tag/v4.4.0)、[Crisp README](https://github.com/didriksg/Crisp)、[Crisp 1.6.0](https://github.com/didriksg/Crisp/releases/tag/v1.6.0)。

## 为什么现在不集成

1. **核心需求已经满足。** 当前 MonitorControl 已在两台外屏上留下有效 DDC 状态，而且进程运行正常。
2. **Crisp 最大卖点之一当前没有明显缺口。** 两台外屏已经分别使用 1920×1080@2× 和 2048×1152@2× HiDPI；没有必要仅为了“更清晰”更换工具。
3. **不能把 Crisp 当作无冲突补充。** 两者都会控制 DDC 亮度/音量、媒体键和 OSD。并行常驻会造成重复 UI、快捷键所有权冲突和相互覆盖的 DDC 写入。
4. **MonitorControl 对 macOS 27 的承诺更明确。** 4.4.0 专门修复了 macOS 26/27 的 OSD、设置窗口和快捷键问题；Crisp 尚未在官方材料中明确声明 macOS 27。
5. **成熟度差异明显。** MonitorControl 始于 2017 年；Crisp 始于 2026 年 7 月。Crisp 开发很活跃，1.6.0 也修复了多屏 DDC、唤醒和重连问题，但运行历史仍短。
6. **Crisp 的高级功能扩大了私有 API 与系统改动范围。** 两者在 Apple Silicon DDC 上都依赖非公开机制；Crisp 还通过私有显示 API实现虚拟屏、拓扑和系统显示控制。其“平滑缩放”首次启用时还会经管理员授权向 `/Library/Displays/Contents/Resources/Overrides` 写入覆盖文件。普通 HiDPI 和其他功能不需要这一步。

## 什么时候值得试 Crisp

以下任一需求变成真实痛点时，再试用：

- 当前 2× 档位太大或太小，需要更细的 HiDPI 缩放，同时保留 100 Hz；
- 经常在不同扩展坞、屏幕排列或亮度组合之间切换，需要一键预设；
- 需要从 shell/快捷指令调用 `crispctl` 控制亮度、HDR 或连接状态；
- 需要虚拟显示器、物理屏软断开、HDR/XDR Extra Brightness 或集中颜色管理。

## 建议的迁移门槛

若要试用：

1. 不修改 chezmoi，临时执行 `brew install --cask crisp`。
2. 完全退出 MonitorControl，并暂时禁用其登录启动；不要让两个应用同时控制显示器。
3. 第一阶段不要启用平滑缩放、物理屏断开、HDR boost 或系统切换；先验证两屏各自与同时连接时的 DDC 亮度/音量、L27qe 100 Hz、睡眠唤醒、拔插扩展坞及软件调暗。
4. 稳定使用至少一个正常工作周，并确认实际持续使用了 Crisp 的独有能力。
5. 通过后，在 `home/.chezmoidata/packages/brew/casks.toml` 中用 `crisp` **替换** `monitorcontrol`；未通过则卸载 Crisp，维持现状。

## 最终判断

**现在不集成。** Crisp 不是当前 MonitorControl 配置缺失的必要依赖，而是一个功能范围更广、但更年轻的替代品。只有在你明确需要灵活缩放、预设、拓扑控制、HDR/虚拟屏或 CLI 自动化时，才值得做互斥试用并考虑迁移。
