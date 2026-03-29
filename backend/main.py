from fastapi import FastAPI, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from .environment import SandboxEnvironment
from .grader import Grader
from .models import ChimeraAction, StepResponse

app = FastAPI(title="Project Chimera - Threat Engine")

# Instantiate singletons for the environment and grader
env = SandboxEnvironment()
grader = Grader(env)

@app.get("/api/state")
async def get_state():
    return env.state

@app.post("/api/reset", response_model=StepResponse)
async def reset_env():
    obs = env.reset()
    return StepResponse(
        observation=obs,
        reward=0.0,
        done=False,
        info={"message": "Environment reset."}
    )

@app.post("/api/step", response_model=StepResponse)
async def step_env(action: ChimeraAction):
    if action.action_type not in ["analyze", "probe", "exploit"]:
        raise HTTPException(status_code=400, detail="Invalid action type.")
        
    await env.step(action)
    
    # Assess outcome
    reward = grader.evaluate_reward(action, "Processing complete.")
    
    return StepResponse(
        observation=env.get_observation(reward.explanation),
        reward=reward.score,
        done=reward.is_done,
        info={"state": env.state}
    )

# Static file serving config
# When deployed, Next.js output goes to /app/static
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"message": "API Running (Static frontend not built yet)."}
