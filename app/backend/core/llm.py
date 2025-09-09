from __future__ import annotations
from typing import Any, Dict, List, Optional
import asyncio
import httpx
from fastapi import FastAPI
from ollama import AsyncClient
from ollama import chat


# llm parameters (shared across agents)
_client: Optional[httpx.AsyncClient] = None
_base_url: str = "http://localhost:11434"
_model: str = "gpt-oss:20b"
_default_keep_alive: Optional[str | int] = "30m"   # keep model resident after calls

_default_chat_params: Dict[str, Any] = {
    "temperature": 0.7,
    "max_tokens": 4096,
}


"""
LLMClient is the interface for interacting with the LLM.
It can be used to chat with the LLM, warm up the model, and close the connection.
"""
class LLMClient:
    def __init__(
        self,
        base_url: str = _base_url, # ollama base url
        model: str = _model,
        keep_alive: Optional[str | int] = _default_keep_alive,
        timeout: httpx.Timeout | None = None
    ):
        # store basic llm config
        self.base_url = base_url
        self.model = model
        self.keep_alive = keep_alive

        # create ollama client
        self.client = AsyncClient(host=base_url)


    async def chat(
        self,
        messages: List[Dict[str, str]],
        keep_alive: Optional[str | int] = _default_keep_alive,
        think: bool = True,
        chat_params: Dict[str, Any] = _default_chat_params,
    ) -> Dict[str, Any]:
        """
        Send a chat request to the LLM.
        """

        async for part in await self.client.chat(
            model=self.model,
            messages=messages,
            stream=True,
            keep_alive=keep_alive,
            think=think,
        ):
            yield {
                "role": part["message"].get("role", "assistant"),
                "thinking": part["message"].get("thinking"),   # <-- reasoning text (may be None)
                "content": part["message"].get("content"),     # <-- final answer tokens
                "done": part.get("done", False),
            }


    async def warmup(self) -> None:  #ensures the model is pre-loaded
        """Warm up the model"""
        async for part in self.chat(messages=[{"role": "user", "content": "ping"}], keep_alive=self.keep_alive, think=False):
            pass

    async def close(self) -> None:
        """Close the underlying HTTP client (call on app shutdown)."""
        await self.client.aclose()

    

"""
initialise the llm client
"""
async def initialise_llm(app: FastAPI):
    """Background task to initialise connection to LLM"""
    try:
        print("Starting LLM initialization...", flush=True)
        app.state.llm_client = LLMClient(
            base_url="http://localhost:11434",
            model="gpt-oss:20b",
            keep_alive="30m",
            timeout=None
        )
        # Try to warmup but don't block if Ollama is not available
        try:
            await asyncio.wait_for(app.state.llm_client.warmup(), timeout=20)
            app.state.llm_ready = True
            print("LLM initialization completed", flush=True)
        except asyncio.TimeoutError:
            print("LLM warmup timed out - Ollama may not be running", flush=True)
            app.state.llm_ready = False
        except Exception as warmup_error:
            print(f"LLM warmup failed: {warmup_error}", flush=True)
            app.state.llm_ready = False
    except Exception as e:
        print(f"LLM initialization failed: {e}", flush=True)
        app.state.llm_ready = False
