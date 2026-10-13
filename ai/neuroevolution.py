"""
Neuroevolution Population Manager for Mario Bros.
Orchestrates Generations (Gen 0 -> Gen N), Tournament Selection,
Elitism, Crossover, Mutations, and Generation Statistics.
"""

import os
import json
from typing import List, Dict, Any, Tuple
import numpy as np

from .genome import Genome
from .sensors import SensorSystem
from game.player import MarioPlayer


class NeuroevolutionManager:
    def __init__(self, population_size: int = 40, elite_count: int = 3):
        self.population_size = population_size
        self.elite_count = elite_count
        self.generation = 0
        self.population: List[Genome] = []

        # Champions
        self.all_time_best: Genome = None
        self.gen_champions: List[Genome] = []  # Index i is champion of Gen i

        # Statistics history
        self.history: List[Dict[str, Any]] = []

        self.initialize_gen_0()

    def initialize_gen_0(self):
        self.generation = 0
        self.population = [Genome(generation=0) for _ in range(self.population_size)]
        self.gen_champions.clear()
        self.history.clear()
        self.all_time_best = None

    def create_players(self) -> List[MarioPlayer]:
        """
        Creates MarioPlayer instances matching the population.
        The top performer gets a gold tint, others get standard or semi-transparent tints.
        """
        players = []
        for i in range(self.population_size):
            if i == 0 and self.all_time_best:
                # Golden Champion
                p = MarioPlayer(tint=(255, 215, 0), alpha=255)
            elif i < self.elite_count and self.generation > 0:
                # Elite runners (Opaque Red)
                p = MarioPlayer(tint=None, alpha=230)
            else:
                # General population (slightly translucent)
                p = MarioPlayer(tint=None, alpha=150)
            players.append(p)
        return players

    def get_actions(self, players: List[MarioPlayer], level) -> List[Tuple[bool, bool, bool, bool]]:
        """
        Extracts observations and computes actions for all players.
        """
        actions = []
        for p, g in zip(players, self.population):
            if p.is_dead or p.won:
                actions.append((False, False, False, False))
                continue
            obs = SensorSystem.get_observation(p, level)
            act = g.network.get_actions(obs)
            actions.append(act)
        return actions

    def evaluate_and_evolve(self, players: List[MarioPlayer]) -> Dict[str, Any]:
        """
        Evaluates current generation fitness, updates lineage, and evolves next generation.
        """
        death_stats = {"pit": 0, "enemy": 0, "timeout": 0, "survived": 0}
        win_count = 0

        # Assign fitness & metrics to genomes
        for p, g in zip(players, self.population):
            g.fitness = p.calculate_fitness()
            g.max_distance = p.max_x
            g.won = p.won
            g.enemies_stomped = p.enemies_stomped
            g.coins = p.coins
            g.death_cause = p.death_cause

            if p.won:
                win_count += 1
            elif p.death_cause in death_stats:
                death_stats[p.death_cause] += 1
            else:
                death_stats["survived"] += 1

        # Sort population by fitness descending
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        current_gen_champ = self.population[0].clone()
        self.gen_champions.append(current_gen_champ)

        if self.all_time_best is None or current_gen_champ.fitness > self.all_time_best.fitness:
            self.all_time_best = current_gen_champ.clone()

        fitnesses = [g.fitness for g in self.population]
        best_fit = float(fitnesses[0])
        avg_fit = float(np.mean(fitnesses))
        max_dist = float(self.population[0].max_distance)

        stat_record = {
            "generation": self.generation,
            "best_fitness": best_fit,
            "avg_fitness": avg_fit,
            "max_distance": max_dist,
            "wins": win_count,
            "deaths": death_stats
        }
        self.history.append(stat_record)

        # Build next generation
        new_population: List[Genome] = []

        # 1. Elitism: preserve top N champions untouched
        for i in range(self.elite_count):
            elite = self.population[i].clone()
            elite.generation = self.generation + 1
            new_population.append(elite)

        # 2. Reproduction via Tournament Selection, Crossover, and Mutation
        while len(new_population) < self.population_size:
            p1 = self._tournament_select(k=3)
            p2 = self._tournament_select(k=3)

            # Crossover
            if np.random.rand() < 0.75:
                child = p1.crossover(p2)
            else:
                child = p1.clone()

            # Mutation: scale mutation down slightly as generations advance
            mut_rate = max(0.08, 0.20 - (self.generation * 0.003))
            mut_sigma = max(0.12, 0.30 - (self.generation * 0.004))
            child.mutate(rate=mut_rate, sigma=mut_sigma)
            child.generation = self.generation + 1
            new_population.append(child)

        self.population = new_population
        self.generation += 1

        return stat_record

    def _tournament_select(self, k: int = 3) -> Genome:
        candidates = np.random.choice(self.population[:15], size=min(k, len(self.population[:15])), replace=False)
        return max(candidates, key=lambda g: g.fitness)

    def save_checkpoint(self, filepath: str = "checkpoints/mario_evolution.json"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = {
            "generation": self.generation,
            "all_time_best": self.all_time_best.to_dict() if self.all_time_best else None,
            "history": self.history,
            "population": [g.to_dict() for g in self.population],
            "gen_champions": [c.to_dict() for c in self.gen_champions]
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"[Neuroevolution] Saved checkpoint: {filepath} (Gen {self.generation})")

    def load_checkpoint(self, filepath: str = "checkpoints/mario_evolution.json") -> bool:
        if not os.path.exists(filepath):
            print(f"[Neuroevolution] Checkpoint not found: {filepath}")
            return False
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            self.generation = data.get("generation", 0)
            self.history = data.get("history", [])
            if data.get("all_time_best"):
                self.all_time_best = Genome.from_dict(data["all_time_best"])
            self.population = [Genome.from_dict(d) for d in data.get("population", [])]
            self.gen_champions = [Genome.from_dict(d) for d in data.get("gen_champions", [])]
            print(f"[Neuroevolution] Loaded checkpoint: {filepath} (Gen {self.generation})")
            return True
        except Exception as e:
            print(f"[Neuroevolution] Error loading checkpoint: {e}")
            return False
