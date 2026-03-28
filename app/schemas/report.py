from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SummarySchema(BaseModel):
    short_summary: str
    result: str

class StageSchema(BaseModel):
    stage: str
    found: bool
    replicas: List[str]

class ScriptAnalysisSchema(BaseModel):
    followed_score: int
    missing_stages: List[str]
    violations: List[str]
    comment: str

class MistakeSchema(BaseModel):
    type: str
    quote: Optional[str] = ""
    description: str

class RecommendationSchema(BaseModel):
    type: str
    category: str
    text: str
    zone_of_growth: str
    why_important: str
    what_to_improve: str

class MetaSchema(BaseModel):
    main_errors: List[str]
    training_focus: List[str]
    raw_score: int

class ReportSchema(BaseModel):
    summary: SummarySchema
    dialog_stages: List[StageSchema]
    script_analysis: ScriptAnalysisSchema
    mistakes: List[MistakeSchema]
    recommendations: List[RecommendationSchema]
    meta: MetaSchema

class UploadCallResponse(BaseModel):
    call_id: str
    filename: str
    transcript: str
    role_transcript: Optional[str] = None
    report: ReportSchema
    report_path: str
    status: str