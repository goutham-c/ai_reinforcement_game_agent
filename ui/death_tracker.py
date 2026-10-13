"""
Death Tracker and Danger Heatmap for Mario AI.
Records mortality coordinates and renders visual graveyard markers across the course.
"""

from typing import List, Tuple
import pygame


class DeathTracker:
    def __init__(self, max_markers: int = 150):
        self.markers: List[Tuple[float, float, str]] = []  # (x, y, cause)
        self.max_markers = max_markers
        self.visible = True

    def record_death(self, x: float, y: float, cause: str):
        self.markers.append((x, y, cause))
        if len(self.markers) > self.max_markers:
            self.markers.pop(0)

    def clear(self):
        self.markers.clear()

    def toggle(self):
        self.visible = not self.visible

    def draw(self, surface: pygame.Surface, camera_x: float):
        if not self.visible:
            return

        for mx, my, cause in self.markers:
            draw_x = mx - camera_x
            if -30 <= draw_x <= surface.get_width() + 30:
                draw_y = min(surface.get_height() - 35, max(50, my))

                # Color based on cause
                if cause == "pit":
                    col = (255, 60, 60)   # Red for pits
                elif cause == "enemy":
                    col = (255, 160, 20)  # Orange for enemies
                else:
                    col = (180, 100, 255) # Purple for timeout

                # Draw small 'X' death marker
                pygame.draw.line(surface, col, (draw_x - 4, draw_y - 4), (draw_x + 4, draw_y + 4), 2)
                pygame.draw.line(surface, col, (draw_x + 4, draw_y - 4), (draw_x - 4, draw_y + 4), 2)
