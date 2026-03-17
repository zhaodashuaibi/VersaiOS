# 🤖 VersaiOS: AI-Driven iOS Physical Automation Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hardware: ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-blue.svg)]()
[![AI: VLM](https://img.shields.io/badge/AI_Brain-Multi_Provider-orange.svg)]()

**VersaiOS** 是一个基于“视觉大模型 (VLM) + 硬件级 HID 注入”的次世代 iOS 跨端物理控制系统。

没有传统的 WebDriverAgent (WDA)、Appium 等繁琐的软件级测试框架，**无需越狱、无需 Mac 电脑、无需 7 天开发者证书签名**。只需一块 ESP32 单片机作为“物理机械手”，结合大模型的“视觉大脑”，即可实现对任何未越狱 iPhone 的像素级自然语言控制。

---

## ✨ 核心亮点 (Core Features)

🧠 视觉大脑 (Vision-Language AI)：** 支持多家视觉大模型（Gemini / OpenAI 兼容接口等），无需繁琐的 UI 树 (XML) 解析。直接输入自然语言（如：“点击微信”或“点右上角的红色关闭按钮”），AI 即可自动理解屏幕语义并返回目标相对坐标。

🛡️ 降维物理打击 (Hardware HID Attack)：** 电脑端 Python 大脑下发绝对坐标指令，ESP32 伪装成苹果官方蓝牙鼠标执行物理点击。从底层彻底绕过iOS 软件层面的自动化防护。

🎯 算法升级：中线十字定位法 (Midline Crosshair Reset)：** 每次点击前，ESP32 会通过边缘撞击利用屏幕“平直边缘”将光标精准重置到绝对中心点 (0.5, 0.5)，完美解决 iOS 圆角/滑动边缘导致的光标偏航问题，为后续相对位移提供像素级基准。

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

## 🛠️ 硬件与环境依赖 (Requirements)
硬件： ESP32 开发板（实测型号：ESP32-S3-N16R8）。

iOS 设置：

- 开启 **辅助触控 (AssistiveTouch)**。
- 关闭 **指针动画 (Pointer Animations)**（必须）。
- 将 **跟踪速度 (Tracking Speed)** 固定为同一档位（**强烈建议调到最小**），避免相对位移出现倍率漂移。

软件环境： * Python 3.8+ (依赖请见 requirements.txt)

Arduino IDE (需手动安装 T-vK 的 ESP32-BLE-Mouse库 https://github.com/T-vK/ESP32-BLE-Mouse ，并建议将 esp32 core 降级至 2.0.17 以避免编译错误)

PC 端需运行 iOS 投屏软件（如基于 AirPlay 协议的 UxPlay）。
## 🚀 开始 (Start)
烧录固件： 将 hardware/esp32_ble_mouse/esp32_ble_mouse.ino 烧录至 ESP32-S3 开发板。

连接蓝牙： 保持开发板通过 USB 连接电脑，在 iPhone 蓝牙列表中连接名为 VersaiOS_Hand 的设备。

配置参数：LLM（模型提供方/Key/模型名/端点）、串口、投屏窗口名与 HID 校准步数等不再写进代码，而是集中在配置层，请任选其一方式配置：
- **推荐** 在 `src` 目录下复制 `config.example.ini` 为 `config.ini`，填写 `llm_provider`、`llm_api_key`、`llm_model`（如使用 OpenAI 兼容接口再填 `llm_base_url`），以及 `com_port`、`window_title`、`hid_max_x`、`hid_max_y`（`config.ini` 已被 git 忽略，不会提交）；
- 或设置环境变量：`VERSAIOS_LLM_PROVIDER`、`VERSAIOS_LLM_API_KEY`、`VERSAIOS_LLM_MODEL`、`VERSAIOS_LLM_BASE_URL`、`VERSAIOS_COM_PORT`、`VERSAIOS_WINDOW_TITLE`、`VERSAIOS_HID_MAX_X`、`VERSAIOS_HID_MAX_Y`。

### 🎮 校准步数（V2.0：交互式遥控器）

V2.0 起，`hid_max_x/hid_max_y` 表示“跨越整块屏幕所需的**相对总步数**”（用于 `SET:max_x,max_y`），不再是旧版的绝对极限坐标。

退出烧录程序后运行 `src/calibrate_mouse.py`，使用 **w/a/s/d + 步数** 的方式像游戏一样遥控光标并累加总步数，最终得到跨屏总步数：

```
cd src
python calibrate_mouse.py
```

示例（具体交互以脚本提示为准）：

- `d 100`：向右移动 100 步
- `a 50`：向左移动 50 步
- `w 30`：向上移动 30 步
- `s 30`：向下移动 30 步

将测得的跨屏总步数填入 `config.ini` 的 `hid_max_x`、`hid_max_y`（或设置环境变量 `VERSAIOS_HID_MAX_X`、`VERSAIOS_HID_MAX_Y`）。

### 🖥️ 投屏接收端（独立模块：`UxPlay/`）

投屏接收端与 VersaiOS 主程序已分离。先启动接收端，再在 iPhone 上发起「屏幕镜像」。

```
cd UxPlay
python main.py
```

启动成功后会提示“视觉引擎已就绪…”。默认窗口名为 `VersaiOS_Screen`（可在 `src/config.ini` 的 `window_title` 配置中匹配该名称）。

### 🧠 主控端（`src/`）

安装依赖：

```
pip install -r requirements.txt
```

点火运行（主程序）：

```
cd src
python main_versaios.py
```

### 🧩 V2.0 配置迁移提示（重要）

- 如果你曾在 `config.ini` 中填过旧版“绝对坐标/极限坐标”的 `hid_max_x/hid_max_y`，请**清理并重新校准**为 V2.0 的“跨屏相对总步数”。
- 使用新版本前，请务必在 iOS 设置中关闭“指针动画”，并将“跟踪速度”固定档位（建议最小），否则会严重影响相对位移准确性。

## 💡 开发者笔记 (Developer Notes)

- **目录职责**
  - `UxPlay/`：投屏接收端（负责把 iPhone 画面接收到桌面窗口）
  - `src/`：主控端（截图、调用 VLM、串口控制 ESP32 执行动作）

- **运行顺序（重要）**
  - 先启动 `UxPlay/main.py`，再启动 `src/main_versaios.py`
  - 如果投屏窗口被最小化/不可见，很多截图方案会抓不到画面；请保持窗口可见（不最小化）

- **窗口名匹配**
  - `UxPlay/main.py` 默认窗口名是 `Direct3D12 Renderer`
  - 主控端通过 `window_title` 定位窗口；找不到窗口时优先检查：窗口名是否一致、窗口是否存在/未最小化

- **模型输出约束**
  - 主控端要求模型返回**严格 JSON**，字段包含 `x_ratio/y_ratio`（0~1），可选 `reason`
  - 如果你接入的 `openai_compatible` 端点不支持 `response_format`，代码会自动降级，但仍依赖提示词约束输出 JSON

- **调试：验证坐标是否点准**
  - 运行 `src/test_vision.py` 会生成带红圈的验证图片 `debug_target_result.png`

```
cd src
python test_vision.py
```

## 📝 更新日志

本项目的版本变更统一维护在 `CHANGELOG.md`，请查看该文件。
