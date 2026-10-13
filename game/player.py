"""
Mario Player Entity with authentic NES physics, collisions, animations, and stats.
"""

import pygame
from .constants import (
    MARIO_WIDTH, MARIO_HEIGHT,
    GRAVITY, TERMINAL_VELOCITY,
    WALK_ACCEL, RUN_ACCEL, MAX_WALK_SPEED, MAX_RUN_SPEED,
    GROUND_FRICTION, AIR_RESISTANCE,
    JUMP_VELOCITY, JUMP_HOLD_BOOST, MAX_JUMP_FRAMES,
    IDLE_TIMEOUT_FRAMES
)
from .sprites import SpriteSheet
from .sound import sound_manager


class MarioPlayer:
    def __init__(self, x: float = 100.0, y: float = 300.0, tint: tuple = None, alpha: int = 255):
        self.spawn_x = x
        self.spawn_y = y
        self.x = x
        self.y = y
        self.w = MARIO_WIDTH
        self.h = MARIO_HEIGHT
        self.vx = 0.0
        self.vy = 0.0

        # State flags
        self.is_grounded = False
        self.is_jumping = False
        self.jump_timer = 0
        self.facing_right = True
        self.is_dead = False
        self.death_cause = None  # "pit", "enemy", "timeout"
        self.won = False

        # Visuals
        self.tint = tint
        self.alpha = alpha
        self.anim_timer = 0
        self.state_name = "idle"

        # Gameplay & Fitness Metrics
        self.score = 0
        self.coins = 0
        self.enemies_stomped = 0
        self.max_x = x
        self.frames_alive = 0
        self.idle_frames = 0
        self.fitness = 0.0

        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)

    def reset(self):
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.is_grounded = False
        self.is_jumping = False
        self.jump_timer = 0
        self.facing_right = True
        self.is_dead = False
        self.death_cause = None
        self.won = False
        self.score = 0
        self.coins = 0
        self.enemies_stomped = 0
        self.max_x = self.spawn_x
        self.frames_alive = 0
        self.idle_frames = 0
        self.fitness = 0.0
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def apply_action(self, right: bool, left: bool, jump: bool, run: bool):
        if self.is_dead or self.won:
            return

        accel = RUN_ACCEL if run else WALK_ACCEL
        max_speed = MAX_RUN_SPEED if run else MAX_WALK_SPEED

        # Horizontal movement
        if right and not left:
            self.vx = min(self.vx + accel, max_speed)
            self.facing_right = True
        elif left and not right:
            self.vx = max(self.vx - accel, -max_speed)
            self.facing_right = False
        else:
            # Apply friction
            friction = GROUND_FRICTION if self.is_grounded else AIR_RESISTANCE
            self.vx *= friction
            if abs(self.vx) < 0.05:
                self.vx = 0.0

        # Jump physics
        if jump:
            if self.is_grounded and not self.is_jumping:
                self.is_jumping = True
                self.jump_timer = 1
                self.vy = JUMP_VELOCITY
                self.is_grounded = False
                sound_manager.play("jump")
            elif self.is_jumping and self.jump_timer < MAX_JUMP_FRAMES:
                # Sustained jump height by holding button
                self.vy -= JUMP_HOLD_BOOST
                self.jump_timer += 1
        else:
            self.is_jumping = False

    def update_physics_and_collisions(self, blocks, enemies, goal_flagpole=None):
        if self.is_dead:
            return

        self.frames_alive += 1

        # Apply gravity
        self.vy = min(self.vy + GRAVITY, TERMINAL_VELOCITY)

        # 1. Move Horizontal and resolve collisions
        self.x += self.vx
        self.rect.x = int(self.x)

        # Spatial cull: only check solid blocks immediately surrounding Mario
        nearby = [b for b in blocks if b.solid and abs(b.x - self.x) < 96]

        for b in nearby:
            if self.rect.colliderect(b.rect):
                if self.vx > 0:
                    self.rect.right = b.rect.left
                    self.x = self.rect.x
                    self.vx = 0.0
                elif self.vx < 0:
                    self.rect.left = b.rect.right
                    self.x = self.rect.x
                    self.vx = 0.0

        # 2. Move Vertical and resolve collisions
        self.y += self.vy
        self.rect.y = int(self.y)
        self.is_grounded = False

        for b in nearby:
            if self.rect.colliderect(b.rect):
                if self.vy > 0:
                    # Landing on top of block
                    self.rect.bottom = b.rect.top
                    self.y = self.rect.y
                    self.vy = 0.0
                    self.is_grounded = True
                    self.is_jumping = False
                    self.jump_timer = 0
                elif self.vy < 0:
                    # Bumping head against bottom of block
                    self.rect.top = b.rect.bottom
                    self.y = self.rect.y
                    self.vy = 0.0
                    if hasattr(b, "bump"):
                        b.bump(self)

        # 3. Enemy collisions
        for e in enemies:
            if not e.alive:
                continue
            if self.rect.colliderect(e.rect):
                # Check stomp condition: feet landed on enemy top half while moving downward
                stomped = (self.vy > 0) and (self.rect.bottom <= e.rect.top + 16)
                if stomped:
                    if hasattr(e, "stomp"):
                        if hasattr(e, "shell_sliding"):
                            e.stomp(self)
                        else:
                            e.stomp()
                    self.vy = -7.5
                    self.enemies_stomped += 1
                    self.score += 200
                else:
                    # Harmful contact
                    if hasattr(e, "shell_sliding") and e.state == "shell" and not e.shell_sliding:
                        # Harmless touch of stationary shell kicks it!
                        e.stomp(self)
                    elif getattr(e, "state", None) != "flat":
                        self.die("enemy")
                        return

        # 4. Check Flagpole Goal
        if goal_flagpole and not self.won:
            if self.rect.colliderect(goal_flagpole.rect):
                self.won = True
                self.score += 5000
                sound_manager.play("victory")

        # 5. Check Pit Death
        if self.y > 540:
            self.die("pit")
            return

        # 6. Track Progress & Idle Timer
        if self.x > self.max_x + 2:
            self.max_x = self.x
            self.idle_frames = 0
        else:
            self.idle_frames += 1
            if self.idle_frames >= IDLE_TIMEOUT_FRAMES:
                self.die("timeout")
                return

        # Animation state update
        self.anim_timer += 1
        if not self.is_grounded:
            self.state_name = "jump"
        elif abs(self.vx) > 0.4:
            f = (self.anim_timer // 8) % 3
            self.state_name = f"run{f}"
        else:
            self.state_name = "idle"

    def die(self, cause: str):
        if not self.is_dead and not self.won:
            self.is_dead = True
            self.death_cause = cause
            self.state_name = "dead"
            sound_manager.play("death")

    def calculate_fitness(self) -> float:
        # Distance progressed from start
        dist_fitness = max(0.0, self.max_x - self.spawn_x) * 1.0

        # Stomp and coin rewards
        stomp_fitness = self.enemies_stomped * 300.0
        coin_fitness = self.coins * 100.0

        # Velocity reward (moving faster is better than sluggish)
        speed_bonus = (self.max_x / max(1, self.frames_alive)) * 12.0

        # Completion bonus
        win_bonus = 6000.0 if self.won else 0.0

        # Penalties
        death_penalty = -60.0 if self.is_dead and not self.won else 0.0
        timeout_penalty = -40.0 if self.death_cause == "timeout" else 0.0

        self.fitness = dist_fitness + stomp_fitness + coin_fitness + speed_bonus + win_bonus + death_penalty + timeout_penalty
        return max(0.0, self.fitness)

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -50 <= draw_x <= surface.get_width():
            spr = SpriteSheet.get_mario_sprite(
                state=self.state_name,
                facing_right=self.facing_right,
                tint=self.tint,
                alpha=self.alpha
            )
            surface.blit(spr, (draw_x, self.y))
