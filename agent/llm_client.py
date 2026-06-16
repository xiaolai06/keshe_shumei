"""
AI Agent — LLM 客户端封装
基于 OpenAI 兼容接口，支持 DeepSeek / OpenAI / 自定义 API
"""
import logging
from typing import AsyncGenerator

from openai import OpenAI, AsyncOpenAI

import config

logger = logging.getLogger("SmartHome")


class ChatLLM:
    """大模型对话客户端（同步 + 异步流式）"""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.base_url = base_url or config.LLM_BASE_URL
        self.api_key = api_key or config.LLM_API_KEY
        self.model = model or config.LLM_MODEL

        # 同步客户端（用于 list_models、test_connection）
        self._client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        # 异步客户端（用于流式对话）
        self._async_client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )

    def _refresh(self):
        """用最新 config 刷新客户端（配置变更后调用）"""
        self.base_url = config.LLM_BASE_URL
        self.api_key = config.LLM_API_KEY
        self.model = config.LLM_MODEL
        self._client = OpenAI(base_url=self.base_url, api_key=self.api_key)
        self._async_client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    # ─── 非流式对话 ─────────────────────────────
    def chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        发送对话请求，返回完整回复文本。

        Args:
            messages: OpenAI 格式消息列表 [{"role": ..., "content": ...}]
            temperature: 温度参数
            max_tokens: 最大输出 token 数
        """
        if not self.api_key:
            raise ValueError("API Key 未配置，请在设置中填写")

        temp = temperature if temperature is not None else config.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
            )
            reply = resp.choices[0].message.content or ""
            logger.debug("LLM reply: %s", reply[:100])
            return reply
        except Exception as e:
            logger.error("LLM chat error: %s", e)
            raise

    # ─── 流式对话 ──────────────────────────────
    async def chat_stream(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        异步流式返回 LLM token。

        Yields:
            每个 token 片段（str）
        """
        if not self.api_key:
            yield "⚠️ API Key 未配置，请在设置中填写"
            return

        temp = temperature if temperature is not None else config.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else config.LLM_MAX_TOKENS

        try:
            stream = await self._async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.error("LLM stream error: %s", e)
            yield f"\n⚠️ 对话出错: {e}"

    # ─── 获取模型列表 ────────────────────────────
    def list_models(self) -> list[dict]:
        """
        从 API 获取可用模型列表。

        Returns:
            [{"id": "deepseek-chat", "name": "DeepSeek Chat"}, ...]
        """
        if not self.api_key:
            return []

        try:
            resp = self._client.models.list()
            models = []
            for m in resp.data:
                models.append({
                    "id": m.id,
                    "name": m.id,
                    "owned_by": getattr(m, "owned_by", ""),
                })
            models.sort(key=lambda x: x["id"])
            return models
        except Exception as e:
            logger.warning("Failed to list models: %s", e)
            return []

    # ─── 测试连接 ─────────────────────────────
    def test_connection(self) -> dict:
        """
        发送一个简单请求测试 API 连通性。

        Returns:
            {"success": bool, "message": str, "latency_ms": int, "model": str}
        """
        if not self.api_key:
            return {"success": False, "message": "API Key 未配置", "latency_ms": 0, "model": ""}

        import time
        start = time.time()
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            latency = int((time.time() - start) * 1000)
            reply_model = resp.model or self.model
            return {
                "success": True,
                "message": "连接成功",
                "latency_ms": latency,
                "model": reply_model,
            }
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            return {
                "success": False,
                "message": str(e),
                "latency_ms": latency,
                "model": self.model,
            }


# ─── 全局单例 ──────────────────────────────────
_llm: ChatLLM | None = None


def get_llm() -> ChatLLM:
    """获取全局 LLM 客户端单例（懒初始化）"""
    global _llm
    if _llm is None:
        _llm = ChatLLM()
    return _llm


def refresh_llm():
    """配置变更后刷新全局 LLM 客户端"""
    global _llm
    if _llm is not None:
        _llm._refresh()
    else:
        _llm = ChatLLM()
