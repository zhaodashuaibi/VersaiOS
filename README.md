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

配置参数： API Key、串口、投屏窗口名与 HID 校准步数等不再写进代码，而是集中在配置层，请任选其一方式配置：
- **推荐** 在 `src` 目录下复制 `config.example.ini` 为 `config.ini`，填入 `api_key`、`com_port`、`window_title`、`hid_max_x`、`hid_max_y`（`config.ini` 已被 git 忽略，不会提交）；
- 或设置环境变量：`VERSAIOS_API_KEY`、`VERSAIOS_COM_PORT`、`VERSAIOS_WINDOW_TITLE`、`VERSAIOS_HID_MAX_X`、`VERSAIOS_HID_MAX_Y`。

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

确保PC与iPhone在同一局域网内，在iPhone上使用屏幕镜像投屏至PC:

```
cd src
python main.py
```
点火运行：

```
python main_versaios.py
```

### 🧩 V2.0 配置迁移提示（重要）

- 如果你曾在 `config.ini` 中填过旧版“绝对坐标/极限坐标”的 `hid_max_x/hid_max_y`，请**清理并重新校准**为 V2.0 的“跨屏相对总步数”。
- 使用新版本前，请务必在 iOS 设置中关闭“指针动画”，并将“跟踪速度”固定档位（建议最小），否则会严重影响相对位移准确性。

## 💡 开发者笔记 (Developer Notes)：
V2.0 的相对鼠标引擎将“屏幕尺寸/边界映射”逻辑上移到 Python，并通过 `SET:max_x,max_y` 与固件同步，避免频繁改固件。

为了实测AI的视觉层对点击位置坐标的识别准确情况，可以运行库内的src/test_vision.py。
确保已通过 `config.ini` 或环境变量配置好 API Key 后，再执行下列命令，即可生成带红圈标记的调试图片：
```
python test_vision.py
```
## 📝 更新说明 (Changelog)

- **V2.0 - 相对鼠标引擎与动态校准重构**
  - 彻底软硬分离：屏幕尺寸/边界计算逻辑上移到 Python，ESP32 变为纯执行引擎。
  - 引入“中线十字定位法”：点击前自动重置到 (0.5, 0.5) 作为相对位移基准，显著提升 iOS 圆角/滑动边缘场景的稳定性。
  - 新串口协议：`SET:max_x,max_y` / `REL:dx,dy` / `CLICK:x,y`。
  - `main_versaios.py`：连接串口后会同步下发边界参数（对应 `SET`）。
  - `config.py`：`hid_max_x/hid_max_y` 默认值体系切换为相对步数（建议使用 `calibrate_mouse.py` 重新测量）。
  - `calibrate_mouse.py`：史诗级重构为“交互式遥控器”，支持 w/a/s/d + 步数并自动累加跨屏总步数。

- **配置抽离与安全性提升**
  - 不再在代码中硬编码 Gemini API Key、串口号、投屏窗口名等敏感或环境相关参数，统一通过 `src/config.py` 读取 `config.ini` / 环境变量。
  - 新增 `config.example.ini`，引导用户复制为 `config.ini` 并填写 `api_key`、`com_port`、`window_title`、`hid_max_x`、`hid_max_y`，避免误把私密信息提交到 Git。
- **HID 校准与 Prompt 配置统一化**
  - HID 极限步数 (`hid_max_x` / `hid_max_y`) 由 `calibrate_mouse.py` 校准后写入 `config.ini`，主程序通过 `config.get_hid_max_x()` / `get_hid_max_y()` 统一读取，实现多机多型号可配置。
  - 高精度 UI 点击的系统 Prompt 已抽离到 `config.get_system_prompt()` 中，如需调整点击策略或语言风格，只需修改该函数（或扩展为从独立 Prompt 文件加载），无需改动业务逻辑代码。
