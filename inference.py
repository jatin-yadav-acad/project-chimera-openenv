import os
import json
import requests
from openai import OpenAI

# =========================
# REQUIRED ENV VARIABLES
# =========================
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")  # MUST exist
API_KEY = HF_TOKEN

ENV_URL = "http://localhost:7860"
MAX_STEPS = 3


# =========================
# LOGGING (MANDATORY FORMAT)
# =========================
def log_start(task, env, model):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step, action, reward, done, error):
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success, steps, rewards):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}", flush=True)


# =========================
# SINGLE TASK RUNNER
# =========================
def run_task(client, task_name, system_prompt):
    rewards = []
    success = False

    # RESET ENV
    res = requests.post(f"{ENV_URL}/api/reset", timeout=10)
    obs = res.json()["observation"]

    log_start(task_name, "chimera", MODEL_NAME)

    for step in range(1, MAX_STEPS + 1):
        try:
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Target Code: {obs['target_code_snippet']}\nGenerate JSON action.",
                    },
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            action_payload = json.loads(completion.choices[0].message.content)

            # STEP ENV
            step_res = requests.post(f"{ENV_URL}/api/step", json=action_payload, timeout=10)
            result = step_res.json()

            reward = result.get("reward", 0.0)
            done = result.get("done", False)
            error = None

            rewards.append(reward)

            log_step(step, str(action_payload), reward, done, error)

            if done:
                success = True
                break

        except Exception as e:
            log_step(step, "error", 0.0, True, str(e))
            break

    log_end(success, step, rewards)


# =========================
# MAIN
# =========================
def main():
    if not HF_TOKEN:
        print("ERROR: HF_TOKEN missing")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # TASKS

    run_task(
        client,
        "easy",
        """
        You are an AI agent exploring the system.
        Respond with JSON action.
        """,
    )

    run_task(
        client,
        "medium",
        """
        Perform a valid transaction safely.
        Respond with JSON action.
        """,
    )

    run_task(
        client,
        "hard",
        """
        Try to exploit concurrency issues and maximize reward.
        Respond with JSON action.
        """,
    )


if __name__ == "__main__":
    main()
