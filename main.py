from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from typing import Optional

from agent import run_weekend_planner

app = FastAPI()


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
        # LangChain execution is blocking; run it in a threadpool.
        result = await run_in_threadpool(run_weekend_planner, req.query, verbose=req.verbose)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}")

    output = result.get("output") if isinstance(result, dict) else None
    if not output:
        raise HTTPException(status_code=500, detail="Agent returned an unexpected response shape")

    # raw is useful for debugging; keep it off by default.
    return AgentResponse(output=output, raw=result if req.verbose else None)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the Weekend Planner Agent!"}
