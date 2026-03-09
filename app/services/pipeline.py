from app.agents.structural_agent import StructuralAgent
from app.agents.script_check_agent import ScriptCheckAgent
from app.agents.mistakes_agent import MistakesAgent
from app.agents.coaching_agent import CoachingAgent
from app.agents.report_agent import FinalReportAgent


def run_analysis_pipeline(transcript: str) -> dict:
    data = {"transcript": transcript}

    agents = [
        StructuralAgent(),
        ScriptCheckAgent(),
        MistakesAgent(),
        CoachingAgent(),
        FinalReportAgent()
    ]

    for agent in agents:
        data = agent.run(data)

    return data["final_report"]