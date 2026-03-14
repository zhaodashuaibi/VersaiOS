# 🤖 VersaiOS: AI-Driven iOS Physical Automation Agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hardware: ESP32-S3](https://img.shields.io/badge/Hardware-ESP32--S3-blue.svg)]()
[![AI: Gemini Vision](https://img.shields.io/badge/AI_Brain-Gemini_Pro_Vision-orange.svg)]()

**VersaiOS** 是一个基于“视觉大模型 (VLM) + 硬件级 HID 注入”的次世代 iOS 跨端物理控制系统。

没有传统的 WebDriverAgent (WDA)、Appium 等繁琐的软件级测试框架，**无需越狱、无需 Mac 电脑、无需 7 天开发者证书签名**。只需一块 ESP32 单片机作为“物理机械手”，结合大模型的“视觉大脑”，即可实现对任何未越狱 iPhone 的像素级自然语言控制。

---

## ✨ 核心亮点 (Core Features)

🧠 视觉大脑 (Vision-Language AI)：** 接入 Gemini 视觉大模型，无需繁琐的 UI 树 (XML) 解析。直接输入自然语言（如：“点击微信”或“点右上角的红色关闭按钮”），AI 即可自动理解屏幕语义并返回目标相对坐标。

🛡️ 降维物理打击 (Hardware HID Attack)：** 电脑端 Python 大脑下发绝对坐标指令，ESP32 伪装成苹果官方蓝牙鼠标执行物理点击。从底层彻底绕过iOS 软件层面的自动化防护。

🎯 独创“暴力归零”防加速算法 (Corner-Bumping Algorithm)：** iOS 系统内置了强制的蓝牙鼠标加速度机制（且无法通过常规协议关闭），导致绝对坐标定位极难。本项目在单片机 C++ 固件中植入了极客级的“左上角暴力归零 + 像素级匀速步进”算法，完美抵消了 iOS 的倍率放大，实现了指哪打哪的绝对坐标精准命中。

---

## 🏗️ 系统架构 (Architecture)

本系统的控制链路分为四个绝对隔离的层级，确保安全：

```text
[ 👁️ 眼睛层 ] -> [ 🧠 大脑层 ] -> [ ⚡ 神经层 ] -> [ 🦾 物理执行层 ]

  PC 投屏软件 -> Python 主控端 -> USB 串口通讯 -> ESP32-S3 -> iPhone
```
## 🛠️ 硬件与环境依赖 (Requirements)
硬件： ESP32 开发板（实测型号：ESP32-S3-N16R8）。

iOS 设置： * 开启 辅助触控 (AssistiveTouch)。

将 跟踪速度 (Tracking Speed) 调至正中间。

关闭 指针动画 (Pointer Animations)。

软件环境： * Python 3.8+ (依赖请见 requirements.txt)

Arduino IDE (需手动安装 T-vK 的 ESP32-BLE-Mouse 库，并建议将 esp32 core 降级至 2.0.17 以避免编译错误)

PC 端需运行 iOS 投屏软件（如基于 AirPlay 协议的 UxPlay）。
## 🚀 开始 (Start)
烧录固件： 将 hardware/esp32_ble_mouse/esp32_ble_mouse.ino 烧录至 ESP32-S3 开发板。

连接蓝牙： 保持开发板通过 USB 连接电脑，在 iPhone 蓝牙列表中连接名为 VersaiOS_Hand 的设备。

配置参数： API Key、串口、投屏窗口名与 HID 校准步数等不再写进代码，而是集中在配置层，请任选其一方式配置：
- **推荐** 在 `src` 目录下复制 `config.example.ini` 为 `config.ini`，填入 `api_key`、`com_port`、`window_title`、`hid_max_x`、`hid_max_y`（`config.ini` 已被 git 忽略，不会提交）；
- 或设置环境变量：`VERSAIOS_API_KEY`、`VERSAIOS_COM_PORT`、`VERSAIOS_WINDOW_TITLE`、`VERSAIOS_HID_MAX_X`、`VERSAIOS_HID_MAX_Y`。

校准步数： 退出烧录程序之后运行 src/calibrate_mouse.py，根据你的 iPhone 型号，测出屏幕边缘的极限 HID 步数:

```
cd src
python calibrate_mouse.py
```
将测得的步数填入 `config.ini` 的 `hid_max_x`、`hid_max_y`（或设置环境变量 `VERSAIOS_HID_MAX_X`、`VERSAIOS_HID_MAX_Y`）。

确保PC与iPhone在同一局域网内，在iPhone上使用屏幕镜像投屏至PC:

```
cd src
python main.py
```
点火运行：

```
python main_versaios.py
```
## 💡 开发者笔记 (Developer Notes)：
在开发过程中，我们发现 iOS 针对非原装蓝牙鼠标具有底层强制加速机制（跟踪速度居中时，放大倍率约 2.8 倍）。
不要试图在 PC 端通过调整窗口分辨率（如 UxPlay 的 -s 参数）来修复坐标偏移，这是无效的。唯一的解法是在 Python 控制端进行降维截断映射。
```
iPhone 16 标准版实测物理极限步数参考： HID_MAX_X = 140, HID_MAX_Y = 310。
```
为了实测AI的视觉层对点击位置坐标的识别准确情况，可以运行库内的src/test_vision.py。
确保已通过 `config.ini` 或环境变量配置好 API Key 后，再执行下列命令，即可生成带红圈标记的调试图片：
```
python test_vision.py
```
## 📝 更新说明 (Changelog)

- **配置抽离与安全性提升**
  - 不再在代码中硬编码 Gemini API Key、串口号、投屏窗口名等敏感或环境相关参数，统一通过 `src/config.py` 读取 `config.ini` / 环境变量。
  - 新增 `config.example.ini`，引导用户复制为 `config.ini` 并填写 `api_key`、`com_port`、`window_title`、`hid_max_x`、`hid_max_y`，避免误把私密信息提交到 Git。
- **HID 校准与 Prompt 配置统一化**
  - HID 极限步数 (`hid_max_x` / `hid_max_y`) 由 `calibrate_mouse.py` 校准后写入 `config.ini`，主程序通过 `config.get_hid_max_x()` / `get_hid_max_y()` 统一读取，实现多机多型号可配置。
  - 高精度 UI 点击的系统 Prompt 已抽离到 `config.get_system_prompt()` 中，如需调整点击策略或语言风格，只需修改该函数（或扩展为从独立 Prompt 文件加载），无需改动业务逻辑代码。
