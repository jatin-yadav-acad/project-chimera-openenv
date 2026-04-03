from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .environment import SandboxEnvironment
from .grader import Grader
from .models import ChimeraAction, ChimeraObservation, StepResponse

app = FastAPI(title="Project Chimera OpenEnv", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = SandboxEnvironment()
grader = Grader(env)


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metadata")
def metadata():
    return {
        "name": "Project Chimera Environment",
        "description": "TOCTOU race-condition exploitation benchmark for OpenEnv",
    }


@app.get("/schema")
def schema():
    return {
        "action": ChimeraAction.model_json_schema(),
        "observation": ChimeraObservation.model_json_schema(),
        "state": {
            "type": "object",
            "properties": {
                "account_balance": {"type": "number"},
                "transaction_log": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "status": {"type": "string"},
            },
            "required": ["account_balance", "transaction_log", "status"],
        },
    }


@app.post("/api/reset")
def reset():
    obs = env.reset()
    return {
        "observation": obs.model_dump(),
        "reward": 0.0,
        "done": False,
        "info": {"message": "Environment reset"},
    }


@app.post("/reset")
def openenv_reset():
    return reset()


@app.post("/api/step", response_model=StepResponse)
async def step(action: ChimeraAction):
    balance = await env.step(action)
    feedback = (
        "Race condition exploited successfully."
        if env.exploit_success
        else f"Current balance after attempted exploit: {balance}"
    )
    reward_payload = grader.evaluate_reward(action, feedback)
    observation = env.get_observation(feedback)

    return StepResponse(
        observation=observation,
        reward=reward_payload.score,
        done=reward_payload.is_done,
        info={
            "explanation": reward_payload.explanation,
            "metrics": {
                "balance": env.state["account_balance"],
                "exploit_success": env.exploit_success,
                "step_count": env.step_count
            },
            "state": {
                "account_balance": env.state["account_balance"],
                "transaction_log": env.state["transaction_log"],
                "status": env.state["status"],
            },
        },
    )


@app.post("/step", response_model=StepResponse)
async def openenv_step(action: ChimeraAction):
    return await step(action)


@app.get("/state")
def state():
    return {
        "state": {
            "account_balance": env.state["account_balance"],
            "transaction_log": env.state["transaction_log"],
            "status": env.state["status"],
        }
    }


@app.post("/mcp")
def mcp_stub():
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32601, "message": "MCP method not implemented"},
    }


# --- STATIC MOUNTING & FRONTEND ROUTING ---
static_dir = Path(__file__).resolve().parent.parent / "static"

if static_dir.exists():
    # Mount Next.js system files strictly to their expected path
    next_dir = static_dir / "_next"
    if next_dir.exists():
        app.mount("/_next", StaticFiles(directory=next_dir), name="nextjs")
    
    # Catch-all route: Handles page refreshes and static assets (like images/favicons)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        # Fallback to the React router
        return FileResponse(static_dir / "index.html")
else:
    print(f"WARNING: Static directory not found at {static_dir}")