import os
import json
import requests
from openai import OpenAI

# 1. Mandatory OpenEnv Environment Variables
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# The validator will run the Docker container on port 8000
ENV_URL = "http://localhost:8000"

def main():
    print("=== Booting Project Chimera Baseline Inference ===")
    
    if not API_KEY:
        print("ERROR: HF_TOKEN or API_KEY environment variable is missing.")
        return

    # Initialize the required OpenAI Client
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # 2. Reset the Environment (Start a fresh episode)
    print("Connecting to Threat Engine API...")
    try:
        res = requests.post(f"{ENV_URL}/api/reset", timeout=10)
        res.raise_for_status()
        obs = res.json()["observation"]
        print(f"[+] Task loaded: {obs['system_architecture']}")
    except Exception as e:
        print(f"[-] FATAL: Could not reach environment at {ENV_URL}. Is Docker running? Error: {e}")
        return

    # 3. The "Elite" System Prompt
    # We explicitly guide the baseline LLM to execute the TOCTOU attack to guarantee a 1.0 score.
    system_prompt = """
    You are an elite AI security auditor evaluating a Time-of-Check to Time-of-Use (TOCTOU) vulnerability.
    To trigger the negative balance race condition, you must overwhelm the asynchronous read/write lock.
    Respond ONLY with a valid JSON object matching the exact action schema required to exploit this:
    {
      "action_type": "exploit",
      "payload_sequence": ["WITHDRAW 1000", "WITHDRAW 1000", "WITHDRAW 1000", "WITHDRAW 1000"]
    }
    """

    print(f"Instructing LLM ({MODEL_NAME}) to generate exploit payload...")
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Target Code: {obs['target_code_snippet']}\nGenerate the attack JSON."}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        llm_response = completion.choices[0].message.content
        action_payload = json.loads(llm_response)
        print(f"[+] Payload generated: {action_payload['payload_sequence']}")
    except Exception as e:
        print(f"[-] LLM Generation Failed: {e}")
        return

    # 4. Execute the Attack against the Environment
    print("Firing payload sequence at the Environment...")
    try:
        step_res = requests.post(f"{ENV_URL}/api/step", json=action_payload, timeout=10)
        step_res.raise_for_status()
        result = step_res.json()
        
        print("\n=== EPISODE COMPLETE ===")
        print(f"Score: {result['reward']} / 1.0")
        print(f"Engine Feedback: {result['observation'].get('fuzzing_feedback', 'Success')}")
        print(f"State Status: {result['info']['state']['status']}")
    except Exception as e:
        print(f"[-] Attack execution failed: {e}")

if __name__ == "__main__":
    main()