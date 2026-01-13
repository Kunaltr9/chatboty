from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from pathlib import Path

app = FastAPI(title="Local Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    promptId: Optional[str] = None
    query: Optional[str] = None


def load_mock_events():
    # Try to load the TypeScript mock file as JSON-like data
    # Fallback to embedded list if file not found
    ts_path = Path(__file__).parent / "lib" / "mock-data.ts"
    if ts_path.exists():
        try:
            text = ts_path.read_text(encoding="utf-8")
            # crude extraction of array literal between = [ and ];
            start = text.find("=[")
            if start == -1:
                start = text.find("= [")
            if start != -1:
                arr_text = text[start + text[start:].find("[") :]
                arr_text = arr_text.rsplit("];", 1)[0] + "]"
                # Replace single quotes with double for JSON parse
                arr_text = arr_text.replace("'", '"')
                return json.loads(arr_text)
        except Exception:
            pass

    # fallback
    return [
        {
            "id": "evt-1001",
            "severity": "High",
            "type": "Unauthorized Access Attempt",
            "source": "10.0.0.12",
            "timestamp": "2026-01-12T08:12:34Z",
            "details": "Multiple failed authentication attempts detected for user admin.",
            "status": "Open",
        },
        {
            "id": "evt-1002",
            "severity": "Medium",
            "type": "Suspicious Activity",
            "source": "172.16.5.4",
            "timestamp": "2026-01-12T07:58:01Z",
            "details": "Unrecognized user agent seen performing POST requests to /login.",
            "status": "Investigating",
        },
    ]


@app.post("/query")
async def query_endpoint(req: QueryRequest):
    events = load_mock_events()
    if req.promptId == "security-threats":
        content = "Here are the recent high-severity security threats."
        data = events
    elif req.query:
        content = f"Analyzed query: {req.query}"
        data = events[:3]
    else:
        content = "No query provided"
        data = []

    return {"content": content, "data": data}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
