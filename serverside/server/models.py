from pydantic import BaseModel

class FreeformSummary(BaseModel):
    summary: str  # format: "med1, med2, ... : new_med"

class SummaryRequest(BaseModel):
    file_path: str  # Path to FHIR JSON file

class MatchRequest(BaseModel):
    file_path: str
    new_medication: str