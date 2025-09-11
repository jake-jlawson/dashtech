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
        "You are a vehicle diagnostics agent who is responsible for figuring out the most likely issue with a truck.\n"
        "Given (a) the most recent test result, (b) the current hypothesis probabilities, "
        "and (c) a short prior log of all previous tests, you must output ONLY JSON matching exactly:\n"
        "{\n"
        '  "updated_probabilities": [{"issue": "short description of the issue", "probability": number}],\n'
        '  "next_test": {\n'
        '    "name": "short_name_for_the_test",\n'
        '    "description": "a_description_of_what_the_test_is_and_what_should_be_done",\n'
        '    "rationale": "a_rationale_for_why_this_test_is_important_and_what_it_might_tell_you",\n'
        '    "outcomes": { "type_of_outcome": "either \'string\' or \'number\' or \'boolean\' or \'array\' or \'object\'", "outcome_data": "the_data_of_the_outcome"}\n'
        "  }\n"
        "}\n"
        "\n"
        "Diagnosis Probability Rules:\n"
        "- Update probabilities using a simple multiplicative scoring rule based ONLY on the most recent test:\n"
        "- strong support: ×2.0; some support: ×1.2; neutral: ×1.0; some contradiction: ×0.8; strong contradiction: ×0.5.\n"
        "- Do not normalize. Probabilities are unnormalized scores and do NOT need to sum to 1.\n"
        "- Do not rescale other hypotheses except by applying their own factor from the rule above.\n"
        "- If you add a new hypothesis, initialize its probability to a score based on an estimate of its prior probability based on how often this issue is seen.\n"
        "- Keep scores within a reasonable numeric range; avoid scientific notation.\n"
        "- If you are completely confident of a diagnosis, you may set its probability much larger than others.\n"
        "- Consider all possible issues and assign probabilities to them. If you believe there is a potential diagnosis not in the list, you may add it to the list.\n"
        "\n"
        "Test Rules:\n"
        "- A test just needs to be a single step in the diagnostic process. It can be but does not need to be a specific test that you run on the vehicle. It can also be a question that you ask the user to gain more information.\n"
        "- The outcomes are the possible results of the test. They are either a string, number, boolean, array, or object.\n"
        "- The outcome data is optional and should provide the options or keys if the outcome is an object or array.\n"
        "- The outcomes are the possible results of the test. They are either a string, number, boolean, array, or object.\n"
        "- The next test should be chosen such that it reveals the most new information with the least amount of effort from the user.\n"
        "\n"
        "Output Rules:\n"
        "- Do not include any extra text outside the JSON.\n"
        "- To shorten reasoning time, don't second guess yourself. Once you make a decision, stick with it.\n"
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

        # Stream reasoning, buffer final answer (do not print content as it streams)
        _final_answer_chunks: List[str] = []
        async for chunk in self.client.chat(
            messages=llm_messages,
            think=True,
        ):
            if chunk["thinking"]:
                print(chunk["thinking"], end="", flush=True)   # reasoning stream only
            if chunk["content"]:
                _final_answer_chunks.append(chunk["content"])     # buffer final answer

        # Join buffered content and store for later use
        self.last_raw_output = "".join(_final_answer_chunks)
        result = parse_llm_json(self.last_raw_output)

        diagnosis_probabilities_updated = result["updated_probabilities"]
        next_test = result["next_test"]
        next_test["result"] = None #ensure the result is None until the user runs the test

        return diagnosis_probabilities_updated, next_test

        









