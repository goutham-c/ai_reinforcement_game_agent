"""
Procedural Pixel-Art Sprite Factory for Mario Bros clone.
Generates authentic retro sprites dynamically using Pygame surfaces.
"""

import pygame
from .constants import (
    TILE_SIZE, MARIO_WIDTH, MARIO_HEIGHT,
    COLOR_MARIO_RED, COLOR_MARIO_BLUE, COLOR_MARIO_SKIN, COLOR_MARIO_BROWN,
    COLOR_GOOMBA_BROWN, COLOR_GOOMBA_LIGHT,
    COLOR_KOOPA_GREEN, COLOR_KOOPA_YELLOW,
    COLOR_GROUND, COLOR_GROUND_DARK,
    COLOR_BRICK, COLOR_QUESTION, COLOR_QUESTION_DARK,
    COLOR_PIPE_GREEN, COLOR_PIPE_DARK, COLOR_PIPE_LIGHT,
    COLOR_CLOUD, COLOR_HILL, COLOR_BUSH
)


class SpriteSheet:
    _cache = {}

    @classmethod
    def get_ground_tile(cls) -> pygame.Surface:
        if "ground" in cls._cache:
            return cls._cache["ground"]
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill(COLOR_GROUND)
        # Brick outlines & texture
        pygame.draw.rect(s, COLOR_GROUND_DARK, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        pygame.draw.line(s, COLOR_GROUND_DARK, (0, 16), (32, 16), 1)
        pygame.draw.line(s, COLOR_GROUND_DARK, (16, 0), (16, 16), 1)
        pygame.draw.line(s, COLOR_GROUND_DARK, (8, 16), (8, 32), 1)
        pygame.draw.line(s, COLOR_GROUND_DARK, (24, 16), (24, 32), 1)
        # Highlight spots
        for pos in [(4, 4), (20, 4), (12, 20), (28, 20)]:
            pygame.draw.rect(s, (240, 120, 60), (pos[0], pos[1], 2, 2))
        cls._cache["ground"] = s
        return s

    @classmethod
    def get_brick_tile(cls) -> pygame.Surface:
        if "brick" in cls._cache:
            return cls._cache["brick"]
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill(COLOR_BRICK)
        dark = (112, 28, 8)
        light = (228, 84, 40)
        # Brick pattern
        pygame.draw.line(s, dark, (0, 8), (32, 8), 1)
        pygame.draw.line(s, dark, (0, 16), (32, 16), 1)
        pygame.draw.line(s, dark, (0, 24), (32, 24), 1)
        pygame.draw.line(s, dark, (16, 0), (16, 8), 1)
        pygame.draw.line(s, dark, (8, 8), (8, 16), 1)
        pygame.draw.line(s, dark, (24, 8), (24, 16), 1)
        pygame.draw.line(s, dark, (16, 16), (16, 24), 1)
        pygame.draw.line(s, dark, (8, 24), (8, 32), 1)
        pygame.draw.line(s, dark, (24, 24), (24, 32), 1)
        # Border
        pygame.draw.rect(s, dark, (0, 0, TILE_SIZE, TILE_SIZE), 1)
        cls._cache["brick"] = s
        return s

    @classmethod
    def get_question_tile(cls, frame: int = 0) -> pygame.Surface:
        key = f"question_{frame % 4}"
        if key in cls._cache:
            return cls._cache[key]
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill(COLOR_QUESTION)
        dark = COLOR_QUESTION_DARK
        pygame.draw.rect(s, dark, (0, 0, TILE_SIZE, TILE_SIZE), 2)
        # Corner studs
        for pt in [(3, 3), (26, 3), (3, 26), (26, 26)]:
            pygame.draw.rect(s, (40, 40, 40), (pt[0], pt[1], 3, 3))
        # Question mark '?'
        q_color = (255, 255, 255) if (frame % 2 == 0) else (255, 240, 180)
        # Top arc of ?
        pygame.draw.rect(s, q_color, (11, 7, 10, 4))
        pygame.draw.rect(s, q_color, (17, 11, 4, 4))
        pygame.draw.rect(s, q_color, (13, 15, 6, 4))
        # Dot of ?
        pygame.draw.rect(s, q_color, (13, 21, 4, 4))
        cls._cache[key] = s
        return s

    @classmethod
    def get_empty_block_tile(cls) -> pygame.Surface:
        if "empty_block" in cls._cache:
            return cls._cache["empty_block"]
        s = pygame.Surface((TILE_SIZE, TILE_SIZE))
        s.fill((168, 90, 40))
        pygame.draw.rect(s, (100, 50, 20), (0, 0, TILE_SIZE, TILE_SIZE), 2)
        for pt in [(3, 3), (26, 3), (3, 26), (26, 26)]:
            pygame.draw.rect(s, (60, 30, 10), (pt[0], pt[1], 3, 3))
        cls._cache["empty_block"] = s
        return s

    @classmethod
    def get_pipe_top(cls) -> pygame.Surface:
        if "pipe_top" in cls._cache:
            return cls._cache["pipe_top"]
        # Pipe top is slightly wider than 32px (64px wide for double tile)
        w, h = 64, 32
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill(COLOR_PIPE_GREEN)
        # Highlights and shading
        pygame.draw.rect(s, COLOR_PIPE_LIGHT, (4, 2, 8, h - 4))
        pygame.draw.rect(s, COLOR_PIPE_DARK, (w - 12, 2, 8, h - 4))
        pygame.draw.rect(s, (0, 40, 0), (0, 0, w, h), 2)
        # Lip shadow
        pygame.draw.line(s, COLOR_PIPE_DARK, (2, h - 1), (w - 2, h - 1), 2)
        cls._cache["pipe_top"] = s
        return s

    @classmethod
    def get_pipe_body(cls) -> pygame.Surface:
        if "pipe_body" in cls._cache:
            return cls._cache["pipe_body"]
        w, h = 64, 32
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        # Inset slightly from pipe top
        pygame.draw.rect(s, COLOR_PIPE_GREEN, (4, 0, w - 8, h))
        pygame.draw.rect(s, COLOR_PIPE_LIGHT, (8, 0, 8, h))
        pygame.draw.rect(s, COLOR_PIPE_DARK, (w - 14, 0, 6, h))
        pygame.draw.rect(s, (0, 40, 0), (4, 0, w - 8, h), 2)
        cls._cache["pipe_body"] = s
        return s

    @classmethod
    def get_mario_sprite(cls, state: str = "idle", facing_right: bool = True,
                         tint: tuple = None, alpha: int = 255) -> pygame.Surface:
        key = f"mario_{state}_{facing_right}_{tint}_{alpha}"
        if key in cls._cache:
            return cls._cache[key]

        w, h = MARIO_WIDTH, MARIO_HEIGHT
        s = pygame.Surface((w, h), pygame.SRCALPHA)

        red = tint if tint else COLOR_MARIO_RED
        blue = COLOR_MARIO_BLUE
        skin = COLOR_MARIO_SKIN
        brown = COLOR_MARIO_BROWN

        if state == "dead":
            # Mario death pose (arms up, X eyes)
            pygame.draw.rect(s, red, (6, 0, 12, 6))      # Hat
            pygame.draw.rect(s, skin, (4, 6, 16, 10))    # Face
            pygame.draw.rect(s, (0, 0, 0), (6, 8, 3, 3)) # X eye
            pygame.draw.rect(s, (0, 0, 0), (14, 8, 3, 3))
            pygame.draw.rect(s, red, (4, 16, 16, 8))     # Shirt
            pygame.draw.rect(s, blue, (6, 24, 12, 8))    # Overalls
        elif state == "jump":
            # Jumping pose: arm up, feet tucked/split
            pygame.draw.rect(s, red, (7, 0, 12, 5))      # Hat
            pygame.draw.rect(s, skin, (6, 5, 13, 8))     # Face
            pygame.draw.rect(s, brown, (4, 7, 4, 6))     # Hair
            pygame.draw.rect(s, brown, (13, 9, 6, 3))    # Moustache
            pygame.draw.rect(s, red, (4, 13, 16, 9))     # Shirt
            pygame.draw.rect(s, skin, (0, 8, 5, 6))      # Upraised arm
            pygame.draw.rect(s, blue, (6, 20, 12, 8))    # Overalls
            pygame.draw.rect(s, brown, (2, 27, 8, 5))    # Left foot
            pygame.draw.rect(s, brown, (14, 25, 8, 5))   # Right foot
        elif "run" in state:
            # Running pose (frame alternates)
            f = 1 if "1" in state else (2 if "2" in state else 0)
            pygame.draw.rect(s, red, (7, 2, 12, 5))
            pygame.draw.rect(s, skin, (7, 7, 12, 8))
            pygame.draw.rect(s, brown, (5, 9, 4, 6))
            pygame.draw.rect(s, brown, (13, 11, 6, 3))
            pygame.draw.rect(s, red, (5, 15, 14, 8))
            pygame.draw.rect(s, blue, (6, 22, 12, 6))
            if f == 0:
                pygame.draw.rect(s, brown, (4, 28, 7, 4))
                pygame.draw.rect(s, brown, (13, 27, 7, 5))
            elif f == 1:
                pygame.draw.rect(s, brown, (1, 27, 8, 5))
                pygame.draw.rect(s, brown, (15, 26, 8, 5))
            else:
                pygame.draw.rect(s, brown, (5, 26, 8, 6))
                pygame.draw.rect(s, brown, (11, 28, 8, 4))
        else:
            # Idle pose
            pygame.draw.rect(s, red, (7, 2, 12, 5))      # Hat
            pygame.draw.rect(s, skin, (7, 7, 12, 8))     # Face
            pygame.draw.rect(s, brown, (5, 9, 4, 6))     # Hair
            pygame.draw.rect(s, brown, (13, 11, 6, 3))   # Moustache
            pygame.draw.rect(s, (0, 0, 0), (14, 8, 2, 3)) # Eye
            pygame.draw.rect(s, red, (5, 15, 14, 8))     # Shirt
            pygame.draw.rect(s, blue, (6, 22, 12, 6))    # Overalls
            pygame.draw.rect(s, (255, 220, 0), (8, 22, 2, 2))  # Button
            pygame.draw.rect(s, (255, 220, 0), (14, 22, 2, 2))
            pygame.draw.rect(s, brown, (4, 27, 7, 5))    # Shoes
            pygame.draw.rect(s, brown, (13, 27, 7, 5))

        if not facing_right:
            s = pygame.transform.flip(s, True, False)

        if alpha < 255:
            s.set_alpha(alpha)

        cls._cache[key] = s
        return s

    @classmethod
    def get_goomba_sprite(cls, state: str = "walk0") -> pygame.Surface:
        if state in cls._cache:
            return cls._cache[state]

        w, h = 28, 28
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        brown = COLOR_GOOMBA_BROWN
        stem = COLOR_GOOMBA_LIGHT

        if state == "flat":
            # Squished Goomba
            pygame.draw.ellipse(s, brown, (2, 16, 24, 10))
            pygame.draw.ellipse(s, (0, 0, 0), (6, 19, 4, 4))
            pygame.draw.ellipse(s, (0, 0, 0), (18, 19, 4, 4))
        else:
            # Mushroom head
            pygame.draw.ellipse(s, brown, (2, 2, 24, 16))
            # Stem body
            pygame.draw.rect(s, stem, (7, 14, 14, 8))
            # Eyes & angry eyebrows
            pygame.draw.line(s, (0, 0, 0), (6, 8), (11, 10), 2)
            pygame.draw.line(s, (0, 0, 0), (22, 8), (17, 10), 2)
            pygame.draw.rect(s, (255, 255, 255), (8, 10, 3, 5))
            pygame.draw.rect(s, (0, 0, 0), (9, 11, 2, 4))
            pygame.draw.rect(s, (255, 255, 255), (17, 10, 3, 5))
            pygame.draw.rect(s, (0, 0, 0), (17, 11, 2, 4))
            # Feet (alternating for walk animation)
            if state == "walk0":
                pygame.draw.ellipse(s, (40, 20, 0), (2, 20, 10, 8))
                pygame.draw.ellipse(s, (40, 20, 0), (16, 22, 10, 6))
            else:
                pygame.draw.ellipse(s, (40, 20, 0), (2, 22, 10, 6))
                pygame.draw.ellipse(s, (40, 20, 0), (16, 20, 10, 8))

        cls._cache[state] = s
        return s

    @classmethod
    def get_koopa_sprite(cls, state: str = "walk0", facing_right: bool = False) -> pygame.Surface:
        key = f"koopa_{state}_{facing_right}"
        if key in cls._cache:
            return cls._cache[key]

        w, h = 28, 36
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        green = COLOR_KOOPA_GREEN
        yellow = COLOR_KOOPA_YELLOW

        if state == "shell":
            # Koopa shell
            pygame.draw.ellipse(s, green, (2, 12, 24, 20))
            pygame.draw.ellipse(s, yellow, (5, 15, 18, 14))
            pygame.draw.rect(s, (255, 255, 255), (7, 20, 14, 4))
        else:
            # Head
            head_x = 16 if facing_right else 4
            pygame.draw.ellipse(s, yellow, (head_x, 2, 10, 12))
            eye_x = head_x + 6 if facing_right else head_x + 2
            pygame.draw.rect(s, (0, 0, 0), (eye_x, 5, 2, 3))
            # Shell body
            pygame.draw.ellipse(s, green, (4, 12, 20, 18))
            # Belly
            belly_x = 12 if facing_right else 6
            pygame.draw.ellipse(s, yellow, (belly_x, 15, 8, 12))
            # Feet
            foot_y1 = 28 if state == "walk0" else 30
            foot_y2 = 30 if state == "walk0" else 28
            pygame.draw.ellipse(s, yellow, (4, foot_y1, 8, 7))
            pygame.draw.ellipse(s, yellow, (16, foot_y2, 8, 7))

        if not facing_right and state != "shell":
            # Default was facing left
            pass

        cls._cache[key] = s
        return s

    @classmethod
    def get_coin_sprite(cls, frame: int = 0) -> pygame.Surface:
        f = frame % 4
        key = f"coin_{f}"
        if key in cls._cache:
            return cls._cache[key]

        s = pygame.Surface((16, 20), pygame.SRCALPHA)
        widths = [14, 10, 6, 10]
        w = widths[f]
        x = (16 - w) // 2
        gold = (252, 216, 0)
        dark_gold = (184, 148, 0)
        pygame.draw.ellipse(s, gold, (x, 2, w, 16))
        pygame.draw.ellipse(s, dark_gold, (x, 2, w, 16), 1)
        if w > 8:
            pygame.draw.line(s, (255, 255, 255), (x + 2, 5), (x + 2, 14), 1)
        cls._cache[key] = s
        return s

    @classmethod
    def get_flagpole(cls, height_tiles: int = 10) -> pygame.Surface:
        key = f"flagpole_{height_tiles}"
        if key in cls._cache:
            return cls._cache[key]
        h = height_tiles * TILE_SIZE
        s = pygame.Surface((48, h), pygame.SRCALPHA)
        # Gold ball at top
        pygame.draw.circle(s, (252, 216, 0), (16, 12), 10)
        pygame.draw.circle(s, (184, 148, 0), (16, 12), 10, 2)
        # Silver pole
        pygame.draw.rect(s, (216, 216, 216), (13, 22, 6, h - 22))
        pygame.draw.rect(s, (140, 140, 140), (16, 22, 3, h - 22))
        # Green flag near top
        pygame.draw.polygon(s, (0, 180, 0), [(13, 26), (46, 38), (13, 50)])
        pygame.draw.polygon(s, (0, 120, 0), [(13, 26), (46, 38), (13, 50)], 1)
        cls._cache[key] = s
        return s

    @classmethod
    def get_castle(cls) -> pygame.Surface:
        if "castle" in cls._cache:
            return cls._cache["castle"]
        w, h = 160, 160
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        brick = (184, 76, 32)
        dark = (100, 36, 12)
        # Main fortress base
        pygame.draw.rect(s, brick, (20, 60, 120, 100))
        # Central tower
        pygame.draw.rect(s, brick, (50, 20, 60, 40))
        # Battlements
        for bx in range(20, 140, 24):
            pygame.draw.rect(s, brick, (bx, 44, 16, 16))
        for bx in range(50, 110, 20):
            pygame.draw.rect(s, brick, (bx, 6, 14, 14))
        # Door arch
        pygame.draw.rect(s, (0, 0, 0), (64, 108, 32, 52))
        pygame.draw.circle(s, (0, 0, 0), (80, 108), 16)
        # Flag on top tower
        pygame.draw.line(s, (220, 220, 220), (80, 0), (80, 10), 2)
        pygame.draw.polygon(s, (220, 0, 0), [(80, 0), (95, 5), (80, 10)])
        cls._cache["castle"] = s
        return s
