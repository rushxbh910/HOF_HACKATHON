import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId

# Load MongoDB Atlas connection
MONGO_DB_URL = "mongodb+srv://rb5726:Rpb7675910!@cluster0.sb9vbdu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
if not MONGO_DB_URL:
    raise RuntimeError("MONGO_DB_URL environment variable not set")

# Hard-coded database & collection
DB_NAME       = "RUSHXBH910"
COLLECTION    = "GPU_Carbon_Footprints"

# Initialize MongoDB client and collection
mongo_client = MongoClient(MONGO_DB_URL)
db           = mongo_client[DB_NAME]
collection   = db[COLLECTION]

app = FastAPI(
    title="GPU Carbon Footprints API",
    description="Endpoints to fetch GPU energy & carbon metrics",
    version="1.0"
)

# Helper to convert ObjectId to str
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, *args):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

# Pydantic model for response
class Footprint(BaseModel):
    @field_validator("gpu_energy_kwh", mode="before")
    def extract_gpu_energy(cls, v, info):
        if v is None:
            metrics = info.data.get("metrics")
            return metrics.get("gpu_energy_kwh")
        return v

    @field_validator("gpu_carbon_kg", mode="before")
    def extract_gpu_carbon(cls, v, info):
        if v is None:
            metrics = info.data.get("metrics")
            return metrics.get("gpu_carbon_kg")
        return v
    
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    run_id: str
    gpu_energy_kwh: Optional[float] = None
    gpu_carbon_kg: Optional[float] = None
    start_time: Optional[int]
    end_time: Optional[int]
    status: Optional[str]

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

@app.get("/footprints", response_model=List[Footprint])
def list_footprints(limit: int = 100, skip: int = 0):
    """Fetch a list of GPU carbon footprint documents."""
    docs = list(collection.find().skip(skip).limit(limit))
    for doc in docs:
        metrics = doc.get("metrics", {}) or {}
        doc["gpu_energy_kwh"] = metrics.get("gpu_energy_kwh")
        doc["gpu_carbon_kg"] = metrics.get("gpu_carbon_kg")
    #print(collection)
    #print(docs)
    return docs

@app.get("/footprints/{run_id}", response_model=Footprint)
def get_footprint(run_id: str):
    """Fetch a single footprint by run_id."""
    doc = collection.find_one({"run_id": run_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    return doc

@app.get("/")
async def health():
    return {"status": "GPU Carbon Footprints API is up and running!"}
