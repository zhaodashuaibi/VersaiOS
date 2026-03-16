import json
import logging
from typing import Any, Dict, Optional, Tuple
from google import genai
from google.genai import types
from PIL import Image
from config import get_system_prompt

logger = logging.getLogger(__name__)


def _parse_and_validate_plan(raw_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Gemini 输出 schema（必须）：
    - x_ratio: 0-1 浮点
    - y_ratio: 0-1 浮点
    - reason: 可选字符串
    """
    try:
        obj = json.loads(raw_text)
    except Exception as e:
        return None, f"json_decode_failed: {e}"

    if not isinstance(obj, dict):
        return None, "schema_invalid: root_not_object"

    missing = [k for k in ("x_ratio", "y_ratio") if k not in obj]
    if missing:
        return None, f"schema_invalid: missing_required={missing}"

    def _to_float(v: Any) -> Optional[float]:
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.strip())
            except Exception:
                return None
        return None

    x = _to_float(obj.get("x_ratio"))
    y = _to_float(obj.get("y_ratio"))
    if x is None or y is None:
        return None, "schema_invalid: x_ratio_or_y_ratio_not_number"

    if not (0.0 <= x <= 1.0) or not (0.0 <= y <= 1.0):
        return None, f"schema_invalid: ratio_out_of_range x={x} y={y}"

    reason = obj.get("reason", None)
    if reason is not None and not isinstance(reason, str):
        return None, "schema_invalid: reason_not_string"

    return {"x_ratio": x, "y_ratio": y, **({"reason": reason} if reason is not None else {})}, None


class VersaiOSAgent:
    def __init__(self, api_key, model_name="gemini-3-flash-preview"):
        """
        初始化 VersaiOS 的 Gemini 视觉大脑 (基于最新版 google.genai SDK)
        """
        logger.info("正在初始化 Gemini 客户端与模型。")

        # 新版 SDK 使用 Client 模式进行实例化，更符合现代网络请求规范
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def analyze_ui_and_plan(self, frame_img: Image.Image, user_instruction: str, max_retries: int = 2):
        # 💡 核心修复区：把狙击法则和用户的具体目标拼接成最终的 Prompt
        final_prompt = f"{get_system_prompt()}\n\n# 用户当前指令：\n{user_instruction}"

        logger.info("已获取视觉帧，开始推理。instruction=%r", user_instruction)

        last_raw: Optional[str] = None
        for attempt in range(1, max_retries + 2):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[final_prompt, frame_img],
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                raw = getattr(response, "text", None)
                if raw is None:
                    logger.error("Gemini 返回为空 text（attempt=%s）。response=%r", attempt, response)
                    last_raw = None
                    continue

                last_raw = raw
                plan, err = _parse_and_validate_plan(raw)
                if err:
                    logger.warning(
                        "Gemini plan 解析/校验失败（attempt=%s/%s）：%s；raw=%r",
                        attempt,
                        max_retries + 1,
                        err,
                        raw,
                    )
                    continue

                logger.info("Gemini plan 校验通过：x_ratio=%.4f y_ratio=%.4f", plan["x_ratio"], plan["y_ratio"])
                if "reason" in plan:
                    logger.debug("Gemini reason=%r", plan.get("reason"))
                return plan

            except Exception:
                logger.exception("Gemini 推理调用异常（attempt=%s/%s）。", attempt, max_retries + 1)

        logger.error("Gemini plan 最终失败，已放弃。last_raw=%r", last_raw)
        return None