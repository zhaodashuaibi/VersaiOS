import json
import logging
from typing import Any, Dict, Optional, Tuple
from PIL import Image
from config import (
    get_system_prompt,
    get_llm_api_key,
    get_llm_base_url,
    get_llm_model,
    get_llm_provider,
)

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
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        VersaiOS 的视觉大脑：
        - provider=gemini：使用 google-genai
        - provider=openai_compatible：使用 OpenAI 兼容接口（OpenAI/DeepSeek/等）
        """
        self.provider = (provider or get_llm_provider()).strip().lower()
        self.api_key = api_key or get_llm_api_key()
        self.model_name = model_name or get_llm_model()
        self.base_url = base_url or get_llm_base_url()

        if not self.api_key:
            raise ValueError("LLM API Key 未配置（llm_api_key / VERSAIOS_LLM_API_KEY）。")

        if self.provider == "gemini":
            logger.info("正在初始化 Gemini 客户端与模型。model=%s", self.model_name)
            from google import genai  # lazy import

            self._gemini_client = genai.Client(api_key=self.api_key)
            self._openai_client = None
        elif self.provider == "openai_compatible":
            logger.info(
                "正在初始化 OpenAI 兼容客户端。model=%s base_url=%s",
                self.model_name,
                self.base_url or "(default)",
            )
            try:
                from openai import OpenAI  # type: ignore
            except Exception as e:
                raise RuntimeError(
                    "未安装 openai 依赖。请先 pip install -r requirements.txt（已包含 openai）。"
                ) from e

            self._openai_client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            self._gemini_client = None
        else:
            raise ValueError(f"未知 llm_provider={self.provider!r}（支持 gemini / openai_compatible）。")

    def analyze_ui_and_plan(self, frame_img: Image.Image, user_instruction: str, max_retries: int = 2):
        # 💡 核心修复区：把狙击法则和用户的具体目标拼接成最终的 Prompt
        final_prompt = f"{get_system_prompt()}\n\n# 用户当前指令：\n{user_instruction}"

        logger.info("已获取视觉帧，开始推理。instruction=%r", user_instruction)

        last_raw: Optional[str] = None
        for attempt in range(1, max_retries + 2):
            try:
                raw = self._generate_json_text(final_prompt, frame_img)
                if raw is None:
                    logger.error("LLM 返回为空 text（attempt=%s）。provider=%s", attempt, self.provider)
                    last_raw = None
                    continue

                last_raw = raw
                plan, err = _parse_and_validate_plan(raw)
                if err:
                    logger.warning(
                        "LLM plan 解析/校验失败（attempt=%s/%s provider=%s）：%s；raw=%r",
                        attempt,
                        max_retries + 1,
                        self.provider,
                        err,
                        raw,
                    )
                    continue

                logger.info(
                    "LLM plan 校验通过：provider=%s x_ratio=%.4f y_ratio=%.4f",
                    self.provider,
                    plan["x_ratio"],
                    plan["y_ratio"],
                )
                if "reason" in plan:
                    logger.debug("LLM reason=%r", plan.get("reason"))
                return plan

            except Exception:
                logger.exception("LLM 推理调用异常（attempt=%s/%s provider=%s）。", attempt, max_retries + 1, self.provider)

        logger.error("LLM plan 最终失败，已放弃。provider=%s last_raw=%r", self.provider, last_raw)
        return None

    def _generate_json_text(self, prompt: str, frame_img: Image.Image) -> Optional[str]:
        if self.provider == "gemini":
            from google.genai import types  # lazy import

            response = self._gemini_client.models.generate_content(
                model=self.model_name,
                contents=[prompt, frame_img],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )
            return getattr(response, "text", None)

        if self.provider == "openai_compatible":
            # OpenAI 兼容：用 chat.completions，消息里混合 text + image_url
            # 这里把 PIL.Image 转成 data URL，避免写临时文件
            import base64
            import io

            buf = io.BytesIO()
            frame_img.save(buf, format="PNG")
            data_b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            data_url = f"data:image/png;base64,{data_b64}"

            messages = [
                {"role": "system", "content": "你必须严格只输出 JSON 对象，不要输出任何多余文字。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ]

            kwargs: Dict[str, Any] = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.1,
            }

            # 某些 OpenAI 兼容实现支持强制 JSON 输出
            kwargs["response_format"] = {"type": "json_object"}
            try:
                resp = self._openai_client.chat.completions.create(**kwargs)
            except Exception:
                # 兼容部分第三方端点不支持 response_format 参数的情况
                logger.debug("openai_compatible 端点不支持 response_format，降级重试。", exc_info=True)
                kwargs.pop("response_format", None)
                resp = self._openai_client.chat.completions.create(**kwargs)
            content = None
            try:
                content = resp.choices[0].message.content
            except Exception:
                content = None
            return content

        raise ValueError(f"未知 provider={self.provider!r}")