"""
Self-Play & Generational Ghost Racing Framework for Mario AI.
Enables real-time side-by-side races between historical generation champions,
human players, and the evolving population.
"""

from typing import List, Optional, Tuple
from .genome import Genome
from .sensors import SensorSystem
from game.player import MarioPlayer
from game.constants import COLOR_GHOST


class GhostRacer:
    def __init__(self, genome: Genome, label: str, tint: tuple = (100, 200, 255), alpha: int = 140):
        self.genome = genome
        self.label = label
        self.player = MarioPlayer(tint=tint, alpha=alpha)

    def reset(self):
        self.player.reset()

    def step(self, level) -> Tuple[bool, bool, bool, bool]:
        if self.player.is_dead or self.player.won:
            return (False, False, False, False)
        obs = SensorSystem.get_observation(self.player, level)
        act = self.genome.network.get_actions(obs)
        r, l, j, run = act
        self.player.apply_action(r, l, j, run)
        return act


class SelfPlayArena:
    def __init__(self):
        self.ghost_racers: List[GhostRacer] = []
        self.active_duel_mode: bool = False

    def clear(self):
        self.ghost_racers.clear()

    def set_past_champion_ghost(self, champion_genome: Optional[Genome], gen_number: int):
        self.ghost_racers.clear()
        if champion_genome:
            ghost = GhostRacer(
                genome=champion_genome,
                label=f"Ghost: Gen {gen_number}",
                tint=(120, 220, 255),
                alpha=140
            )
            self.ghost_racers.append(ghost)

    def setup_multigen_race(self, champions: List[Tuple[int, Genome]]):
        """
        Sets up a grand generational race (e.g. Gen 0, Gen 5, Gen 10, Gen 25).
        """
        self.ghost_racers.clear()
        colors = [
            (255, 80, 80),    # Red
            (80, 180, 255),   # Cyan
            (100, 255, 100),  # Green
            (255, 215, 0),    # Gold
            (220, 100, 255),  # Purple
        ]
        for idx, (gen_num, genome) in enumerate(champions):
            c = colors[idx % len(colors)]
            ghost = GhostRacer(
                genome=genome,
                label=f"Gen {gen_num}",
                tint=c,
                alpha=220
            )
            self.ghost_racers.append(ghost)

    def reset(self):
        for g in self.ghost_racers:
            g.reset()

    def step(self, level):
        for g in self.ghost_racers:
            g.step(level)

    def get_leaderboard(self) -> List[Tuple[str, float, bool]]:
        """
        Returns list of (label, x_position, is_dead) sorted by x descending.
        """
        board = [(g.label, g.player.x, g.player.is_dead) for g in self.ghost_racers]
        board.sort(key=lambda item: item[1], reverse=True)
        return board
