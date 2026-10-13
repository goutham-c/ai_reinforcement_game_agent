"""
Sensory Perception and Observation Extraction for Mario AI.
Extracts 2D spatial vision grid, radar proximity features, and kinematics.
"""

from typing import List, Tuple
import numpy as np
from game.constants import TILE_SIZE, MAX_RUN_SPEED, TERMINAL_VELOCITY
from game.player import MarioPlayer


class SensorSystem:
    # 7 columns: -1 to +5 relative to Mario tile
    COL_OFFSETS = [-1, 0, 1, 2, 3, 4, 5]
    # 6 rows: -3 to +2 relative to Mario tile
    ROW_OFFSETS = [-3, -2, -1, 0, 1, 2]
    GRID_SIZE = len(COL_OFFSETS) * len(ROW_OFFSETS)  # 42

    @classmethod
    def get_observation(cls, player: MarioPlayer, level) -> np.ndarray:
        """
        Extracts a 50-dimensional observation vector for the given player.
        """
        obs = np.zeros(50, dtype=np.float32)

        mario_tile_x = int(player.x // TILE_SIZE)
        mario_tile_y = int(player.y // TILE_SIZE)

        # 1. Spatial Vision Grid (42 cells)
        grid_idx = 0
        for ro in cls.ROW_OFFSETS:
            ty = mario_tile_y + ro
            for co in cls.COL_OFFSETS:
                tx = mario_tile_x + co
                cell_val = 0.0
                # O(1) Fast check across level solid tiles
                if (tx, ty) in level.solid_tiles:
                    cell_val = 1.0
                else:
                    # Check if enemy is in this cell
                    cx = tx * TILE_SIZE
                    cy = ty * TILE_SIZE
                    for e in level.enemies:
                        if e.alive and (e.x - 12 <= cx <= e.x + e.w + 12) and (e.y - 12 <= cy <= e.y + e.h + 12):
                            cell_val = -1.0
                            break

                obs[grid_idx] = cell_val
                grid_idx += 1

        # 2. Radar Proximity Features (4 values)
        # Find nearest alive enemy ahead
        nearest_enemy_dist = 1.0
        nearest_enemy_dy = 0.0
        min_dx = float('inf')

        for e in level.enemies:
            if not e.alive:
                continue
            dx = e.x - player.x
            if 0 <= dx < 360.0:  # Within 360px ahead
                if dx < min_dx:
                    min_dx = dx
                    nearest_enemy_dist = dx / 360.0
                    nearest_enemy_dy = np.clip((e.y - player.y) / 120.0, -1.0, 1.0)

        obs[42] = nearest_enemy_dist
        obs[43] = nearest_enemy_dy

        # Pit radar: find upcoming pit
        pit_dist = 1.0
        pit_width = 0.0
        for p_start, p_end in level.pits:
            dist_to_edge = p_start - (player.x + player.w)
            if 0 <= dist_to_edge < 360.0:
                pit_dist = dist_to_edge / 360.0
                pit_width = min(1.0, (p_end - p_start) / (TILE_SIZE * 4))
                break

        obs[44] = pit_dist
        obs[45] = pit_width

        # 3. Mario Kinematics / Proprioception (4 values)
        obs[46] = np.clip(player.vx / MAX_RUN_SPEED, -1.0, 1.0)
        obs[47] = np.clip(player.vy / TERMINAL_VELOCITY, -1.0, 1.0)
        obs[48] = 1.0 if player.is_grounded else 0.0
        obs[49] = 1.0 if (player.is_grounded and not player.is_jumping) else 0.0

        return obs
