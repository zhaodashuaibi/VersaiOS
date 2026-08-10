## 更新日志（Changelog）

本项目采用“尽量可读”的更新记录方式：按日期归档，描述对使用者有影响的变化。

## V3.1.0（2026-08-10）

- **模型接口收敛为 OpenAI 兼容接口**
  - 删除 GUI 中的模型厂商下拉选择，固定使用 OpenAI 兼容接口，默认 `llm_provider = openai_compatible`。
  - `src/config.py` 移除各厂商默认端点/模型与多厂商选择逻辑；`src/ai_brain.py` 只保留 openai SDK 调用路径。
  - `requirements.txt` 移除 `google-genai`、`anthropic`，仅保留 `openai`。

- **GUI 配置写入修复**
  - 「阶段一：准备」新增「确认并写入 config」按钮：填写 API Key / Base URL / 模型名后点击，立即写入 `src/config.ini` 并刷新配置缓存。
  - Base URL 标签明确为必填并给出示例端点；`config.ini` / `config.example.ini` 同步更新为 `openai_compatible`。

## V3.0.2（2026-08-05）

- **requirements.txt 与 Python 3.13 兼容性修复**
  - `numpy`：`<2.0.0` → `<3.0.0`（numpy 1.x 无 Python 3.13 wheel）。
  - `Pillow`：`<11.0.0` → `<12.0.0`。
  - `mss`：`<10.0.0` → `<11.0.0`。
  - `opencv-python`：`>=4.8.0` → `>=4.10.0`（确保提供 Python 3.13 预编译包）。

- **SDK 专属异常重试修复（`src/ai_brain.py`）**
  - 在 `VersaiOSAgent.__init__` 中按 provider 收集可重试异常：Gemini `ServerError`、OpenAI `APIConnectionError/RateLimitError/InternalServerError`、Anthropic 对应异常，并叠加 Python `ConnectionError/TimeoutError`。
  - `analyze_ui_and_plan` 统一捕获 `self._retryable_errors`，避免 SDK 专属网络/限流异常被裸 `except Exception` 吞掉。

- **视觉捕获稳定性增强（`src/vision_engine.py`）**
  - `_get_window_rect` 在保留具体异常捕获的基础上，新增 `Exception` 兜底分支，窗口枚举偶发错误时返回 `None` 而非崩溃。

- **GUI 异常捕获收窄**
  - `gui/calibration_module.py`：串口操作统一捕获 `_SERIAL_ERRORS = (serial.SerialException, PermissionError, OSError)`。
  - `gui/control_module.py`：子进程操作统一捕获 `_PROCESS_ERRORS = (subprocess.SubprocessError, OSError)`；stdin 写入捕获 `(OSError, ValueError)`。

## V3.0.1（2026-08-02）

- **模型选择器扩展**
  - 模型厂商按 OpenAI、兼容 OpenAI 接口（本地模型/中转代理）、DeepSeek、Google Gemini、Anthropic Claude、智谱 AI、阿里通义千问、MiniMax 的顺序展示。
  - 新增官方默认模型与端点；切换厂商时 GUI 自动填充推荐值，同时保留用户手动填写的模型名和代理端点。
  - DeepSeek、智谱、通义、MiniMax 复用 OpenAI 兼容调用；Claude 新增 Anthropic Messages API 路径与 `anthropic` 依赖。

- **依赖清单修正**
  - `requirements.txt`：新增 `numpy`、`customtkinter`。
  - 所有依赖按运行场景分组并固定 major 版本：核心 / CLI、视觉处理、图形界面。
  - 新增 README 说明：不同运行模式（CLI / GUI / vision-only）所需依赖组。

- **图像上送安全化（`src/ai_brain.py`）**
  - 发往 LLM 的截图统一先缩放（长边 ≤ 1280px）并压缩为 JPEG（质量 85），避免 base64 请求体过大。
  - Gemini 路径优先调用 `client.files.upload` 上传图片，仅传递文件 URI；上传失败时自动回退到内联 bytes。
  - OpenAI 兼容路径使用 `image_url` + JPEG base64 data URL，并保留 `response_format` 自动降级逻辑。
  - 明确按 SDK 异常类型捕获，避免裸 `except Exception` 吞掉错误。

