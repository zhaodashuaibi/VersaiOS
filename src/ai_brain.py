import base64
import io
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

from PIL import Image

from config import (
    get_llm_api_key,
    get_llm_base_url,
    get_llm_model,
    get_llm_provider,
    get_system_prompt,
)

logger = logging.getLogger(__name__)

# 视觉输入统一压缩策略：长边不超过 1280px、JPEG 质量 85。
# 可显著降低请求体大小，同时保留 UI 文字/图标细节。
_MAX_IMAGE_LONG_SIDE = 1280
_JPEG_QUALITY = 85

# 可重试的网络/服务端异常基线
_RETRYABLE_BASE = (ConnectionError, TimeoutError)


def _strip_json_fence(raw_text: str) -> str:
    """去掉 LLM 可能包裹的 ```json ... ``` 围栏。"""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, count=1)
        text = re.sub(r"\s*```$", "", text, count=1)
    return text.strip()


def _compress_image_to_jpeg(img: Image.Image) -> bytes:
    """
    将 PIL Image 缩放到合理尺寸并压缩为 JPEG bytes。
    避免把原始 PNG 直接塞进请求体导致体积过大。
    """
    original_width, original_height = img.size
    long_side = max(original_width, original_height)
    if long_side > _MAX_IMAGE_LONG_SIDE:
        ratio = _MAX_IMAGE_LONG_SIDE / long_side
        new_size = (int(original_width * ratio), int(original_height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        logger.debug("图像已缩放 %s -> %s", (original_width, original_height), new_size)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=_JPEG_QUALITY, optimize=True)
    jpeg_bytes = buf.getvalue()
    logger.debug(
        "图像已压缩为 JPEG: original=%s, jpeg_bytes=%d",
        (original_width, original_height),
        len(jpeg_bytes),
    )
    return jpeg_bytes


def _image_to_data_url(jpeg_bytes: bytes) -> str:
    """将 JPEG bytes 转为 OpenAI 兼容的 data URL。"""
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def validate_plan_dict(obj: Any) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """校验 plan 字典 schema（x_ratio/y_ratio 必填，reason 可选）。"""
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
            except (TypeError, ValueError):
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


def _parse_and_validate_plan(raw_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    LLM 输出 schema（必须）：
    - x_ratio: 0-1 浮点
    - y_ratio: 0-1 浮点
    - reason: 可选字符串
    """
    try:
        obj = json.loads(_strip_json_fence(raw_text))
    except json.JSONDecodeError as e:
        return None, f"json_decode_failed: {e}"

    return validate_plan_dict(obj)


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
        固定使用 OpenAI 兼容接口（openai SDK），端点在 GUI/ini 中通过 llm_base_url 配置。
        """
        self.provider = (provider or get_llm_provider()).strip().lower()
        self.api_key = api_key or get_llm_api_key()
        self.model_name = model_name or get_llm_model()
        self.base_url = base_url or get_llm_base_url()

        if not self.api_key:
            raise ValueError("LLM API Key 未配置（llm_api_key / VERSAIOS_LLM_API_KEY）。")

        logger.info(
            "正在初始化 OpenAI 兼容客户端。model=%s base_url=%s",
            self.model_name,
            self.base_url or "(未设置)",
        )
        try:
            from openai import OpenAI  # type: ignore
            import openai
        except ImportError as e:
            raise RuntimeError(
                "未安装 openai 依赖。请执行：pip install -r requirements.txt"
            ) from e

        if not self.base_url:
            raise ValueError("OpenAI 兼容接口未配置 llm_base_url（请先在 GUI 填写并点击确认）。")

        self._openai_client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self._retryable_errors = _RETRYABLE_BASE + (
            openai.APIConnectionError,
            openai.RateLimitError,
            openai.InternalServerError,
        )

    def analyze_ui_and_plan(
        self, frame_img: Image.Image, user_instruction: str, max_retries: int = 2
    ) -> Optional[Dict[str, Any]]:
        # 把狙击法则和用户的具体目标拼接成最终的 Prompt
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

            except self._retryable_errors as e:
                logger.warning(
                    "LLM 推理遇到可重试异常（attempt=%s/%s provider=%s）：%s",
                    attempt,
                    max_retries + 1,
                    self.provider,
                    e,
                )
            except RuntimeError:
                # 初始化或 SDK 调用参数错误，重试无意义，直接抛出
                raise
            except Exception:
                # 其余未预期异常记录后仍尝试重试，避免单次偶发错误导致任务失败
                logger.exception(
                    "LLM 推理调用异常（attempt=%s/%s provider=%s）。",
                    attempt,
                    max_retries + 1,
                    self.provider,
                )

        logger.error("LLM plan 最终失败，已放弃。provider=%s last_raw=%r", self.provider, last_raw)
        return None

    def _generate_json_text(self, prompt: str, frame_img: Image.Image) -> Optional[str]:
        jpeg_bytes = _compress_image_to_jpeg(frame_img)
        return self._generate_with_openai(prompt, jpeg_bytes)

    def _generate_with_openai(self, prompt: str, jpeg_bytes: bytes) -> Optional[str]:
        import openai

        data_url = _image_to_data_url(jpeg_bytes)

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

        # 某些 OpenAI 兼容实现支持强制 JSON 输出；若不支持则降级重试
        attempts = [
            {**kwargs, "response_format": {"type": "json_object"}},
            kwargs,
        ]

        last_err: Optional[Exception] = None
        for idx, call_kwargs in enumerate(attempts):
            try:
                resp = self._openai_client.chat.completions.create(**call_kwargs)
            except openai.BadRequestError as e:
                # 大概率是 response_format 不被支持，继续第二次尝试
                if idx == 0 and "response_format" in call_kwargs:
                    logger.debug("openai_compatible 端点不支持 response_format，降级重试。error=%s", e)
                    last_err = e
                    continue
                raise
            except (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError):
                # 网络/限流/服务端错误交给上层重试
                raise
            except openai.APIError as e:
                logger.error("OpenAI 兼容端点返回错误：%s", e)
                raise

            try:
                content = resp.choices[0].message.content
            except (AttributeError, IndexError) as e:
                logger.warning("OpenAI 返回结构异常：%s", e)
                content = None
            return content

        if last_err is not None:
            raise last_err
        return None
