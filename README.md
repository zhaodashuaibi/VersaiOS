# 🤖 VersaiOS: AI-Driven iOS Physical Automation Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hardware: ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-blue.svg)]()
[![AI: VLM](https://img.shields.io/badge/AI_Brain-Multi_Provider-orange.svg)]()

**VersaiOS** 是一个基于“视觉大模型 (VLM) + 硬件级 HID 注入”的次世代 iOS 跨端物理控制系统。

没有传统的 WebDriverAgent (WDA)、Appium 等繁琐的软件级测试框架，**无需越狱、无需 Mac 电脑、无需 7 天开发者证书签名**。只需一块 ESP32 单片机作为“物理机械手”，结合大模型的“视觉大脑”，即可实现对任何未越狱 iPhone 的像素级自然语言控制。

---

## ✨ 核心亮点 (Core Features)

🧠 视觉大脑 (Vision-Language AI)：** 支持多家视觉大模型（Gemini / OpenAI 兼容接口等），无需繁琐的 UI 树 (XML) 解析。直接输入自然语言（如：“点击微信”或“点右上角的红色关闭按钮”），AI 即可自动理解屏幕语义并返回目标相对坐标。

🛡️ 降维物理打击 (Hardware HID Attack)：** 电脑端 Python 大脑下发绝对坐标指令，ESP32 伪装成苹果官方蓝牙鼠标执行物理点击。从底层彻底绕过 iOS 软件层面的自动化防护。

🎯 算法升级：中线十字定位法 (Midline Crosshair Reset)：** 每次点击前，ESP32 会通过边缘撞击利用屏幕“平直边缘”将光标精准重置到绝对中心点 (0.5, 0.5)，完美解决 iOS 圆角/滑动边缘导致的光标偏航问题，为后续相对位移提供像素级基准。

🖥️ 图形化控制台：** V2.5 起提供 `gui_app.py` 一站式图形界面，将准备工作与日常使用整合为两个阶段，无需手动进入 `src/` 运行任何脚本。

---

## 🏗️ 系统架构 (Architecture)

本系统控制链路分为四个层级，并在 V2.0 完成了“软硬分离”：所有屏幕尺寸/边界计算逻辑上移到 Python；ESP32 仅做“纯执行引擎”，未来调整屏幕参数无需重复烧录固件。

```text
[ 👁️ 眼睛层 ] -> [ 🧠 大脑层 ] -> [ ⚡ 神经层 ] -> [ 🦾 物理执行层 ]

  PC 投屏软件 -> Python 主控端 -> USB 串口通讯 -> ESP32-S3 -> iPhone
```

### 🔌 串口通信协议（V2.0）

- `SET:max_x,max_y`：Python 下发动态屏幕边界（相对鼠标引擎的“跨屏总步数”）。
- `REL:dx,dy`：纯相对位移（用于交互式校准/遥控）。
- `CLICK:x,y`：接收目标后由固件自动执行“中线校准 -> 相对滑行 -> 点击”。

---

## 🛠️ 硬件与环境依赖 (Requirements)

硬件： ESP32 开发板（实测型号：ESP32-S3-N16R8）。

iOS 设置：

- 开启 **辅助触控 (AssistiveTouch)**。
- 关闭 **指针动画 (Pointer Animations)**（必须）。
- 将 **跟踪速度 (Tracking Speed)** 固定为同一档位（**强烈建议调到最小**），避免相对位移出现倍率漂移。

软件环境：

- Python 3.10+（依赖请见 `requirements.txt`）
- Arduino IDE（需手动安装 T-vK 的 ESP32-BLE-Mouse 库 https://github.com/T-vK/ESP32-BLE-Mouse ，并建议将 esp32 core 降级至 2.0.17 以避免编译错误）
- PC 端需运行 iOS 投屏软件（如基于 AirPlay 协议的 UxPlay，已内置在 `UxPlay/`）

---

## 🚀 开始 (Start)

### 1. 烧录固件

将 `hardware/esp32_ble_mouse/VersaiOS.ino` 烧录至 ESP32-S3 开发板。

### 2. 连接蓝牙

保持开发板通过 USB 连接电脑，在 iPhone 蓝牙列表中连接名为 **VersaiOS Mouse** 的设备（固件代码中 `BleMouse` 构造函数传入的设备名）。

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

> 注意：`requirements.txt` 位于项目根目录，请在项目根目录下执行。

### 4. 启动图形化控制台（推荐）

```bash
python gui_app.py
```

`gui_app.py` 会引导你完成两个阶段：

1. **阶段一：准备**
   - 配置 LLM 提供方、API Key、模型名、串口号；
   - 通过方向键遥控光标完成 HID 步数校准，并保存 `hid_max_x` / `hid_max_y`。
2. **阶段二：运行**
   - 启动 `UxPlay` 投屏接收端；
   - 在 iPhone 上发起屏幕镜像；
   - 启动主控端，输入自然语言指令（如“点击微信”）执行自动化操作。

`gui_app.py` 启动时会自动从 `src/config.example.ini` 创建 `src/config.ini`（`config.ini` 已被 git 忽略，不会提交）。

---

## 🎮 校准步数（V2.0：交互式遥控器）

V2.0 起，`hid_max_x/hid_max_y` 表示“跨越整块屏幕所需的**相对总步数**”（用于 `SET:max_x,max_y`），不再是旧版的绝对极限坐标。

### 图形界面方式（推荐）

在 `gui_app.py` 的“阶段一：准备”中：

1. 输入串口号并点击“连接 ESP32”；
2. 使用 **W/A/S/D + 步长** 遥控光标移动；
3. 到达屏幕边缘后点击“归零”，再向反方向移动到底；
4. 将最终累计步数填入 `hid_max_x` / `hid_max_y`，点击“保存全部配置”。

---

## 🖥️ 投屏接收端（独立模块：`UxPlay/`）

投屏接收端与 VersaiOS 主程序已分离。你可以通过图形界面一键启动，也可以手动启动：

```bash
cd UxPlay
python main.py
```

启动成功后会提示“视觉引擎已就绪…”。默认窗口名为 `VersaiOS_Screen`（已在 `UxPlay/main.py` 中固定，与 `src/config.py` 的 `DEFAULT_WINDOW_TITLE` 一致）。

---

## 🧠 主控端（`src/`）

### 图形界面方式（推荐）

在 `gui_app.py` 的“阶段二：运行”中：

1. 先启动“投屏接收端”，然后在 iPhone 上发起屏幕镜像；
2. 启动“主控端”；
3. 在“自然语言指令”输入框中输入指令并发送，例如：
   - `点击微信`
   - `点右上角的红色关闭按钮`

主控端运行日志会实时显示在界面下方的日志区域。

### 命令行方式（备用）

```bash
cd src
python main_versaios.py
```

---

## 🧩 V2.0 配置迁移提示（重要）

- 如果你曾在 `config.ini` 中填过旧版“绝对坐标/极限坐标”的 `hid_max_x/hid_max_y`，请**清理并重新校准**为 V2.0 的“跨屏相对总步数”。
- 使用新版本前，请务必在 iOS 设置中关闭“指针动画”，并将“跟踪速度”固定档位（建议最小），否则会严重影响相对位移准确性。

---

## 💡 开发者笔记 (Developer Notes)

- **目录职责**
  - `gui/`：图形化控制台模块（`gui_app.py` 拆分为 `calibration_module.py` 与 `control_module.py`）
  - `UxPlay/`：投屏接收端（负责把 iPhone 画面接收到桌面窗口）
  - `src/`：主控端（截图、调用 VLM、串口控制 ESP32 执行动作）
  - `hardware/`：ESP32 固件源码

- **图形化流程（推荐）**
  - 运行 `python gui_app.py` 完成全部操作；
  - 阶段一负责模型配置与 HID 校准，阶段二负责接收端启动与指令交互；
  - 无需手动运行 `src/` 或 `UxPlay/` 下的脚本。

- **命令行运行顺序（备用）**
  - 先启动 `UxPlay/main.py`，再启动 `src/main_versaios.py`；
  - 如果投屏窗口被最小化/不可见，很多截图方案会抓不到画面；请保持窗口可见（不最小化）。

- **窗口名匹配**
  - `UxPlay/main.py` 默认窗口名是 `VersaiOS_Screen`（与 `src/config.py` 的 `DEFAULT_WINDOW_TITLE` 一致）
  - 主控端通过 `window_title` 定位窗口；找不到窗口时优先检查：窗口名是否一致、窗口是否存在/未最小化

- **模型输出约束**
  - 主控端要求模型返回**严格 JSON**，字段包含 `x_ratio/y_ratio`（0~1），可选 `reason`
  - 如果你接入的 `openai_compatible` 端点不支持 `response_format`，代码会自动降级，但仍依赖提示词约束输出 JSON

- **调试：验证坐标是否点准**
  - 在 `gui_app.py` 的“阶段二：运行”中点击“测试视觉（截图 + 标红目标）”，系统会截取当前画面、调用 VLM 预测目标位置并绘制红圈，结果保存为 `assets/debug_target_result.png` 同时弹窗预览。

## 📝 更新日志

本项目的版本变更统一维护在 `CHANGELOG.md`，请查看该文件。