- **异常处理收紧**
  - `src/main_versaios.py`：串口相关异常捕获 `serial.SerialException` / `PermissionError` / `OSError`，不再吞掉无关错误。
  - `src/vision_engine.py`：窗口定位与 mss 截图分别捕获 `_WINDOW_ERRORS` / `_MSS_ERRORS`。
  - `src/ai_brain.py`：按 `ConnectionError`、`TimeoutError`、SDK 具体错误分类处理并保留重试逻辑。

- **HID 未校准风险提示**
  - `src/config.py`：新增 `DEFAULT_HID_MAX_X/Y` 常量与 `is_hid_calibrated()` 判断。
  - `gui/calibration_module.py`：若 HID 步数未显式配置，界面显示橙色警告。
  - `src/main_versaios.py`：CLI 启动时若使用默认值，日志输出校准警告。
  - README 校准章节补充风险提示。

- **启动前配置校验**
  - `src/config.py`：识别 `config.example.ini` 复制来的 API Key 占位值，启动前直接提示填写真实 Key。
  - `gui_app.py`：窗口标题版本号同步为 V3.0.1。

- **日志初始化保护**
  - `src/logging_setup.py`：增加进程级 `_setup_done` 标志；调用时先清空已有 handler 再统一格式，避免第三方库提前写入导致格式不一致。

- **系统依赖说明**
  - README 补充：Windows 需安装 Apple Bonjour；`UxPlay/gst_plugins/` 为 GStreamer 插件矩阵，首次运行自动生成 `gst_registry.bin`。

- **项目整洁化**
  - 删除 IDE 配置 `.idea/`、`.vscode/`、所有 `__pycache__`、运行时生成的 `assets/debug_target_result.png`、缓存 `UxPlay/gst_registry.bin`、安装器 `BonjourPSSetup.exe`。
  - 更新 `.gitignore`：忽略 IDE 配置、调试图。

## V3.0（2026-07-24）

- **图形化控制台正式发布**
  - 新增 `gui/` 包，将用户交互拆分为两个阶段：
    - `gui/calibration_module.py`：阶段一（模型配置 + 串口连接 + HID 步数校准 + 配置保存）
    - `gui/control_module.py`：阶段二（启动 UxPlay 接收端 + 启动主控端 + 自然语言指令输入 + 实时日志）
  - 入口统一为 `python gui_app.py`，用户无需再手动进入 `src/` 或 `UxPlay/` 运行任何脚本。

- **测试功能并入 GUI**
  - 在“阶段一”新增“测试硬件点击”按钮，替代 `src/test_hardware.py`。
  - 在“阶段二”新增“测试视觉（截图 + 标红目标）”按钮，替代 `src/test_vision.py`，结果保存为 `assets/debug_target_result.png` 并弹窗预览。

- **移除冗余 CLI 脚本**
  - 删除 `src/calibrate_mouse.py`、`src/test_hardware.py`、`src/test_vision.py`。
  - 核心库（`ai_brain.py`、`vision_engine.py`、`config.py`、`logging_setup.py`）与主控引擎（`main_versaios.py`）继续保留在 `src/`，作为 GUI 后端调用。

- **文档重构**
  - 重写 `README.md`：以 GUI 流程为主线，命令行方式作为备用；修正固件路径、依赖安装目录等不一致之处。

## V2.5

- **投屏接收端与主程序分离**
  - 将投屏/接收端作为独立模块放在 `UxPlay/`，入口为 `UxPlay/main.py`
  - 主控端继续位于 `src/`，入口为 `src/main_versaios.py`
  - 默认投屏窗口名统一为 `VersaiOS_Screen`（与 `UxPlay/main.py` 启动参数一致）

- **多模型提供方支持（统一配置）**
  - `config.ini` 统一使用 `llm_provider/llm_api_key/llm_model/llm_base_url` 配置模型
  - 新增 `openai_compatible` 提供方：可对接 OpenAI 兼容接口（OpenAI/DeepSeek/通义千问兼容/自建兼容网关等，以 `llm_base_url` 为准）
  - 视觉推理层 `VersaiOSAgent` 按 `llm_provider` 路由不同厂商 SDK

