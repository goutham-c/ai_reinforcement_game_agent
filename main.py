"""
Mario Bros Self-Learning AI & Self-Play Framework.
Main launcher supporting:
 - Real-Time Evolution Training with Live Population
 - Generational Self-Play & Ghost Racing
 - Headless Turbo Training (evoles generations in seconds)
 - Champion Replay Mode
 - Human Play Mode
"""

import sys
import os
import time
import argparse
import pygame

from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    COLOR_MARIO_RED
)
from game.environment import MarioEnvironment
from game.player import MarioPlayer
from ai.neuroevolution import NeuroevolutionManager
from ai.self_play import SelfPlayArena
from ai.curriculum import CurriculumManager
from ui.hud import HUD
from ui.neural_visualizer import NeuralVisualizer
from ui.death_tracker import DeathTracker


def parse_arguments():
    parser = argparse.ArgumentParser(description="Mario Bros Self-Learning RL & Self-Play System")
    parser.add_argument("--mode", type=str, default="train", choices=["train", "headless", "replay", "race", "play"],
                        help="Execution mode: train (visual evolution), headless (turbo train), replay (watch champion), race (self-play), play (human)")
    parser.add_argument("--stage", type=int, default=1, choices=[1, 2, 3],
                        help="Starting level stage: 1 (Tutorial), 2 (World 1-1 replica), 3 (Hardcore gauntlet)")
    parser.add_argument("--pop", type=int, default=40, help="Population size per generation (default: 40)")
    parser.add_argument("--generations", type=int, default=50, help="Target generations for headless training")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/mario_evolution.json", help="Path to checkpoint file")
    return parser.parse_args()


