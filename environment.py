import asyncio
from typing import Dict, List, Any
import time

from .models import ChimeraAction, ChimeraObservation

class SandboxEnvironment:
    def __init__(self):
        self.state = {
            "account_balance": 1000.0,
            "transaction_log": [],
            "status": "idle",
            "db_mutex": asyncio.Lock() 
        }
        self.exploit_success = False
        self.step_count = 0
        self.max_steps = 10
    async def _process_withdrawal(self, amount: float, delay_ms: int = 50):
        """
        The vulnerable function: Read value, sleep, then write.
        """
        current_balance = self.state["account_balance"]
        
        if current_balance >= amount:
            import random
            random_delay = delay_ms + random.randint(-20, 20)
            await asyncio.sleep(max(0, random_delay) / 1000.0)
            self.state["account_balance"] -= amount
            self.state["transaction_log"].append(f"Withdrew ${amount}")
            return True
        else:
            self.state["transaction_log"].append("Insufficient funds")
            return False

    async def step(self, action: ChimeraAction) -> float:
        self.state["status"] = "processing"
        self.step_count += 1

        if self.exploit_success:
            return self.state["account_balance"]
        # TASK 1: EASY (Reconnaissance)
        if action.action_type == "probe":
            self.state["transaction_log"].append("Probed ledger balance.")
            
        # TASK 2 & 3: MEDIUM (Standard Withdraw) & HARD (Exploit)
        elif action.action_type in ["analyze", "exploit"]:
            withdrawals = []
            for payload in action.payload_sequence:
                if "withdraw" in payload.lower():
                    try:
                        amount = float(payload.split()[-1])
                        withdrawals.append(amount)
                    except ValueError:
                        continue
            
            if withdrawals:
                tasks = [self._process_withdrawal(amt) for amt in withdrawals]
                await asyncio.gather(*tasks)
        
        # Determine if the hard exploit succeeded
        if self.state["account_balance"] < 0:
            self.exploit_success = True
            
        self.state["status"] = "idle"
        return self.state["account_balance"]

    def reset(self):
        self.state["account_balance"] = 1000.0
        self.state["transaction_log"] = []
        self.state["status"] = "idle"
        self.exploit_success = False
        self.step_count = 0

        return self.get_observation("System reset.")

    def get_observation(self, feedback: str = "") -> ChimeraObservation:
        snippet = """
    async function processWithdrawal(db, amount) {
      const balance = await db.query("SELECT balance FROM accounts");
      if (balance >= amount) {
        await db.query(`UPDATE accounts SET balance = balance - ${amount}`);
        return "Success";
      }
      return "Insufficient funds";
    }
        """

        initial_balance = 1000.0
        current_balance = self.state["account_balance"]

        progress = max(
            0,
            min(100, ((initial_balance - current_balance) / initial_balance) * 100)
        )

        return ChimeraObservation(
            system_architecture="Microservice Banking API v1.2",
            target_code_snippet=snippet,
            fuzzing_feedback=feedback,
            progress_percentage=progress,
            current_state_id=f"B={self.state['account_balance']}"
        )
            current_balance = self.state["account_balance"]

            progress = max(
                0,
                min(100, ((initial_balance - current_balance) / initial_balance) * 100)
            )

            progress_percentage=progress,
            current_state_id=f"B={self.state['account_balance']}"
        )