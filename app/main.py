import json
import re
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field, ValidationError
from app.agent import generate_forecast
from app.db import log_request_response, fetch_recent_logs
import os

app = FastAPI()

logger = logging.getLogger(__name__)

class ForecastRequest(BaseModel):
    task: str = Field(
        "Analyze the financial reports and transcripts for the last three quarters and provide a qualitative forecast for the upcoming quarter. Your forecast must identify key financial trends (e.g., revenue growth, margin pressure), summarize management's stated outlook, and highlight any significant risks or opportunities mentioned",
    )

@app.post("/forecast")
async def forecast(request: Request, body: ForecastRequest):
    request_id = os.urandom(8).hex()
    try:
        result = generate_forecast(task=body.task)
        cleaned_str = re.sub(r'^```json|```$', '', result.strip(), flags=re.MULTILINE).strip()
        cleaned_result = json.loads(cleaned_str)

        log_request_response(
            request_id=request_id,
            request_data=body.model_dump(),
            response_data=cleaned_result
        )
        return cleaned_result

    except json.JSONDecodeError as jde:
        logger.error(f"JSON parsing failed: {jde}")
        raise HTTPException(status_code=500, detail="Failed to parse forecast output as JSON.")

    except ValidationError as ve:
        logger.error(f"Request validation error: {ve}")
        raise HTTPException(status_code=422, detail=str(ve))

    except Exception as e:
        logger.error(f"Unexpected error in /forecast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/logs")
def get_logs(limit: int = 20):
    logs = fetch_recent_logs(limit=limit)
    return logs