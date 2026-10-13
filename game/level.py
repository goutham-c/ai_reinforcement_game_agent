"""
Level Layouts and Progressive Challenge System for Mario Bros.
Includes Stage 1 (Tutorial), Stage 2 (World 1-1 Replica), and Stage 3 (Hardcore Chaos).
"""

from typing import List, Tuple
from .constants import TILE_SIZE, GROUND_Y
from .blocks import Block, GroundBlock, BrickBlock, QuestionBlock, Pipe, Flagpole, Castle
from .entities import Goomba, Koopa


class Level:
    def __init__(self, stage_number: int = 1):
        self.stage_number = stage_number
        self.blocks: List[Block] = []
        self.enemies: List = []
        self.flagpole: Flagpole = None
        self.castle: Castle = None
        self.start_x: float = 80.0
        self.start_y: float = GROUND_Y - 40.0
        self.level_length: float = 3000.0
        self.name: str = f"Stage {stage_number}"
        self.pits: List[Tuple[float, float]] = []  # List of (pit_start_x, pit_end_x)
        self.solid_tiles: set = set()  # Set of (tile_x, tile_y) for O(1) sensor collision checks

        self._build_stage(stage_number)

    def _build_stage(self, stage: int):
        self.blocks.clear()
        self.enemies.clear()
        self.pits.clear()
        self.solid_tiles.clear()

        if stage == 1:
            self._build_stage_1_tutorial()
        elif stage == 2:
            self._build_stage_2_world_1_1()
        else:
            self._build_stage_3_hardcore()

        self._bake_solid_tiles()

    def _bake_solid_tiles(self):
        for b in self.blocks:
            if b.solid:
                tx_start = int(b.x // TILE_SIZE)
                tx_end = int((b.x + b.w - 1) // TILE_SIZE)
                ty_start = int(b.y // TILE_SIZE)
                ty_end = int((b.y + b.h - 1) // TILE_SIZE)
                for tx in range(tx_start, tx_end + 1):
                    for ty in range(ty_start, ty_end + 1):
                        self.solid_tiles.add((tx, ty))

    def _add_ground_span(self, start_tile: int, end_tile: int):
        for tx in range(start_tile, end_tile):
            x = tx * TILE_SIZE
            # Two layers of ground tiles for solid footing
            self.blocks.append(GroundBlock(x, GROUND_Y))
            self.blocks.append(GroundBlock(x, GROUND_Y + TILE_SIZE))
            self.blocks.append(GroundBlock(x, GROUND_Y + TILE_SIZE * 2))

    def _record_pit(self, pit_start_tile: int, pit_end_tile: int):
        self.pits.append((pit_start_tile * TILE_SIZE, pit_end_tile * TILE_SIZE))

    def _build_stage_1_tutorial(self):
        """Introductory stage: small gaps, solitary Goombas, simple jumps."""
        self.name = "Stage 1: Beginner Plains"
        self.level_length = 2200.0

        # Ground spans with gentle pits
        self._add_ground_span(0, 22)
        self._record_pit(22, 24)  # 2-tile pit

        self._add_ground_span(24, 45)
        self._record_pit(45, 48)  # 3-tile pit

        self._add_ground_span(48, 75)

        # Question mark blocks
        self.blocks.append(QuestionBlock(14 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(QuestionBlock(16 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(QuestionBlock(18 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))

        # Short pipes
        self.blocks.append(Pipe(28 * TILE_SIZE, GROUND_Y - 2 * TILE_SIZE, height_tiles=2))
        self.blocks.append(Pipe(38 * TILE_SIZE, GROUND_Y - 3 * TILE_SIZE, height_tiles=3))

        # Solitary Goombas
        self.enemies.append(Goomba(12 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(33 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(54 * TILE_SIZE, GROUND_Y - 32))

        # End Goal
        flag_x = 65 * TILE_SIZE
        self.flagpole = Flagpole(flag_x, GROUND_Y)
        self.castle = Castle(flag_x + 120, GROUND_Y)
        self.blocks.append(self.flagpole)
        self.blocks.append(self.castle)

    def _build_stage_2_world_1_1(self):
        """Authentic Super Mario Bros World 1-1 layout."""
        self.name = "Stage 2: Super Mario Bros World 1-1"
        self.level_length = 3600.0

        # Ground spans with authentic pits
        self._add_ground_span(0, 69)
        self._record_pit(69, 71)

        self._add_ground_span(71, 86)
        self._record_pit(86, 89)

        self._add_ground_span(89, 153)
        self._record_pit(153, 155)

        self._add_ground_span(155, 200)

        # First question block
        self.blocks.append(QuestionBlock(16 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))

        # Trio of blocks (Brick, Question, Brick, Question, Brick)
        self.blocks.append(BrickBlock(20 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(QuestionBlock(21 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(BrickBlock(22 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(QuestionBlock(23 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(BrickBlock(24 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))

        # High question block above
        self.blocks.append(QuestionBlock(22 * TILE_SIZE, GROUND_Y - 8 * TILE_SIZE))

        # Pipes of increasing height
        self.blocks.append(Pipe(28 * TILE_SIZE, GROUND_Y - 2 * TILE_SIZE, height_tiles=2))
        self.blocks.append(Pipe(38 * TILE_SIZE, GROUND_Y - 3 * TILE_SIZE, height_tiles=3))
        self.blocks.append(Pipe(46 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE, height_tiles=4))
        self.blocks.append(Pipe(57 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE, height_tiles=4))

        # Enemies in first sector
        self.enemies.append(Goomba(22 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(41 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(51 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(53 * TILE_SIZE, GROUND_Y - 32))

        # Second block cluster
        for bx in range(77, 85):
            self.blocks.append(BrickBlock(bx * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))
        self.blocks.append(QuestionBlock(80 * TILE_SIZE, GROUND_Y - 8 * TILE_SIZE))

        # Koopa Troopa patrolling
        self.enemies.append(Koopa(82 * TILE_SIZE, GROUND_Y - 40))

        # Staircase Pyramids
        for step in range(1, 5):
            for h in range(step):
                self.blocks.append(GroundBlock((95 + step) * TILE_SIZE, GROUND_Y - (h + 1) * TILE_SIZE))

        # Final Staircase to Flagpole
        for step in range(1, 9):
            for h in range(step):
                self.blocks.append(GroundBlock((120 + step) * TILE_SIZE, GROUND_Y - (h + 1) * TILE_SIZE))

        # Flagpole & Castle
        flag_x = 135 * TILE_SIZE
        self.flagpole = Flagpole(flag_x, GROUND_Y)
        self.castle = Castle(flag_x + 140, GROUND_Y)
        self.blocks.append(self.flagpole)
        self.blocks.append(self.castle)

    def _build_stage_3_hardcore(self):
        """Hardcore challenge: tight pit jumps, dense enemy waves, sliding shells, and high pipes."""
        self.name = "Stage 3: Bowser's Gauntlet (Hardcore)"
        self.level_length = 3200.0

        # Narrow islands over lava pits
        self._add_ground_span(0, 18)
        self._record_pit(18, 22)

        self._add_ground_span(22, 35)
        self._record_pit(35, 39)

        self._add_ground_span(39, 52)
        self._record_pit(52, 57)

        self._add_ground_span(57, 80)
        self._record_pit(80, 84)

        self._add_ground_span(84, 120)

        # Tricky pipes
        self.blocks.append(Pipe(26 * TILE_SIZE, GROUND_Y - 3 * TILE_SIZE, height_tiles=3))
        self.blocks.append(Pipe(44 * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE, height_tiles=4))
        self.blocks.append(Pipe(68 * TILE_SIZE, GROUND_Y - 3 * TILE_SIZE, height_tiles=3))

        # Elevated platform steps
        for px in range(29, 34):
            self.blocks.append(BrickBlock(px * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))

        for px in range(60, 66):
            self.blocks.append(QuestionBlock(px * TILE_SIZE, GROUND_Y - 4 * TILE_SIZE))

        # Heavy enemy patrols
        self.enemies.append(Goomba(14 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(24 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Koopa(31 * TILE_SIZE, GROUND_Y - 40))
        self.enemies.append(Goomba(41 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(48 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Koopa(63 * TILE_SIZE, GROUND_Y - 40))
        self.enemies.append(Goomba(72 * TILE_SIZE, GROUND_Y - 32))
        self.enemies.append(Goomba(75 * TILE_SIZE, GROUND_Y - 32))

        # Flagpole & Castle
        flag_x = 95 * TILE_SIZE
        self.flagpole = Flagpole(flag_x, GROUND_Y)
        self.castle = Castle(flag_x + 130, GROUND_Y)
        self.blocks.append(self.flagpole)
        self.blocks.append(self.castle)
