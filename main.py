from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from typing import Optional
import time
import uuid
import logging

from agent import run_weekend_planner
from agent import UpstreamLLMTimeoutError
from logging_utils import setup_logging, request_id_ctx

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

# Configure CORS middleware
origins = [
    "*"  # Allow all origins for development. Restrict this in production.
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_logging(request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    start = time.perf_counter()
    try:
        logger.info("request start %s %s", request.method, request.url.path)
        response = await call_next(request)
        dur_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "request end %s %s status=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            getattr(response, "status_code", "?"),
            dur_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_ctx.reset(token)


class AgentRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query for the weekend planner agent")
    verbose: bool = Field(False, description="Return tool/agent logs on server side (debug)")


class AgentResponse(BaseModel):
    output: str
    raw: Optional[dict] = None


@app.post("/agent", response_model=AgentResponse)
async def agent_plan(req: AgentRequest):
    """Run the weekend planner agent for a given user query."""
    try:
        logger.info("agent start verbose=%s query_len=%s", req.verbose, len(req.query or ""))
        start = time.perf_counter()
        # LangChain execution is blocking; run it in a threadpool.
        result = await run_in_threadpool(run_weekend_planner, req.query, verbose=req.verbose)
        dur_ms = (time.perf_counter() - start) * 1000
        logger.info("agent end duration_ms=%.2f", dur_ms)
    except ValueError as e:
        logger.warning("agent validation error: %s", e)
        raise HTTPException(status_code=422, detail=str(e))
    except UpstreamLLMTimeoutError:
        logger.exception("agent upstream LLM timed out")
        raise HTTPException(
            status_code=504,
            detail="Upstream LLM request timed out. Please retry.",
        )
    except Exception:
        logger.exception("agent execution failed")
        raise HTTPException(status_code=500, detail="Agent execution failed")

    output = result.get("output") if isinstance(result, dict) else None
    if not output:
        logger.error("agent returned unexpected response shape: %s", type(result))
        raise HTTPException(status_code=500, detail="Agent returned an unexpected response shape")

    # raw is useful for debugging; keep it off by default.
    return AgentResponse(output=output, raw=result if req.verbose else None)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Weekend Planner Agent!"}
