"""
High-Fidelity Retro HUD & On-Screen Dashboard for Mario AI Simulation.
"""

import pygame
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    COLOR_HUD_BG, COLOR_HUD_TEXT, COLOR_HUD_ACCENT
)


class HUD:
    def __init__(self):
        pygame.font.init()
        # Clean retro system font
        self.font_large = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_mid = pygame.font.SysFont("Consolas", 15, bold=True)
        self.font_small = pygame.font.SysFont("Consolas", 12)

    def draw(self, surface: pygame.Surface, stats: dict):
        """
        Renders HUD with generation telemetry, speed, death stats, and hotkeys.
        """
        # 1. Top Status Banner (Translucent Dark Slate)
        banner_h = 72
        banner = pygame.Surface((SCREEN_WIDTH, banner_h), pygame.SRCALPHA)
        banner.fill((16, 20, 30, 215))
        pygame.draw.line(banner, (80, 100, 140), (0, banner_h - 1), (SCREEN_WIDTH, banner_h - 1), 2)
        surface.blit(banner, (0, 0))

        # Generation & Stage Info
        gen_str = f"GEN {stats.get('generation', 0)}"
        gen_surf = self.font_large.render(gen_str, True, (255, 215, 0))
        surface.blit(gen_surf, (16, 12))

        stage_str = f"{stats.get('stage_name', 'Stage 1')}"
        stage_surf = self.font_mid.render(stage_str, True, (180, 220, 255))
        surface.blit(stage_surf, (16, 40))

        # Alive Count Bar
        alive_cnt = stats.get('alive_count', 0)
        pop_size = stats.get('population_size', 40)
        alive_txt = f"Alive: {alive_cnt}/{pop_size}"
        alive_col = (50, 255, 120) if alive_cnt > 0 else (255, 80, 80)
        surface.blit(self.font_mid.render(alive_txt, True, alive_col), (240, 14))

        # Health/Population Mini Bar
        bar_w = 120
        bar_h = 10
        ratio = alive_cnt / max(1, pop_size)
        pygame.draw.rect(surface, (60, 60, 60), (240, 42, bar_w, bar_h))
        pygame.draw.rect(surface, alive_col, (240, 42, int(bar_w * ratio), bar_h))
        pygame.draw.rect(surface, (200, 200, 200), (240, 42, bar_w, bar_h), 1)

        # Fitness & Distance
        best_fit = stats.get('best_fitness', 0.0)
        all_time = stats.get('all_time_best', 0.0)
        fit_txt = f"Best Fit: {best_fit:6.1f}  |  All-Time: {all_time:6.1f}"
        surface.blit(self.font_mid.render(fit_txt, True, (255, 255, 255)), (410, 14))

        max_d = stats.get('max_distance', 0.0)
        lvl_len = stats.get('level_length', 3000.0)
        pct = min(100.0, (max_d / lvl_len) * 100.0)
        dist_txt = f"Progress: {max_d:5.0f}m / {lvl_len:5.0f}m ({pct:4.1f}%)"
        surface.blit(self.font_mid.render(dist_txt, True, (255, 230, 120)), (410, 40))

        # Mode & Speed Badge
        mode_str = f"[{stats.get('mode', 'TRAINING')}]"
        speed_str = f"Speed: {stats.get('speed', 1)}x"
        surface.blit(self.font_mid.render(mode_str, True, (100, 220, 255)), (SCREEN_WIDTH - 210, 14))
        surface.blit(self.font_mid.render(speed_str, True, (255, 160, 80)), (SCREEN_WIDTH - 210, 40))

        # 2. Bottom Controls & Telemetry Bar
        foot_h = 28
        footer = pygame.Surface((SCREEN_WIDTH, foot_h), pygame.SRCALPHA)
        footer.fill((16, 20, 30, 215))
        pygame.draw.line(footer, (80, 100, 140), (0, 0), (SCREEN_WIDTH, 0), 1)
        surface.blit(footer, (0, SCREEN_HEIGHT - foot_h))

        # Deaths summary
        d_stats = stats.get('deaths', {})
        d_txt = f"Deaths -> Pits: {d_stats.get('pit', 0)} | Enemies: {d_stats.get('enemy', 0)} | Timeout: {d_stats.get('timeout', 0)}"
        surface.blit(self.font_small.render(d_txt, True, (220, 180, 180)), (14, SCREEN_HEIGHT - 22))

        # Hotkeys prompt
        help_txt = "[SPACE] Pause | [1-5] Speed | [H] Headless | [N] Brain | [G] Ghost | [P] Play | [C] Stage | [S/L] Save/Load"
        surface.blit(self.font_small.render(help_txt, True, (200, 220, 255)), (SCREEN_WIDTH - 650, SCREEN_HEIGHT - 22))
