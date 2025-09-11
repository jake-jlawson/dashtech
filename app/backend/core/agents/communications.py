from core.llm import LLMClient
from core.agents.diagnostics import Test
from core.agents.utilities import _jd
import json
from core.schemas import InboundMessage
import asyncio
from typing import Any, Dict, List, Callable, Optional, Awaitable
import datetime
from core.agents.utilities import parse_llm_json






class CommunicationsAgent:
    """
    CommunicationsAgent is the middleman between the issue context and the user. It is responsible for all communications with the user.
    There are several types of communications:
    - Asking the diagnosis questions in an easy to understand way.
    - Providing instructions to the user on how and why to complete the tests.
    - Providing updates on the process (what the system is doing, whether a diagnosis has been made, etc.)
    - Controlling the UI to better inform the user (displaying images, videos, etc.)
    - Interpreting the user's responses to the tests and updating the issue context accordingly.
    """

    BASE_SYSTEM_PROMPT = """You are a vehicle diagnostics communicator. Convert technical tests into clear user instructions."""

    def __init__(self, llm_client: LLMClient, issue_id: str, emit: Callable[[str, Dict[str, Any]], None]):
        self.client = llm_client
        self.issue_id = issue_id
        self.emit = emit

    
    async def talk(self, message: str) -> None:
        """
        Talk to the user.
        """
        await self.emit("communications.talk", {"message": message})


    async def communicate_test(self, test: Test) -> None:
        """
        Communicate the test to the user.
        """
        COMMUNICATION_SYSTEM_PROMPT = """Convert vehicle diagnostic tests into clear user instructions.

Output JSON:
{
  "test_text": "initial message to user",
  "test_instructions": [{"step_number": "1", "step_text": "instruction"}],
  "test_result_field_label": "field label",
  "test_result_field_type": "text|number|boolean|array",
  "test_result_field_options": ["option1", "option2"],
  "safety_and_warnings": ["warning1", "warning2"]
}

Fields are optional. Write for UI display."""
        
        user_prompt = (
            "Test: {test}\n"
        ).format(
            test=_jd(test)
        )

        llm_messages = [
            {"role": "system", "content": self.BASE_SYSTEM_PROMPT + "\n" + COMMUNICATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        _final_answer_chunks: List[str] = []
        async for chunk in self.client.chat(
            messages=llm_messages,
            think=False,  # Disable verbose reasoning
        ):
            if chunk["thinking"]:
                # stream thinking to UI
                try:
                    await self.emit("llm.thinking", {"text": chunk["thinking"]})
                except Exception:
                    pass
                print(chunk["thinking"], end="", flush=True)   # reasoning stream only
            if chunk["content"]:
                _final_answer_chunks.append(chunk["content"])
        
        full_test_payload = {
            "test_id": test["id"],
            "test_rationale": test["rationale"],
        } | parse_llm_json("".join(_final_answer_chunks))

        return self.construct_outbound_message("diagnostics.test", full_test_payload, self.issue_id)



    def construct_outbound_message(self, type: str, payload: Dict[str, Any], issue_id: str) -> InboundMessage:
        """
        Construct the outbound message for the test.
        """
        return {
            "type": type,
            "v": 1,
            "issue_id": issue_id,
            "payload": payload,
            "meta": {
                "timestamp": datetime.datetime.utcnow().isoformat(),
            },
        }