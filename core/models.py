from pydantic import BaseModel

class EvalJob(BaseModel):
    input: str
    prediction: str
    reference: str
    grader_name: str = "exact_match"
    model_name: str = "unknown"
