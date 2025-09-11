import typing, json
import re
import uuid
from typing import Any, Dict, List, Protocol, TypedDict, Optional, Tuple
from core.llm import LLMClient
from core.agents.utilities import _jd, parse_llm_json



# ----- TYPES -----
class DiagnosisProbability(TypedDict):
    diagnosis: str
    probability: float


class Test(TypedDict):
    id: str
    name: str #human readable name
    description: str #human readable description (instructions, etc.)
    rationale: str #rationale for the test (why it is important and what it might tell you)
    outcomes: Any #any type, depends on the test
    result: Any



# ----- AGENT BASE CLASS -----
"""
DiagnosticsAgent Base Class
The role of the diagnostics agent is to come up with tests to run and then update the probabilities.
Inputs: diagnosis_probabilities, tests_log
Ouputs: diagnosis_probabilities_updated, next_test
"""
class DiagnosticsAgent:
    async def run(
        self, 
        diagnosis_probabilities: List[DiagnosisProbability | None], 
        tests_log: List[Test]
    ) -> Tuple[List[DiagnosisProbability], str]:
        pass



# ----- AGENT IMPLEMENTATIONS -----
"""
LLM Diagnostics Agent
"""
class LLMDiagnosticsAgent(DiagnosticsAgent):
    SYSTEM_PROMPT = (
        "You are a vehicle diagnostics agent. Analyze test results and update diagnosis probabilities.\n\n"
        "Output ONLY this JSON:\n"
        "{\n"
        '  "updated_probabilities": [{"issue": "description", "probability": number}],\n'
        '  "next_test": {"name": "test_name", "description": "what to do", "rationale": "why important", "outcomes": {"type": "string|number|boolean|array|object", "outcome_data": "options"}}\n'
        "}\n\n"
        "Rules:\n"
        "- Update probabilities: strong support ×2.0, some support ×1.2, neutral ×1.0, some contradiction ×0.8, strong contradiction ×0.5\n"
        "- Don't normalize probabilities\n"
        "- Choose next test that reveals most info with least effort\n"
        "- Output only JSON, no extra text\n"
    )

    def __init__(self, llm_client: LLMClient):
        self.client = llm_client

    async def run(
        self, 
        diagnosis_probabilities: List[DiagnosisProbability | None], 
        tests_log: List[Test]
    ) -> Tuple[List[DiagnosisProbability], Test]:

        user_prompt = (
            "Most recent test result: {test_result}\n"
            "Current hypothesis probabilities: {diagnosis_probabilities}\n"
            "Prior log of all previous tests: {tests_log}\n"
        )

        # Separate most recent test from prior log
        most_recent_test = tests_log[-1] if tests_log else {}
        prior_tests_log = tests_log[:-1] if tests_log else []

        user_prompt = user_prompt.format(
            test_result=_jd(most_recent_test),
            diagnosis_probabilities=_jd(diagnosis_probabilities),
            tests_log=_jd(prior_tests_log)
        )

        llm_messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Stream response, buffer final answer
        _final_answer_chunks: List[str] = []
        async for chunk in self.client.chat(
            messages=llm_messages,
            think=False,  # Disable verbose reasoning
        ):
            if chunk["content"]:
                _final_answer_chunks.append(chunk["content"])

        # Join buffered content and store for later use
        self.last_raw_output = "".join(_final_answer_chunks)
        result = parse_llm_json(self.last_raw_output)

        diagnosis_probabilities_updated = result["updated_probabilities"]
        next_test = result["next_test"]
        next_test["result"] = None #ensure the result is None until the user runs the test

        return diagnosis_probabilities_updated, next_test

        









