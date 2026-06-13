from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from core.runner import create_dataset, get_datasets, get_dataset, run_experiment, get_experiments

router = APIRouter(prefix="/datasets", tags=["datasets"])

class DatasetItem(BaseModel):
    input: str = ""
    prediction: str
    reference: str
    grader_name: str = "exact_match"
    model_name: str = "unknown"

class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    items: List[DatasetItem] = []

@router.post("")
def create_new_dataset(body: DatasetCreate):
    try:
        result = create_dataset(
            name=body.name,
            description=body.description,
            items=[item.dict() for item in body.items]
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_datasets():
    return get_datasets()

@router.get("/experiments")
def list_experiments():
    return get_experiments()

@router.get("/{dataset_id}")
def get_single_dataset(dataset_id: int):
    result = get_dataset(dataset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result

@router.post("/{dataset_id}/run")
def run_dataset_experiment(dataset_id: int):
    result = run_experiment(dataset_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return result