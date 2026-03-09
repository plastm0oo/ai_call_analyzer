from app.agents.structural_agent import StructuralAgent
from app.agents.script_check_agent import ScriptCheckAgent
from app.agents.mistakes_agent import MistakesAgent
from app.agents.coaching_agent import CoachingAgent
from app.agents.report_agent import FinalReportAgent


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