- **依赖更新**
  - `requirements.txt` 新增 `openai`（用于 `openai_compatible`）

- **安全性**
  - 不再在仓库内保留 `src/config.ini`，改为仅提供 `src/config.example.ini` 作为模板（运行时使用 `src/config.ini`）
  - `src/config.ini` 已加入 `.gitignore`，避免误提交密钥

## V2.5.1（2026-06-16）

- **配置默认值对齐**
  - `config.py` 新增 `DEFAULT_WINDOW_TITLE = "VersaiOS_Screen"`，与 `UxPlay/main.py` 的 `-n` 参数保持一致
  - `get_window_title()`、`config.example.ini`、`vision_engine.py` 默认窗口名由 `Direct3D12 Renderer` 修正为 `VersaiOS_Screen`
  - `get_hid_max_x()` / `get_hid_max_y()` 未配置时的默认值由 `780/1620` 调整为 `140/310`，与 `config.example.ini` 及 V2.0 校准说明一致

- **启动前 LLM 配置校验**
  - 新增 `validate_llm_config()`：启动时检查 API Key、`llm_provider` 合法性，以及 `openai_compatible` 是否配置了 `llm_base_url`
  - `main_versaios.py` 在初始化 Agent 前调用，配置缺失时提前退出并给出明确提示

- **Plan 解析与校验增强**
  - 将 plan 校验逻辑提取为 `validate_plan_dict()`（`ai_brain.py`），`main_versaios.py` 复用同一函数，移除重复校验代码
  - 新增 `_strip_json_fence()`，可解析 LLM 返回的 ` ```json ... ``` ` 围栏格式，降低 JSON 解析失败率

- **文档修正**
  - `README.md` 中窗口名说明与代码默认值保持一致（`VersaiOS_Screen`）

- **兼容性提示**
  - 若本地 `config.ini` 中 `window_title` 仍为旧值 `Direct3D12 Renderer`，请改为 `VersaiOS_Screen`，或删除该项以使用新默认值

## V2.0

- **相对鼠标引擎与动态校准重构**
  - 彻底软硬分离：屏幕尺寸/边界计算逻辑上移到 Python，ESP32 变为纯执行引擎
  - 引入“中线十字定位法”：点击前自动重置到 (0.5, 0.5) 作为相对位移基准，显著提升 iOS 圆角/滑动边缘场景的稳定性
  - 新串口协议：`SET:max_x,max_y` / `REL:dx,dy` / `CLICK:x,y`
  - `src/main_versaios.py`：连接串口后会同步下发边界参数（对应 `SET`）
  - `src/config.py`：`hid_max_x/hid_max_y` 默认值体系切换为相对步数（建议使用 `src/calibrate_mouse.py` 重新测量）
  - `src/calibrate_mouse.py`：重构为“交互式遥控器”，支持 `w/a/s/d + 步数` 并自动累加跨屏总步数

- **配置抽离与安全性提升**
  - 不再在代码中硬编码 LLM Key、串口号、投屏窗口名等敏感或环境相关参数，统一通过 `src/config.py` 读取 `config.ini` / 环境变量
  - 新增 `src/config.example.ini`，引导用户复制为 `src/config.ini` 并填写 `llm_provider`、`llm_api_key`、`llm_model`（以及 `llm_base_url`，如使用 OpenAI 兼容接口）、`com_port`、`window_title`、`hid_max_x`、`hid_max_y`，避免误把私密信息提交到 Git

- **HID 校准与 Prompt 配置统一化**
  - HID 极限步数（`hid_max_x/hid_max_y`）由 `src/calibrate_mouse.py` 校准后写入 `src/config.ini`，主程序通过 `config.get_hid_max_x()` / `get_hid_max_y()` 统一读取，实现多机多型号可配置
  - 高精度 UI 点击的系统 Prompt 已抽离到 `config.get_system_prompt()` 中，如需调整点击策略或语言风格，只需修改该函数（或扩展为从独立 Prompt 文件加载），无需改动业务逻辑代码

## 说明

- `gemini`：使用 `google-genai`
- `openai_compatible`：使用 `openai` SDK + `base_url` 指向你的兼容端点
