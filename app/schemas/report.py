from pydantic import BaseModel
from typing import List, Dict, Any


class StageSchema(BaseModel):
    stage: str
    replicas: List[str]


class MistakeSchema(BaseModel):
    type: str
    description: str


class RecommendationSchema(BaseModel):
    problem: str
    reason: str
    recommendation: str


class ReportSchema(BaseModel):
    summary: Dict[str, Any]
    dialog_stages: List[StageSchema]
    script_analysis: Dict[str, Any]
    mistakes: List[MistakeSchema]
    recommendations: List[RecommendationSchema]


class UploadCallResponse(BaseModel):
    call_id: str
    filename: str
    transcript: str
    report: ReportSchema
    report_path: str
    status: str