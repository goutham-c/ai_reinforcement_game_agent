"""
Interactive Blocks, Pipes, Platforms, and Goals for Mario Bros.
"""

import pygame
from .constants import TILE_SIZE
from .sprites import SpriteSheet
from .sound import sound_manager


class Block:
    def __init__(self, x: float, y: float, w: int = TILE_SIZE, h: int = TILE_SIZE, solid: bool = True):
        self.x = x
        self.y = y
        self.orig_y = y
        self.w = w
        self.h = h
        self.solid = solid
        self.rect = pygame.Rect(x, y, w, h)
        self.bump_vy = 0.0
        self.is_bumping = False

    def bump(self, player=None):
        if not self.is_bumping:
            self.is_bumping = True
            self.bump_vy = -4.0
            sound_manager.play("bump")

    def update(self):
        if self.is_bumping:
            self.y += self.bump_vy
            self.bump_vy += 0.8
            if self.y >= self.orig_y:
                self.y = self.orig_y
                self.bump_vy = 0.0
                self.is_bumping = False
            self.rect.y = int(self.y)

    def draw(self, surface: pygame.Surface, camera_x: float):
        pass


class GroundBlock(Block):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, solid=True)

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -TILE_SIZE <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_ground_tile(), (draw_x, self.y))


class BrickBlock(Block):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, solid=True)

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -TILE_SIZE <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_brick_tile(), (draw_x, self.y))


class QuestionBlock(Block):
    def __init__(self, x: float, y: float, contents: str = "coin"):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, solid=True)
        self.contents = contents
        self.spent = False
        self.anim_timer = 0

    def bump(self, player=None):
        if not self.spent:
            super().bump()
            self.spent = True
            if self.contents == "coin":
                sound_manager.play("coin")
                if player:
                    player.coins += 1
                    player.score += 100
        else:
            sound_manager.play("bump")

    def update(self):
        super().update()
        self.anim_timer += 1

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -TILE_SIZE <= draw_x <= surface.get_width():
            if self.spent:
                surface.blit(SpriteSheet.get_empty_block_tile(), (draw_x, self.y))
            else:
                frame = (self.anim_timer // 15) % 4
                surface.blit(SpriteSheet.get_question_tile(frame), (draw_x, self.y))


class Pipe(Block):
    def __init__(self, x: float, y: float, height_tiles: int = 2):
        w = 64
        h = height_tiles * TILE_SIZE
        # y is the top of the pipe
        super().__init__(x, y, w, h, solid=True)
        self.height_tiles = height_tiles

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -64 <= draw_x <= surface.get_width():
            # Draw top
            surface.blit(SpriteSheet.get_pipe_top(), (draw_x, self.y))
            # Draw body tiles below
            for i in range(1, self.height_tiles):
                surface.blit(SpriteSheet.get_pipe_body(), (draw_x, self.y + i * TILE_SIZE))


class Flagpole(Block):
    def __init__(self, x: float, ground_y: float, height_tiles: int = 10):
        h = height_tiles * TILE_SIZE
        y = ground_y - h
        super().__init__(x, y, 48, h, solid=False)
        self.height_tiles = height_tiles
        self.reached = False

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -64 <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_flagpole(self.height_tiles), (draw_x, self.y))


class Castle(Block):
    def __init__(self, x: float, ground_y: float):
        w, h = 160, 160
        y = ground_y - h
        super().__init__(x, y, w, h, solid=False)

    def draw(self, surface: pygame.Surface, camera_x: float):
        draw_x = self.x - camera_x
        if -160 <= draw_x <= surface.get_width():
            surface.blit(SpriteSheet.get_castle(), (draw_x, self.y))
