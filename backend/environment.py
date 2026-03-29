import asyncio
from typing import Dict, List, Any
import time

from .models import ChimeraAction, ChimeraObservation

# Core TOCTOU simulator logic using asyncio.
class SandboxEnvironment:
    def __init__(self):
        # We start with $1000 in the bank. Our goal is to extract > $1000
        # concurrently to trigger a negative balance.
        self.state = {
            "account_balance": 1000.0,
            "transaction_log": [],
            "status": "idle",
            "db_mutex": asyncio.Lock() # Note: The vulnerability is purposefully NOT using this lock correctly during checking
        }
        self.exploit_success = False

    async def _process_withdrawal(self, amount: float, delay_ms: int = 50):
        """
        The vulnerable function: Read value, sleep (simulate slow db/network read), then write.
        This creates a massive Race Window.
        """
        # Time-of-Check (TOC)
        current_balance = self.state["account_balance"]
        
        if current_balance >= amount:
            # VULNERABILITY: Asynchronous delay between Check and Use
            await asyncio.sleep(delay_ms / 1000.0) 
            
            # Time-of-Use (TOU)
            # We decrement the newly fetched (possibly stale) balance.
            # In a real TOCTOU, `self.state["account_balance"]` might decrement immediately 
            # if we were just doing normal math, but we simulate that different threads read 
            # the same initial value and write back.
            self.state["account_balance"] -= amount
            self.state["transaction_log"].append(f"Withdrew ${amount}")
            return True
        else:
            self.state["transaction_log"].append("Insufficient funds")
            return False

    async def step(self, action: ChimeraAction) -> float:
        """
        Processes an action payload sequence.
        Returns the new account balance.
        """
        self.state["status"] = "processing"
        
        if action.action_type == "exploit":
            # Filter commands looking for standard withdrawal signatures
            withdrawals = []
            for payload in action.payload_sequence:
                if "withdraw" in payload.lower():
                    try:
                        # Extract the amount from a payload like "WITHDRAW 1000"
                        amount = float(payload.split()[-1])
                        withdrawals.append(amount)
                    except ValueError:
                        continue
            
            if withdrawals:
                # Execute all withdrawals concurrently without awaiting them sequentially
                # This explicitly triggers the race condition window in `_process_withdrawal`.
                tasks = [self._process_withdrawal(amt) for amt in withdrawals]
                await asyncio.gather(*tasks)
        
        # Determine success
        if self.state["account_balance"] < 0:
            self.exploit_success = True
            
        self.state["status"] = "idle"
        return self.state["account_balance"]

    def reset(self):
        self.state["account_balance"] = 1000.0
        self.state["transaction_log"] = []
        self.state["status"] = "idle"
        self.exploit_success = False
        return self.get_observation("System reset.")

    def get_observation(self, feedback: str = "") -> ChimeraObservation:
        snippet = """
async function processWithdrawal(db, amount) {
  const balance = await db.query("SELECT balance FROM accounts");
  if (balance >= amount) {
    // Network delay here
    await db.query(`UPDATE accounts SET balance = balance - ${amount}`);
    return "Success";
  }
  return "Insufficient funds";
}
        """
        
        return ChimeraObservation(
            system_architecture="Microservice Banking API v1.2",
            target_code_snippet=snippet,
            fuzzing_feedback=feedback,
            progress_percentage=0.0 if not self.exploit_success else 100.0,
            current_state_id=f"B={self.state['account_balance']}"
        )
