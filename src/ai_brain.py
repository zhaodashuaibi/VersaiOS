import json
from google import genai
from google.genai import types
from PIL import Image


class VersaiOSAgent:
    def __init__(self, api_key, model_name="gemini-3-flash-preview"):
        """
        初始化 VersaiOS 的 Gemini 视觉大脑 (基于最新版 google.genai SDK)
        """
        print(">>> [VersaiOS Brain] 正在初始化全新 Gemini 神经网络架构...")

        # 新版 SDK 使用 Client 模式进行实例化，更符合现代网络请求规范
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def analyze_ui_and_plan(self, frame_img: Image.Image, user_instruction: str):
        SYSTEM_PROMPT_HIGH_PRECISION = """
        # 角色
        你是一个具备像素级高精度视觉推理能力的 iOS UI 自动化点击专家。

        # 任务
        根据用户提供的 iPhone 投屏截图和人类的自然语言指令，找到目标的【绝对精准】的物理点击坐标（x, y 比例）。

        # 核心高精度指令（极其重要，必须严格执行）：

        ## 1. 定义“目标区域”
        一个目标的触摸区域往往比它显示的文字或图标要大。你需要找到整个【可触摸视觉背景】。

        ## 2. 避免“文本基线偏移”误差（核心修复点！）
        AI 常常会输出文字本身的中心坐标，这会导致点击位置偏下。你必须强行向下修正这个习惯：
        - **如果是文字按钮：** 不要点击文字本身的几何中心，也不要点击文字所在的基线。你必须找到包裹这串文字的视觉背景框（通常是一个隐形的矩形触摸块），然后输出这个【背景框】的几何中心。
        - **如果是图标按钮（如返回、设置图标）：** 找到整个图标图案的视觉边界，输出图标本身的几何中心。

        ## 3. 示例校准
        - 指令：“点击 设置”
          - 错误坐标 (AI 常见错误)：在“设置”文字的正中心，或者文字偏下方。
          - 正确坐标 (你需要输出)：在文字周围灰色条状区域的正中心（通常比文字中心偏高一点，使其落在触摸块正中心）。

        - 指令：“点击 微信”图标
          - 错误坐标：在“微信”两个字上。
          - 正确坐标：在那个绿色的、圆角的图标图案正中心。

        # 输出格式
        必须严格输出以下 JSON 格式，不要包含任何多余文字：
        ```json
        {
          "reason": "简述你锁定该目标的几何视觉理由，以及你是如何修正偏差的",
          "x_ratio": 目标背景中心在横轴的 0.00-1.00 比例,
          "y_ratio": 目标背景中心在纵轴的 0.00-1.00 比例
        }
        ```
        """

        # 💡 核心修复区：把狙击法则和用户的具体目标拼接成最终的 Prompt
        final_prompt = f"{SYSTEM_PROMPT_HIGH_PRECISION}\n\n# 用户当前指令：\n{user_instruction}"

        print(f">>> [VersaiOS Brain] 视觉数据已送达，正在思考: '{user_instruction}'")

        try:
            # 新版 SDK 的配置和调用方式
            response = self.client.models.generate_content(
                model=self.model_name,
                # 💡 把拼接好的 final_prompt 喂给大模型
                contents=[final_prompt, frame_img],
                config=types.GenerateContentConfig(
                    temperature=0.1,  # 温度调低，让输出极其稳定精确
                    response_mime_type="application/json"
                )
            )

            # 解析纯 JSON 响应
            plan = json.loads(response.text)
            print(f">>> [VersaiOS Brain] 决策出炉: {plan}")
            return plan

        except Exception as e:
            print(f"❌ Gemini 推理失败，请检查网络或 API Key: {e}")
            return None