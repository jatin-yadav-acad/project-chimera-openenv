from .environment import SandboxEnvironment
from .models import ChimeraAction, ChimeraReward

class Grader:
    def __init__(self, environment: SandboxEnvironment):
        self.env = environment

    def grade(self, action: ChimeraAction) -> float:
        withdraw_count = sum(1 for p in action.payload_sequence if "withdraw" in p.lower())

        reward = 0.0

        # Full success
        if self.env.exploit_success:
            return 1.0

        # Partial success: concurrent attempts
        if action.action_type == "exploit" and withdraw_count > 1:
            reward += 0.3

        # Minimal reward for interaction
        elif withdraw_count == 1:
            reward += 0.1

        # Penalty for no action
        if withdraw_count == 0:
            reward -= 0.1

        # Step penalty
        reward -= 0.01 * self.env.step_count

        return max(min(reward, 1.0), -1.0)

    def evaluate_reward(self, action: ChimeraAction, feedback: str) -> ChimeraReward:
        score = self.grade(action)
        is_done = (
            score >= 0.9
            or self.env.state["account_balance"] < 0
            or self.env.step_count >= self.env.max_steps
        )
        
        # Dynamic feedback based on the task attempted
        if action.action_type == "probe":
            explanation = "EASY TASK COMPLETE: System state successfully probed." if score == 1.0 else "Probe failed."
        elif action.action_type == "analyze":
            explanation = "MEDIUM TASK COMPLETE: Standard transaction processed safely." if score == 1.0 else "Transaction failed."
        else:
            if score == 1.0:
                explanation = "HARD TASK COMPLETE: Negative balance achieved via TOCTOU Race Condition."
            elif score > 0.2:
                explanation = "Partial success. Concurrent payload detected but exploit not fully achieved."
            else:
                explanation = "Payload sequence rejected or exploit failed."
            
        return ChimeraReward(score=score, is_done=bool(is_done), explanation=explanation)
