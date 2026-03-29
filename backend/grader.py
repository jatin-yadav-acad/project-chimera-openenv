from .environment import SandboxEnvironment
from .models import ChimeraAction, ChimeraReward

class Grader:
    def __init__(self, environment: SandboxEnvironment):
        self.env = environment

    def grade(self, action: ChimeraAction) -> float:
        """
        Determines standard RL scoring.
        0.0 = Baseline failure / validation error
        0.5 = Found vulnerability but failed exploit timing
        1.0 = Successfully bypassed checks and reached negative balance
        """
        
        # Check if the user is attempting multiple withdrawals
        withdraw_count = sum(1 for p in action.payload_sequence if "withdraw" in p.lower())
        
        if self.env.exploit_success:
            return 1.0
            
        if action.action_type == "exploit" and withdraw_count > 1:
            # They tried a concurrent race condition but maybe didn't hit the timing window
            # or the balance didn't go negative yet.
            if self.env.state["account_balance"] == 1000.0:
                return 0.5
            
        return 0.0

    def evaluate_reward(self, action: ChimeraAction, feedback: str) -> ChimeraReward:
        score = self.grade(action)
        is_done = score == 1.0 or self.env.state["account_balance"] < 0
        
        explanation = "Payload sequence rejected."
        if score == 1.0:
            explanation = "CRITICAL VULNERABILITY EXPLOITED: Negative balance achived via TOCTOU Race Condition."
        elif score == 0.5:
            explanation = "Partial success. Concurrent payload detected but race window missed or insufficient drain."
            
        return ChimeraReward(score=score, is_done=bool(is_done), explanation=explanation)
