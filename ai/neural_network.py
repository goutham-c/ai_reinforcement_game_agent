"""
Pure NumPy Multi-Layer Perceptron (Neural Network) for Mario RL.
Fast vectorized execution with real-time activation logging for UI visualization.
"""

from typing import List, Dict, Any, Tuple
import numpy as np


class NeuralNetwork:
    def __init__(self, layer_sizes: List[int] = None):
        # Default: 50 inputs -> 32 hidden1 -> 16 hidden2 -> 4 outputs
        self.layer_sizes = layer_sizes if layer_sizes else [50, 32, 16, 4]
        self.weights: List[np.ndarray] = []
        self.biases: List[np.ndarray] = []

        # Real-time activations for visualizer
        self.last_activations: List[np.ndarray] = []

        self._init_random_weights()

    def _init_random_weights(self):
        self.weights = []
        self.biases = []
        for i in range(len(self.layer_sizes) - 1):
            fan_in = self.layer_sizes[i]
            fan_out = self.layer_sizes[i + 1]
            # He / Xavier initialization
            scale = np.sqrt(2.0 / fan_in)
            w = np.random.randn(fan_in, fan_out) * scale
            b = np.zeros(fan_out)
            self.weights.append(w)
            self.biases.append(b)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """
        Forward pass with Tanh hidden layers and Sigmoid outputs.
        x: 1D array of length layer_sizes[0].
        """
        a = np.array(x, dtype=np.float32)
        self.last_activations = [a]

        for i in range(len(self.weights) - 1):
            z = np.dot(a, self.weights[i]) + self.biases[i]
            a = np.tanh(z)
            self.last_activations.append(a)

        # Output layer with Sigmoid for action probabilities / binary switches
        z_out = np.dot(a, self.weights[-1]) + self.biases[-1]
        out = 1.0 / (1.0 + np.exp(-np.clip(z_out, -15.0, 15.0)))
        self.last_activations.append(out)

        return out

    def get_actions(self, x: np.ndarray, threshold: float = 0.5) -> Tuple[bool, bool, bool, bool]:
        """
        Returns boolean actions: (RIGHT, LEFT, JUMP, RUN)
        """
        out = self.forward(x)
        right = bool(out[0] > threshold)
        left = bool(out[1] > threshold)
        jump = bool(out[2] > threshold)
        run = bool(out[3] > threshold)

        # Prevent conflicting inputs (cannot press both right and left simultaneously)
        if right and left:
            if out[0] > out[1]:
                left = False
            else:
                right = False

        return (right, left, jump, run)

    def get_flat_weights(self) -> np.ndarray:
        parts = []
        for w, b in zip(self.weights, self.biases):
            parts.append(w.flatten())
            parts.append(b.flatten())
        return np.concatenate(parts)

    def set_flat_weights(self, flat: np.ndarray):
        idx = 0
        for i in range(len(self.layer_sizes) - 1):
            fan_in = self.layer_sizes[i]
            fan_out = self.layer_sizes[i + 1]
            w_size = fan_in * fan_out
            self.weights[i] = flat[idx : idx + w_size].reshape(fan_in, fan_out)
            idx += w_size

            b_size = fan_out
            self.biases[i] = flat[idx : idx + b_size]
            idx += b_size

    def copy(self) -> 'NeuralNetwork':
        net = NeuralNetwork(self.layer_sizes.copy())
        net.weights = [w.copy() for w in self.weights]
        net.biases = [b.copy() for b in self.biases]
        return net

    def to_dict(self) -> Dict[str, Any]:
        return {
            "layer_sizes": self.layer_sizes,
            "weights": [w.tolist() for w in self.weights],
            "biases": [b.tolist() for b in self.biases],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NeuralNetwork':
        net = cls(data["layer_sizes"])
        net.weights = [np.array(w, dtype=np.float32) for w in data["weights"]]
        net.biases = [np.array(b, dtype=np.float32) for b in data["biases"]]
        return net
