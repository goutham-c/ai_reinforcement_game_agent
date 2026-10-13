"""
Game Environment Simulation Engine for Mario RL.
Supports single-agent gym-style step, multi-agent population simulation,
fast headless mode, and rich retro rendering with parallax scrolling.
"""

from typing import List, Dict, Any, Tuple
import pygame
from .constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_SKY,
    COLOR_CLOUD, COLOR_HILL, COLOR_BUSH, TILE_SIZE
)
from .level import Level
from .player import MarioPlayer
from .entities import FloatingCoin, FloatingText


class MarioEnvironment:
    def __init__(self, stage: int = 1):
        self.stage_number = stage
        self.level = Level(stage)
        self.players: List[MarioPlayer] = []
        self.ghost_player: MarioPlayer = None
        self.particles: List[Any] = []
        self.camera_x = 0.0
        self.frame_count = 0

        # Background decorative elements (hills, clouds, bushes)
        self._init_scenery()

    def _init_scenery(self):
        self.clouds = [
            (120, 80, 70, 32), (380, 60, 90, 36), (720, 90, 60, 28),
            (1100, 70, 80, 34), (1600, 85, 75, 30), (2200, 65, 95, 38),
            (2800, 80, 70, 32), (3400, 60, 85, 35)
        ]
        self.hills = [
            (40, 448, 140, 70), (460, 448, 180, 90), (980, 448, 150, 75),
            (1520, 448, 190, 95), (2100, 448, 160, 80), (2750, 448, 180, 90)
        ]
        self.bushes = [
            (240, 448, 80, 32), (650, 448, 100, 32), (1240, 448, 70, 32),
            (1850, 448, 90, 32), (2450, 448, 80, 32)
        ]

    def reset(self, stage: int = None):
        if stage is not None and stage != self.stage_number:
            self.stage_number = stage
        self.level = Level(self.stage_number)
        self.particles.clear()
        self.camera_x = 0.0
        self.frame_count = 0
        for p in self.players:
            p.reset()
        if self.ghost_player:
            self.ghost_player.reset()

    def set_players(self, players: List[MarioPlayer]):
        self.players = players
        self.reset()

    def set_ghost_player(self, ghost: MarioPlayer):
        self.ghost_player = ghost

    def step(self, actions: List[Tuple[bool, bool, bool, bool]] = None):
        """
        Step simulation by 1 frame.
        actions: list of (right, left, jump, run) tuples corresponding to each player.
        """
        self.frame_count += 1

        # 1. Update blocks (bumping animations, etc.)
        for b in self.level.blocks:
            if hasattr(b, "update"):
                b.update()

        # 2. Update enemies
        for e in self.level.enemies:
            if e.alive:
                e.update(self.level.blocks)

        # 3. Update active players
        any_alive = False
        lead_x = 0.0

        for idx, p in enumerate(self.players):
            if not p.is_dead and not p.won:
                any_alive = True
                if actions and idx < len(actions):
                    r, l, j, run = actions[idx]
                    p.apply_action(r, l, j, run)
                p.update_physics_and_collisions(
                    self.level.blocks,
                    self.level.enemies,
                    self.level.flagpole
                )
                if p.x > lead_x:
                    lead_x = p.x
            else:
                if p.x > lead_x:
                    lead_x = p.x

        # 4. Update Ghost player (if present in self-play mode)
        if self.ghost_player and not self.ghost_player.is_dead and not self.ghost_player.won:
            # Ghost uses its own policy or recorded action in self_play manager
            self.ghost_player.update_physics_and_collisions(
                self.level.blocks,
                self.level.enemies,
                self.level.flagpole
            )

        # 5. Smooth camera tracking follow lead Mario
        target_cam_x = max(0.0, lead_x - 300.0)
        self.camera_x += (target_cam_x - self.camera_x) * 0.1

        return any_alive

    def render(self, surface: pygame.Surface, show_all_players: bool = True, focused_player: MarioPlayer = None):
        # 1. Clear sky background
        surface.fill(COLOR_SKY)

        # 2. Render Parallax Scenery
        # Clouds
        for cx, cy, cw, ch in self.clouds:
            draw_x = cx - self.camera_x * 0.3
            if -cw <= draw_x <= SCREEN_WIDTH:
                pygame.draw.ellipse(surface, COLOR_CLOUD, (draw_x, cy, cw, ch))
                pygame.draw.circle(surface, COLOR_CLOUD, (int(draw_x + cw * 0.35), int(cy + ch * 0.4)), int(ch * 0.6))
                pygame.draw.circle(surface, COLOR_CLOUD, (int(draw_x + cw * 0.65), int(cy + ch * 0.4)), int(ch * 0.5))

        # Green Hills
        for hx, hy, hw, hh in self.hills:
            draw_x = hx - self.camera_x * 0.5
            if -hw <= draw_x <= SCREEN_WIDTH:
                pygame.draw.ellipse(surface, COLOR_HILL, (draw_x, hy - hh + 10, hw, hh * 2))

        # Bushes
        for bx, by, bw, bh in self.bushes:
            draw_x = bx - self.camera_x * 0.8
            if -bw <= draw_x <= SCREEN_WIDTH:
                pygame.draw.ellipse(surface, COLOR_BUSH, (draw_x, by - bh + 6, bw, bh * 2))

        # 3. Render all blocks, pipes, and flagpole
        for b in self.level.blocks:
            b.draw(surface, self.camera_x)

        # 4. Render enemies
        for e in self.level.enemies:
            if e.alive:
                e.draw(surface, self.camera_x)

        # 5. Render Ghost player (in self-play mode)
        if self.ghost_player and not self.ghost_player.is_dead:
            self.ghost_player.draw(surface, self.camera_x)

        # 6. Render Players
        if focused_player:
            # Render only the focused hero
            focused_player.draw(surface, self.camera_x)
        elif show_all_players:
            # Sort players: dead first, alive on top, highest x topmost
            sorted_players = sorted(self.players, key=lambda p: (not p.is_dead, p.x))
            for p in sorted_players:
                p.draw(surface, self.camera_x)
        else:
            # Render best alive player
            alive = [p for p in self.players if not p.is_dead]
            if alive:
                best = max(alive, key=lambda p: p.x)
                best.draw(surface, self.camera_x)

        # 7. Render floating particles/text
        for p in self.particles:
            if hasattr(p, "draw"):
                p.draw(surface, self.camera_x)
