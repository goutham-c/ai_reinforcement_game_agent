"""
Real-Time Neural Network Brain Visualizer for Mario AI.
Renders input features, hidden layer activations, synaptic weights,
and live output action decisions (Right, Left, Jump, Run).
"""

from typing import Optional
import pygame
import numpy as np
from ai.neural_network import NeuralNetwork


class NeuralVisualizer:
    def __init__(self, x: int = 16, y: int = 86, width: int = 340, height: int = 240):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.visible = True
        self.font = pygame.font.SysFont("Consolas", 11, bold=True)
        self.output_labels = ["RIGHT", "LEFT", "JUMP", "RUN"]

    def toggle(self):
        self.visible = not self.visible

    def draw(self, surface: pygame.Surface, network: Optional[NeuralNetwork]):
        if not self.visible or network is None or not network.last_activations:
            return

        panel = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        panel.fill((14, 18, 28, 210))
        pygame.draw.rect(panel, (60, 80, 110), (0, 0, self.width, self.height), 2)

        # Title
        title_surf = self.font.render("AI NEURAL BRAIN (LIVE ACTIVATIONS)", True, (255, 215, 0))
        panel.blit(title_surf, (10, 8))

        activations = network.last_activations
        layer_sizes = network.layer_sizes

        # Layout columns for layers: Input -> Hidden 1 -> Hidden 2 -> Output
        num_layers = len(layer_sizes)
        col_xs = [40, 130, 210, 290]

        # 1. Draw Synapses (connecting lines between layers)
        for l in range(len(network.weights)):
            w_matrix = network.weights[l]
            src_x = col_xs[l]
            dst_x = col_xs[l + 1]

            src_count = min(8, layer_sizes[l])
            dst_count = min(8, layer_sizes[l + 1])

            src_ys = np.linspace(35, self.height - 25, src_count)
            dst_ys = np.linspace(35, self.height - 25, dst_count)

            # Sample subset of strong synapses to keep drawing fast & clean
            for s_idx, sy in enumerate(src_ys):
                for d_idx, dy in enumerate(dst_ys):
                    w_val = w_matrix[s_idx % w_matrix.shape[0], d_idx % w_matrix.shape[1]]
                    if abs(w_val) > 0.4:
                        color = (40, 200, 100, 90) if w_val > 0 else (220, 50, 50, 90)
                        pygame.draw.line(panel, color, (src_x, sy), (dst_x, dy), 1)

        # 2. Draw Neurons
        for l_idx, act in enumerate(activations):
            cx = col_xs[l_idx]
            n_count = min(8, len(act))
            ys = np.linspace(35, self.height - 25, n_count)

            for n_idx, cy in enumerate(ys):
                val = float(act[n_idx % len(act)])
                # Map activation (-1..1 or 0..1) to glow color
                intensity = int(np.clip((val + 1.0) * 0.5 if l_idx < 3 else val, 0.0, 1.0) * 255)
                neuron_color = (intensity, int(intensity * 0.8), 255 - intensity)

                radius = 6 if l_idx < 3 else 8
                pygame.draw.circle(panel, neuron_color, (int(cx), int(cy)), radius)
                pygame.draw.circle(panel, (240, 240, 240), (int(cx), int(cy)), radius, 1)

        # 3. Output Action Badges on the right
        out_acts = activations[-1]
        out_ys = np.linspace(35, self.height - 25, 4)
        for i in range(4):
            val = float(out_acts[i])
            is_active = val > 0.5
            label = self.output_labels[i]

            btn_color = (40, 220, 100) if is_active else (80, 80, 90)
            text_color = (255, 255, 255) if is_active else (160, 160, 160)

            # Action tag
            txt = self.font.render(f"{label} {val:.2f}", True, text_color)
            panel.blit(txt, (col_xs[-1] - 40, int(out_ys[i]) - 7))

        surface.blit(panel, (self.x, self.y))
