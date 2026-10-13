"""
Genome representation for Neuroevolution in Mario AI.
Handles weight mutations, crossover, fitness tracking, and persistence.
"""

from typing import Dict, Any
import numpy as np
from .neural_network import NeuralNetwork


class Genome:
    _next_id = 0

    def __init__(self, network: NeuralNetwork = None, generation: int = 0):
        self.id = Genome._next_id
        Genome._next_id += 1
        self.generation = generation
        self.network = network if network else NeuralNetwork()
        self.fitness: float = 0.0
        self.max_distance: float = 0.0
        self.won: bool = False
        self.death_cause: str = None
        self.enemies_stomped: int = 0
        self.coins: int = 0

    def mutate(self, rate: float = 0.15, sigma: float = 0.25):
        """
        Applies Gaussian noise mutations to network weights and biases.
        """
        flat = self.network.get_flat_weights()
        mask = np.random.rand(len(flat)) < rate

        # Gaussian perturbation
        noise = np.random.randn(len(flat)) * sigma
        flat[mask] += noise[mask]

        # Occasional random reset (2% chance for radical exploratory mutation)
        reset_mask = np.random.rand(len(flat)) < 0.02
        flat[reset_mask] = np.random.randn(np.sum(reset_mask)) * 0.5

        # Clip extreme weights to avoid overflow
        flat = np.clip(flat, -8.0, 8.0)
        self.network.set_flat_weights(flat)

    def crossover(self, partner: 'Genome') -> 'Genome':
        """
        Uniform crossover between two parent genomes.
        """
        w1 = self.network.get_flat_weights()
        w2 = partner.network.get_flat_weights()

        mask = np.random.rand(len(w1)) < 0.5
        child_weights = np.where(mask, w1, w2)

        child_net = self.network.copy()
        child_net.set_flat_weights(child_weights)

        child = Genome(network=child_net, generation=self.generation + 1)
        return child

    def clone(self) -> 'Genome':
        child = Genome(network=self.network.copy(), generation=self.generation)
        child.fitness = self.fitness
        child.max_distance = self.max_distance
        child.won = self.won
        return child

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "generation": self.generation,
            "fitness": float(self.fitness),
            "max_distance": float(self.max_distance),
            "won": self.won,
            "enemies_stomped": self.enemies_stomped,
            "coins": self.coins,
            "network": self.network.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Genome':
        net = NeuralNetwork.from_dict(data["network"])
        genome = cls(network=net, generation=data.get("generation", 0))
        genome.fitness = data.get("fitness", 0.0)
        genome.max_distance = data.get("max_distance", 0.0)
        genome.won = data.get("won", False)
        genome.enemies_stomped = data.get("enemies_stomped", 0)
        genome.coins = data.get("coins", 0)
        return genome
