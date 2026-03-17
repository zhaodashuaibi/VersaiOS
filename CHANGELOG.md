## 更新日志（Changelog）

本项目采用“尽量可读”的更新记录方式：按日期归档，描述对使用者有影响的变化。

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
