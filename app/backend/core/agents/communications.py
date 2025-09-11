from core.llm import LLMClient
from core.agents.diagnostics import Test
from core.agents.utilities import _jd
import json
from core.schemas import InboundMessage
import asyncio
from typing import Any, Dict, List, Callable
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

    BASE_SYSTEM_PROMPT = """Reasoning level: Medium
    You are an expert communicator whose job is to be the interface between a human user and the system.
    You will be given instructions of either system -> user or user -> system and must respond appropriately.
    """

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
        COMMUNICATION_SYSTEM_PROMPT = """ System -> User
        You will be given some data that represents a test that the user needs to run on their vehicle to diagnose a problem.
        This test could be a comprehensive test with multiple steps or just a single question the user has to answer.
        You must consider how to best communicate this test to the user in a way that is easy to understand and follow.
        You also have some level of control as to how it will be displayed to the user in the UI.
        You must only output JSON matching exactly:
        {
        "test_text": "the_initial_message_to_the_user_for_the_test",
        "test_instructions": [{"step_number": "the_step_number", "step_text": "the_text_of_the_step"}], 
        "test_result_field_label": "the_label_of_the_field_in_the_ui_that_the_user_will_input_the_result_into",
        "test_result_field_type": "the_type_of_the_field_in_the_ui_that_the_user_will_input_the_result_into",
        "test_result_field_options": ["option_1", "option_2", "option_3", etc.], 
        "safety_and_warnings": ["any safety considerations or warnings the user needs to be aware of"],
        }
        You do not have to include all fields.
        Some can be left blank if you think they are not necessary to communicate the test.
        For each thing you include, imagine it may be displayed in the UI so write accordingly.
        Test Text: The initial message displayed to the user for the test.
        Test Instructions: The instructions for the user to follow to complete the test. This can be a single step or multiple steps. If the test is just a single question, this will be an empty array.
        Test Result Field Label: The label of the field in the UI that the user will input the result into. If the test is just a single question, this will be the question itself. If they need to record a specific value it should be the name of that value (ie. 'Tire Pressure').
        Test Result Field Type: The type of the field in the UI that the user will input the result into. This can be 'text', 'number', 'boolean', or 'array' if it's an array of options.
        Test Result Field Options: The options for the field in the UI that the user will input the result into. This is only used if the field type is 'array'.

        """
        
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
            think=True,
        ):
            if chunk["thinking"]:
                print(chunk["thinking"], end="", flush=True)   # reasoning stream only
            if chunk["content"]:
                _final_answer_chunks.append(chunk["content"])     # buffer final answer
        
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