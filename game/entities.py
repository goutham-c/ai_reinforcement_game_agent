"""
Enemies and Dynamic Entities (Goombas, Koopas, Coins, Particles).
"""

import pygame
from .constants import (
    TILE_SIZE, GRAVITY, TERMINAL_VELOCITY,
    GOOMBA_SPEED, KOOPA_SPEED, SHELL_SLIDE_SPEED
)
from .sprites import SpriteSheet
from .sound import sound_manager


class Entity:
    def __init__(self, x: float, y: float, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.alive = True
        self.rect = pygame.Rect(x, y, w, h)

    def update_physics(self, blocks):
        # Apply gravity
        self.vy = min(self.vy + GRAVITY, TERMINAL_VELOCITY)

        # Move X
        self.x += self.vx
        self.rect.x = int(self.x)
        for b in blocks:
            if b.solid and self.rect.colliderect(b.rect):
                if self.vx > 0:
                    self.rect.right = b.rect.left
                    self.x = self.rect.x
                    self.vx = -self.vx  # Bounce off walls
                elif self.vx < 0:
                    self.rect.left = b.rect.right
                    self.x = self.rect.x
                    self.vx = -self.vx

        # Move Y
        self.y += self.vy
        self.rect.y = int(self.y)
        self.on_ground = False
        for b in blocks:
            if b.solid and self.rect.colliderect(b.rect):
                if self.vy > 0:
                    self.rect.bottom = b.rect.top
                    self.y = self.rect.y
                    self.vy = 0.0
                    self.on_ground = True
                elif self.vy < 0:
                    self.rect.top = b.rect.bottom
                    self.y = self.rect.y
                    self.vy = 0.0


class Goomba(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 28, 28)
        self.vx = -GOOMBA_SPEED
        self.state = "walk0"  # walk0, walk1, flat
        self.anim_timer = 0
        self.squish_timer = 0

    def update(self, blocks):
        if self.state == "flat":
            self.squish_timer += 1
            if self.squish_timer > 25:
                self.alive = False
            return

        self.update_physics(blocks)
        self.anim_timer += 1
        self.state = "walk0" if (self.anim_timer // 15) % 2 == 0 else "walk1"

        # Offscreen pit fall
        if self.y > 600:
            self.alive = False

    def stomp(self):
        self.state = "flat"
        self.vx = 0.0
        self.vy = 0.0
        sound_manager.play("stomp")

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -32 <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_goomba_sprite(self.state), (draw_x, self.y))


class Koopa(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 28, 36)
        self.vx = -KOOPA_SPEED
        self.state = "walk0"  # walk0, walk1, shell
        self.anim_timer = 0
        self.shell_sliding = False

    def update(self, blocks):
        self.update_physics(blocks)

        if self.state == "shell":
            if self.shell_sliding:
                pass  # Keep sliding at high speed
            else:
                self.vx = 0.0
        else:
            self.anim_timer += 1
            self.state = "walk0" if (self.anim_timer // 15) % 2 == 0 else "walk1"

        if self.y > 600:
            self.alive = False

    def stomp(self, player):
        if self.state != "shell":
            self.state = "shell"
            self.h = 24
            self.rect.height = 24
            self.y += 12
            self.rect.y = int(self.y)
            self.vx = 0.0
            self.shell_sliding = False
            sound_manager.play("stomp")
        else:
            # Kick shell
            self.shell_sliding = True
            # Slide in direction player is moving, or away from player
            self.vx = SHELL_SLIDE_SPEED if player.x < self.x else -SHELL_SLIDE_SPEED
            sound_manager.play("stomp")

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -32 <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_koopa_sprite(self.state, self.vx >= 0), (draw_x, self.y))


class FloatingCoin(Entity):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 20)
        self.vy = -6.0
        self.timer = 0

    def update(self):
        self.y += self.vy
        self.vy += 0.4
        self.timer += 1
        if self.timer > 30:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -20 <= draw_x <= surface.get_width():
            frame = (self.timer // 4) % 4
            surface.blit(SpriteSheet.get_coin_sprite(frame), (draw_x, self.y))


class FloatingText:
    def __init__(self, x: float, y: float, text: str, color=(255, 255, 255)):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.timer = 0
        self.alive = True

    def update(self):
        self.y -= 1.0
        self.timer += 1
        if self.timer > 40:
            self.alive = False

    def draw(self, surface: pygame.Surface, camera_x: float, font: pygame.font.Font):
        if not self.alive:
            return
        draw_x = self.x - camera_x
        if -50 <= draw_x <= surface.get_width():
            txt_surf = font.render(self.text, True, self.color)
            surface.blit(txt_surf, (draw_x, self.y))
