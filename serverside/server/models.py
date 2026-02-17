from pydantic import BaseModel


class SummaryRequest(BaseModel):
    file_path: str  # Filename of a FHIR JSON file inside data/fhir/


class MatchRequest(BaseModel):
    file_path: str
    new_medication: str