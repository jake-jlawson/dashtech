from typing import List, Dict, Any, Optional
from core.agents.diagnostics import DiagnosisProbability, Test
from core.llm import LLMClient
from core.agents.utilities import _jd, parse_llm_json
from pathlib import Path
from rag.retriever import RagRetriever


class MaintainenceAgent:
    SYSTEM_PROMPT = """
    You are a vehicle maintainence agent who is responsible for providing the user with detailed instructions on how to fix their vehicle.
    You will be given:
    - The description of the initial problem the user was having (including any error codes present).
    - The diagnosis made by the diagnostics agent.
    - The history of tests performed by the diagnostics agent that led to the diagnosis.
    - Additional relevant information for maintainence extracted directly from the vehicle's comprehensive documentation.

    Your goal is to provide the user with a detailed plan for how to fix their vehicle.
    You should return your response in JSON matching exactly:
    {
        "tools": ["the_tools_needed_to_fix_the_vehicle"],
        "parts": ["the_parts_needed_to_fix_the_vehicle"],
        "steps": ["step_1", "step_2", "step_3"],
        "difficulty": a number between 1 and 10,
    }
    - Tools: The tools needed to fix the vehicle (can be empty if no tools are needed).
    - Parts: The parts needed to fix the vehicle (can be empty if no parts are needed).
    - Steps: The steps needed to fix the vehicle (can be empty if no steps are needed).
    - Difficulty: A number between 1 and 10, 1 being a very quick simple fix a child could do and 10 being difficult even for a professional mechanic.
    """
    

    def __init__(self, llm_client: LLMClient):
        self.client = llm_client
        # Reusable RAG retriever (store assumed at app/backend/rag/store)
        self.retriever = RagRetriever(base_url=getattr(llm_client, "base_url", "http://localhost:11434"))

+
    def query_rag(self, problem_description: List[Test], diagnosis: DiagnosisProbability, diagnosis_history: List[Test], k: int = 10) -> List[Dict[str, Any]]:
        issue = diagnosis.get("diagnosis") or ""
        q = (
            "Maintenance/repair procedures, tools, parts, torque specs, cautions for:\n"
            f"Problem context: {problem_description if problem_description else []}"
            f"Diagnosis Made: {issue}\n"
            f"Recent Test History: {diagnosis_history[-3:] if diagnosis_history else []}\n"
        )
        # Prefer maintenance and shared
        return self.retriever.search(q, k=k, namespaces=["maintenance", "shared"], systems=self.match_system(issue), types=None)

    
    
    def match_system(self, diagnosis_description: str) -> Optional[str]:
        """
        Infer the most likely vehicle system from a diagnosis description.
        Returns one of: engine, brakes, fuel, electrical, cab, gearbox,
        clutch, steering, suspension, rear_axle; or None if no clear match.
        """
        if not diagnosis_description:
            return None

        text = diagnosis_description.lower()

        system_to_keywords: Dict[str, List[str]] = {
            "engine": [
                "engine", "coolant", "overheat", "oil pressure", "oil leak", "misfire",
                "compression", "turbo", "egr", "emissions", "camshaft", "crankshaft",
            ],
            "brakes": [
                "brake", "abs", "caliper", "pad", "disc", "rotor", "booster",
                "master cylinder", "brake line", "brake fluid",
            ],
            "fuel": [
                "fuel", "injector", "injection", "pump", "fuel rail", "fuel pressure",
                "filter", "diesel", "common rail",
            ],
            "electrical": [
                "electrical", "wiring", "relay", "fuse", "battery", "alternator",
                "harness", "connector", "short", "ground", "sensor", "ecu", "control unit",
            ],
            "cab": [
                "cab", "door", "window", "mirror", "seat", "hvac", "blower", "heater",
            ],
            "gearbox": [
                "gearbox", "transmission", "gear box", "gearshift", "shifter", "synchromesh",
            ],
            "clutch": [
                "clutch", "pressure plate", "release bearing", "throwout", "flywheel",
            ],
            "steering": [
                "steering", "power steering", "steering rack", "tie rod", "column",
            ],
            "suspension": [
                "suspension", "shock", "damper", "spring", "leaf", "airbag", "strut",
            ],
            "rear_axle": [
                "rear axle", "axle", "differential", "diff", "final drive",
            ],
        }

        best_system: Optional[str] = None
        best_score = 0

        for system, keywords in system_to_keywords.items():
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 1
            if score > best_score:
                best_system = system
                best_score = score

        return best_system if best_score > 0 else None
    
    
    
    
    
    async def run(self, problem_description: List[Test], diagnosis: DiagnosisProbability, diagnosis_history: List[Test]) -> Dict[str, Any]:
        """
        Stream reasoning and return the final parsed maintenance plan JSON.
        """
        # Retrieve relevant documentation from RAG
        relevant_documentation = self.query_rag(problem_description, diagnosis, diagnosis_history)

        user_prompt = (
            "Problem Description: {problem_description}\n"
            "Diagnosis: {diagnosis}\n"
            "Diagnosis History: {diagnosis_history}\n"
            "Relevant Documentation: {relevant_documentation}\n"
        ).format(
            problem_description=_jd(problem_description),
            diagnosis=_jd(diagnosis),
            diagnosis_history=_jd(diagnosis_history),
            relevant_documentation=_jd(relevant_documentation)
        )

        llm_messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        _final_answer_chunks: List[str] = []
        async for chunk in self.client.chat(
            messages=llm_messages,
            think=True,
        ):
            if chunk.get("thinking"):
                print(chunk["thinking"], end="", flush=True)
            if chunk.get("content"):
                _final_answer_chunks.append(chunk["content"])

        self.last_raw_output = "".join(_final_answer_chunks)
        plan = parse_llm_json(self.last_raw_output)
        return plan
        