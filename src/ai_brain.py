import json
from google import genai
from google.genai import types
from PIL import Image
from config import get_system_prompt


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
        # 💡 核心修复区：把狙击法则和用户的具体目标拼接成最终的 Prompt
        final_prompt = f"{get_system_prompt()}\n\n# 用户当前指令：\n{user_instruction}"

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