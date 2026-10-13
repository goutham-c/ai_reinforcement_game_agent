"""
Curriculum Learning Manager for progressive Mario difficulty challenges.
"""

from typing import Dict, Any


class CurriculumManager:
    STAGE_THRESHOLDS = {
        1: 2000.0,   # Promotion threshold for Stage 1
        2: 4000.0,   # Promotion threshold for Stage 2
        3: 7000.0    # Mastery threshold for Stage 3
    }

    def __init__(self, start_stage: int = 1, auto_advance: bool = True):
        self.current_stage = start_stage
        self.auto_advance = auto_advance
        self.promoted_this_gen = False
        self.highest_stage_unlocked = start_stage

    def check_progression(self, best_fitness: float, level_completed: bool) -> bool:
        """
        Checks if the generation has earned promotion to the next curriculum challenge.
        """
        self.promoted_this_gen = False
        if not self.auto_advance:
            return False

        threshold = self.STAGE_THRESHOLDS.get(self.current_stage, 5000.0)
        if (level_completed or best_fitness >= threshold) and self.current_stage < 3:
            self.current_stage += 1
            self.highest_stage_unlocked = max(self.highest_stage_unlocked, self.current_stage)
            self.promoted_this_gen = True
            print(f"[Curriculum] PROMOTION! AI advanced to Stage {self.current_stage}!")
            return True
        return False

    def cycle_stage(self) -> int:
        self.current_stage = (self.current_stage % 3) + 1
        return self.current_stage
