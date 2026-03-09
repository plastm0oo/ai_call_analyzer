from app.services.llm_analysis_service import run_llm_analysis
from app.agents.structural_agent import StructuralAgent
from app.agents.script_check_agent import ScriptCheckAgent
from app.agents.mistakes_agent import MistakesAgent
from app.agents.coaching_agent import CoachingAgent
from app.agents.report_agent import FinalReportAgent

USE_LLM_PIPELINE = True

def run_analysis_pipeline(call_id: str, transcript: str) -> dict:
    data = {
        "call_id": call_id,
        "transcript": transcript,
        "dialog_structure": [],
        "script_analysis": {},
        "mistakes": [],
        "coaching_recommendations": [],
        "final_report": {}
    }

    agents = [
        StructuralAgent(),
        ScriptCheckAgent(),
        MistakesAgent(),
        CoachingAgent(),
        FinalReportAgent()
    ]

    for agent in agents:
        data = agent.run(data)

    return data

def run_analysis_pipeline(call_id: str, transcript: str) -> dict:
    if USE_LLM_PIPELINE:
        return run_llm_analysis(call_id=call_id, transcript=transcript, debug=True)

    return run_stub_pipeline(call_id=call_id, transcript=transcript)