# api_server.py

import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import httpx
from datetime import datetime
import pprint

logging.basicConfig(level=logging.INFO)

MONGO_DB_URL = os.getenv(
    "MONGO_DB_URL",
    "mongodb+srv://rb5726:Rpb7675910!@cluster0.sb9vbdu.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
if not MONGO_DB_URL:
    raise RuntimeError("MONGO_DB_URL environment variable not set")

DB_NAME = "RUSHXBH910"
COLLECTION = "GPU_Carbon_Footprints"
mongo_client = MongoClient(MONGO_DB_URL)
db = mongo_client[DB_NAME]
collection = db[COLLECTION]

LAMBDA_URL = os.getenv(
    "LAMBDA_URL",
    "https://dle73zvmmwh43abjc7iqlhopb40vglat.lambda-url.us-east-1.on.aws/"
)

app = FastAPI(
    title="GPU Carbon Footprints API",
    description="Endpoints to fetch GPU energy & carbon metrics and send to AWS Lambda",
    version="1.1"
)

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, *args):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid ObjectId")
        return ObjectId(value)

class Footprint(BaseModel):
    @field_validator("gpu_energy_kwh", mode="before")
    def extract_gpu_energy(cls, v, info):
        if v is None:
            metrics = info.data.get("metrics", {})
            return metrics.get("gpu_energy_kwh", 0.0)
        return v

    @field_validator("gpu_carbon_kg", mode="before")
    def extract_gpu_carbon(cls, v, info):
        if v is None:
            metrics = info.data.get("metrics", {})
            return metrics.get("gpu_carbon_kg", 0.0)
        return v

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    run_id: str
    gpu_energy_kwh: Optional[float] = 0.0
    gpu_carbon_kg: Optional[float] = 0.0
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    status: Optional[str] = "unknown"

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}

@app.get("/")
async def health():
    return {"status": "GPU Carbon Footprints API is up and running!"}

@app.get("/footprints", response_model=List[Footprint])
def list_footprints(limit: int = 100, skip: int = 0):
    docs = list(collection.find().skip(skip).limit(limit))
    for doc in docs:
        metrics = doc.get("metrics", {}) or {}
        doc["gpu_energy_kwh"] = metrics.get("gpu_energy_kwh", 0.0)
        doc["gpu_carbon_kg"] = metrics.get("gpu_carbon_kg", 0.0)
    return docs

@app.get("/footprints/{run_id}", response_model=Footprint)
def get_footprint(run_id: str):
    doc = collection.find_one({"run_id": run_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found")
    return doc

def format_doc_for_lambda(doc: dict) -> dict:
    metrics = doc.get("metrics", {}) or {}
    payload = {
        "run_id": doc.get("run_id", "unknown"),
        "gpu_energy_kwh": metrics.get("gpu_energy_kwh", 0.0),
        "gpu_carbon_kg": metrics.get("gpu_carbon_kg", 0.0),
        "start_time": doc.get("start_time"),
        "end_time": doc.get("end_time"),
        "status": doc.get("status", "unknown"),
        "sent_at": datetime.utcnow().isoformat()
    }
    logging.info(f"✅ Prepared Payload for Lambda: {payload}")
    return payload

async def send_to_lambda(data: dict):
    logging.info(f"📦 Sending to Lambda: {data}")
    pprint.pprint(data)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(LAMBDA_URL, json=data)
            response.raise_for_status()
            logging.info("✅ Lambda Response: %s", response.text)
            return response.json()
        except httpx.HTTPError as e:
            error_msg = e.response.text if e.response else str(e)
            logging.error("❌ Lambda Error: %s", error_msg)
            raise HTTPException(status_code=500, detail=f"Lambda Error: {error_msg}")

@app.post("/send/{run_id}")
async def send_footprint_to_lambda(run_id: str):
    doc = collection.find_one({"run_id": run_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Run not found in MongoDB")

    payload = format_doc_for_lambda(doc)
    lambda_response = await send_to_lambda(payload)

    collection.update_one(
        {"run_id": run_id},
        {"$set": {
            "lambda_response": lambda_response,
            "lambda_status": "sent",
            "sent_at": datetime.utcnow()
        }}
    )

    return {
        "message": "Data sent to Lambda and saved to MongoDB.",
        "run_id": run_id,
        "lambda_response": lambda_response
    }