class MarioApp:
    def __init__(self, args):
        self.args = args
        self.stage = args.stage
        self.mode = args.mode  # "train", "replay", "race", "play"
        self.speed = 1  # 1x, 2x, 5x, 10x, 20x
        self.paused = False
        self.running = True

        # Core Systems
        self.env = MarioEnvironment(stage=self.stage)
        self.ai = NeuroevolutionManager(population_size=args.pop)
        self.curriculum = CurriculumManager(start_stage=self.stage, auto_advance=True)
        self.self_play = SelfPlayArena()

        # UI & Analytics
        self.hud = HUD()
        self.neural_vis = NeuralVisualizer()
        self.death_tracker = DeathTracker()

        # Try auto-load existing checkpoint if available
        if os.path.exists(args.checkpoint):
            self.ai.load_checkpoint(args.checkpoint)
            if self.ai.all_time_best:
                print(f"[MarioApp] Checkpoint loaded! Best Fitness: {self.ai.all_time_best.fitness:.1f}")

        # Human player instance for Play mode
        self.human_player = MarioPlayer(tint=(255, 50, 50), alpha=255)

        # Pygame Window setup (if not headless)
        if self.mode != "headless":
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption(TITLE)
            self.clock = pygame.time.Clock()
        else:
            self.screen = None
            self.clock = None

        self._setup_current_mode()

    def _setup_current_mode(self):
        self.env.reset(self.stage)
        self.death_tracker.clear()

        if self.mode in ("train", "headless"):
            players = self.ai.create_players()
            self.env.set_players(players)
            # Setup past champion ghost for self-play comparison
            if self.ai.all_time_best:
                self.self_play.set_past_champion_ghost(self.ai.all_time_best, self.ai.generation)
                if self.self_play.ghost_racers:
                    self.env.set_ghost_player(self.self_play.ghost_racers[0].player)

        elif self.mode == "replay":
            if self.ai.all_time_best:
                champ_player = MarioPlayer(tint=(255, 215, 0), alpha=255)
                self.env.set_players([champ_player])
            else:
                print("[MarioApp] No champion checkpoint found yet. Starting fresh.")
                self.mode = "train"
                self._setup_current_mode()

        elif self.mode == "race":
            # Race champion of Gen 0, Gen 5, Gen 10 vs All-time Best!
            race_entries = []
            if self.ai.gen_champions:
                for idx in [0, min(5, len(self.ai.gen_champions)-1), min(15, len(self.ai.gen_champions)-1)]:
                    if idx < len(self.ai.gen_champions):
                        race_entries.append((idx, self.ai.gen_champions[idx]))
            if self.ai.all_time_best:
                race_entries.append((self.ai.generation, self.ai.all_time_best))

            if not race_entries and self.ai.population:
                race_entries.append((0, self.ai.population[0]))

            self.self_play.setup_multigen_race(race_entries)
            race_players = [g.player for g in self.self_play.ghost_racers]
            self.env.set_players(race_players)

        elif self.mode == "play":
            self.human_player.reset()
            players = [self.human_player]
            if self.ai.all_time_best:
                # Race against AI Champion!
                self.self_play.set_past_champion_ghost(self.ai.all_time_best, self.ai.generation)
                if self.self_play.ghost_racers:
                    players.append(self.self_play.ghost_racers[0].player)
            self.env.set_players(players)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused

                # Speed Multipliers (1x, 2x, 5x, 10x, 20x)
                elif event.key == pygame.K_1:
                    self.speed = 1
                elif event.key == pygame.K_2:
                    self.speed = 2
                elif event.key == pygame.K_3:
                    self.speed = 5
                elif event.key == pygame.K_4:
                    self.speed = 10
                elif event.key == pygame.K_5:
                    self.speed = 20

                # Headless Turbo Toggle
                elif event.key == pygame.K_h:
                    self._run_turbo_headless_evolution(generations_to_run=10)

                # Overlays & Features
                elif event.key == pygame.K_n:
                    self.neural_vis.toggle()

                elif event.key == pygame.K_g:
                    # Toggle Ghost Self-Play
                    if self.env.ghost_player:
                        self.env.set_ghost_player(None)
                    elif self.self_play.ghost_racers:
                        self.env.set_ghost_player(self.self_play.ghost_racers[0].player)

                # Mode Switching
                elif event.key == pygame.K_p:
                    modes = ["train", "replay", "race", "play"]
                    cur_idx = modes.index(self.mode) if self.mode in modes else 0
                    self.mode = modes[(cur_idx + 1) % len(modes)]
                    print(f"[MarioApp] Switched to mode: {self.mode.upper()}")
                    self._setup_current_mode()

                # Stage Cycling
                elif event.key == pygame.K_c:
                    self.stage = self.curriculum.cycle_stage()
                    print(f"[MarioApp] Switched to: Stage {self.stage}")
                    self._setup_current_mode()

                # Save / Load Checkpoint
                elif event.key == pygame.K_s:
                    self.ai.save_checkpoint(self.args.checkpoint)
                elif event.key == pygame.K_l:
                    if self.ai.load_checkpoint(self.args.checkpoint):
                        self._setup_current_mode()

                # Reset Generation
                elif event.key == pygame.K_r:
                    self._setup_current_mode()

    def _get_human_actions(self):
        keys = pygame.key.get_pressed()
        right = bool(keys[pygame.K_RIGHT] or keys[pygame.K_d])
        left = bool(keys[pygame.K_LEFT] or keys[pygame.K_a])
        jump = bool(keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w])
        run = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
        return (right, left, jump, run)

    def update_simulation_step(self):
        if self.paused:
            return

        if self.mode == "train":
            # 1. Compute AI actions for all genomes
            actions = self.ai.get_actions(self.env.players, self.env.level)

            # 2. Ghost self-play action
            if self.self_play.ghost_racers:
                self.self_play.ghost_racers[0].step(self.env.level)

            # 3. Step physics simulation
            any_alive = self.env.step(actions)

            # Track deaths for danger markers
            for p in self.env.players:
                if p.is_dead and p.death_cause:
                    self.death_tracker.record_death(p.x, p.y, p.death_cause)

            # If all agents died or finished, evolve next generation!
            if not any_alive:
                self._evolve_next_generation()

        elif self.mode == "replay":
            if self.ai.all_time_best and self.env.players:
                champ_player = self.env.players[0]
                if not champ_player.is_dead and not champ_player.won:
                    from ai.sensors import SensorSystem
                    obs = SensorSystem.get_observation(champ_player, self.env.level)
                    act = self.ai.all_time_best.network.get_actions(obs)
                    champ_player.apply_action(*act)
                    self.env.step([act])
                else:
                    # Restart replay loop
                    time.sleep(0.5)
                    self._setup_current_mode()

        elif self.mode == "race":
            # Race mode: all racers step according to their respective historical genomes
            actions = []
            for racer in self.self_play.ghost_racers:
                act = racer.step(self.env.level)
                actions.append(act)
            any_alive = self.env.step(actions)
            if not any_alive or self.env.frame_count > 900:
                time.sleep(0.8)
                self._setup_current_mode()

        elif self.mode == "play":
            # Human player + Ghost AI champion
            human_act = self._get_human_actions()
            actions = [human_act]
            if self.self_play.ghost_racers:
                ghost_act = self.self_play.ghost_racers[0].step(self.env.level)
                actions.append(ghost_act)
            self.env.step(actions)
            if self.human_player.is_dead:
                time.sleep(0.5)
                self._setup_current_mode()

    def _evolve_next_generation(self):
        stat = self.ai.evaluate_and_evolve(self.env.players)
        print(f"[{stat['generation']}] Best Fit: {stat['best_fitness']:6.1f} | Avg Fit: {stat['avg_fitness']:6.1f} | Max Dist: {stat['max_distance']:5.0f}m | Wins: {stat['wins']}")

        # Curriculum Progression Check
        if self.curriculum.check_progression(stat['best_fitness'], stat['wins'] > 0):
            self.stage = self.curriculum.current_stage

        # Auto-save checkpoint every 5 generations
        if self.ai.generation % 5 == 0:
            self.ai.save_checkpoint(self.args.checkpoint)

        self._setup_current_mode()

    def _run_turbo_headless_evolution(self, generations_to_run: int = 15):
        """
        Runs batch generations at maximum speed without graphic rendering.
        """
        print(f"\n[TURBO] Running {generations_to_run} generations in headless turbo mode...", flush=True)
        start_time = time.time()

        for g in range(generations_to_run):
            self.env.reset(self.stage)
            players = self.ai.create_players()
            self.env.set_players(players)

            max_frames = 1200
            for frame in range(max_frames):
                actions = self.ai.get_actions(self.env.players, self.env.level)
                any_alive = self.env.step(actions)
                if not any_alive:
                    break

            stat = self.ai.evaluate_and_evolve(self.env.players)
            print(f" [Turbo Gen {stat['generation']:2d}] Best Fit: {stat['best_fitness']:6.1f} | Dist: {stat['max_distance']:5.0f}m | Wins: {stat['wins']}", flush=True)

            if self.curriculum.check_progression(stat['best_fitness'], stat['wins'] > 0):
                self.stage = self.curriculum.current_stage

        elapsed = time.time() - start_time
        print(f"[TURBO] Completed {generations_to_run} generations in {elapsed:.2f}s! ({elapsed/generations_to_run:.2f}s/gen)\n", flush=True)
        self.ai.save_checkpoint(self.args.checkpoint)
        self._setup_current_mode()

    def render(self):
        if self.screen is None:
            return

        # 1. Render Environment (World, blocks, enemies, players, scenery)
        self.env.render(self.screen, show_all_players=(self.mode == "train" or self.mode == "race"))

        # 2. Render Death markers
        self.death_tracker.draw(self.screen, self.env.camera_x)

        # 3. Render Neural Network Visualizer (Active brain)
        active_net = None
        if self.mode == "train" and self.ai.population:
            # Show brain of leading player
            alive_players = [(idx, p) for idx, p in enumerate(self.env.players) if not p.is_dead]
            if alive_players:
                best_idx, _ = max(alive_players, key=lambda item: item[1].x)
                active_net = self.ai.population[best_idx].network
            else:
                active_net = self.ai.population[0].network
        elif self.ai.all_time_best:
            active_net = self.ai.all_time_best.network

        self.neural_vis.draw(self.screen, active_net)

        # 4. Render HUD
        alive_count = sum(1 for p in self.env.players if not p.is_dead and not p.won)
        lead_x = max([p.x for p in self.env.players], default=0.0)
        lead_fit = max([p.calculate_fitness() for p in self.env.players], default=0.0)

        stats = {
            "generation": self.ai.generation,
            "stage_name": self.env.level.name,
            "alive_count": alive_count,
            "population_size": len(self.env.players),
            "best_fitness": lead_fit,
            "all_time_best": self.ai.all_time_best.fitness if self.ai.all_time_best else 0.0,
            "max_distance": lead_x,
            "level_length": self.env.level.level_length,
            "mode": self.mode.upper(),
            "speed": self.speed,
            "deaths": self.ai.history[-1]["deaths"] if self.ai.history else {}
        }
        self.hud.draw(self.screen, stats)

        pygame.display.flip()

    def run(self):
        if self.mode == "headless":
            self._run_turbo_headless_evolution(self.args.generations)
            return

        while self.running:
            self.handle_events()

            # Multiple simulation substeps per frame for fast-forward speeds
            for _ in range(self.speed):
                self.update_simulation_step()

            self.render()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    args = parse_arguments()
    app = MarioApp(args)
    app.run()


if __name__ == "__main__":
    main()
