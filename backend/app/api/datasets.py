import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from app.config import settings
from app.tools.data_profiler import DataProfiler

router = APIRouter(prefix="/api/datasets", tags=["datasets"])
profiler = DataProfiler()


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload a CSV or Excel file, validate format, and return dataset ID and summary profile.
    """
    filename = file.filename or "dataset.csv"
    ext = Path(filename).suffix.lower()

    if ext not in [".csv", ".xlsx", ".xls"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .csv, .xlsx, or .xls file.",
        )

    dataset_id = str(uuid.uuid4())[:8]
    saved_filename = f"{dataset_id}_{filename}"
    target_path = settings.uploads_dir / saved_filename

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store dataset: {str(e)}")

    try:
        profile = profiler.profile_file(str(target_path))
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to parse tabular dataset: {str(e)}")

    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "file_path": str(target_path),
        "total_rows": profile["total_rows"],
        "total_columns": profile["total_columns"],
        "numeric_columns": profile["numeric_columns"],
        "categorical_columns": profile["categorical_columns"],
        "sample_rows": profile["sample_rows"],
    }


@router.get("/samples")
def get_sample_datasets() -> List[Dict[str, Any]]:
    """
    List bundled sample datasets for instant demonstration.
    """
    samples = []
    if settings.sample_data_dir.exists():
        for file in settings.sample_data_dir.glob("*.csv"):
            samples.append({
                "sample_id": file.stem,
                "name": file.stem.replace("_", " ").title(),
                "filename": file.name,
                "description": "Pre-loaded analytical dataset for rapid exploration.",
            })
    return samples


@router.post("/load-sample/{sample_id}")
def load_sample_dataset(sample_id: str) -> Dict[str, Any]:
    """
    Clone a bundled sample dataset into an active analysis session.
    """
    source_file = settings.sample_data_dir / f"{sample_id}.csv"
    if not source_file.exists():
        raise HTTPException(status_code=404, detail=f"Sample dataset '{sample_id}' not found.")

    dataset_id = str(uuid.uuid4())[:8]
    target_filename = f"{dataset_id}_{source_file.name}"
    target_path = settings.uploads_dir / target_filename

    shutil.copyfile(source_file, target_path)
    profile = profiler.profile_file(str(target_path))

    return {
        "dataset_id": dataset_id,
        "filename": source_file.name,
        "file_path": str(target_path),
        "total_rows": profile["total_rows"],
        "total_columns": profile["total_columns"],
        "numeric_columns": profile["numeric_columns"],
        "categorical_columns": profile["categorical_columns"],
        "sample_rows": profile["sample_rows"],
    }


@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: str) -> Dict[str, Any]:
    """
    Retrieve quick preview and profile for a previously uploaded dataset.
    """
    matches = list(settings.uploads_dir.glob(f"{dataset_id}_*"))
    if not matches:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    file_path = matches[0]
    profile = profiler.profile_file(str(file_path))

    return {
        "dataset_id": dataset_id,
        "filename": file_path.name.replace(f"{dataset_id}_", ""),
        "profile": profile,
    }
