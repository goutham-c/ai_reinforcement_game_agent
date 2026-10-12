# 🍄 Super Mario Bros: Self-Learning AI & Self-Play Framework

An autonomous, self-learning Artificial Intelligence framework and game simulation built from the ground up with **Reinforcement Learning (RL)**, **Neuroevolution**, and **Generational Self-Play**.

Watch the AI evolve from **Gen 0** (random flailing, running into Goombas, falling into pits) into an agile, obstacle-vaulting, enemy-stomping speedrunner that races against its own past generations!

---

## 🌟 Key Features

1. **Complete Custom Mario Bros Game Engine**:
   - Built from scratch in pure Python with **Pygame** and procedural pixel art.
   - **Authentic NES Physics**: running acceleration, sprint momentum, variable-height jump arcs, ground friction, and terminal velocity.
   - **Interactive Blocks**: breakable brick blocks with head-bump bounce, question mark (`?`) blocks with coins, and collision pipes of variable heights.
   - **Living Hazards & Enemies**:
     - **Goombas**: patrol terrain, bounce off pipes, squish into flat pancakes when stomped from above.
     - **Koopa Troopas**: stomping knocks them into shells; stationary shells can be kicked to slide at high velocity, mowing down obstacles and enemies!
     - **Lava Pits & Chasms**: fatal drops requiring calculated sprint jumps.
   - **Stage Progression & Goal**: pyramid staircases, victory flagpole with sliding flag, and end fortress/castle.

2. **Deep Sensory Perception (Mario's Brain Input)**:
   - **50-Dimensional Spatial Sensory Vector**:
     - **Spatial Vision Grid (42 cells)**: 7 columns (-1 behind to +5 ahead) by 6 rows (-3 above to +2 below) relative to Mario detecting solids (`+1.0`), enemies (`-1.0`), or clear air (`0.0`).
     - **Radar Proximity (4 features)**: distance and relative Y to the nearest alive enemy, distance and width of upcoming pit gaps.
     - **Proprioception & Kinematics (4 features)**: normalized horizontal velocity $v_x$, vertical velocity $v_y$, grounded state, and jump readiness.

3. **Pure NumPy Neural Network & Neuroevolution**:
   - Multi-Layer Perceptron (MLP) architecture: `[50 Inputs -> 32 Hidden (Tanh) -> 16 Hidden (Tanh) -> 4 Outputs (Sigmoid)]`.
   - **Action Space**: `[RIGHT, LEFT, JUMP, SPRINT]`.
   - **Evolutionary Algorithm**:
     - **Elitism**: top champions preserved untouched across generations.
     - **Tournament Selection**: picks fittest parents for reproduction.
     - **Uniform Crossover**: blends synaptic weights between successful lineages.
     - **Adaptive Gaussian Mutation**: explores novel jump timings and survival strategies.

4. **Generational Self-Play & Ghost Racing**:
   - Stores historical generation champions (`Champion Gen 0`, `Champion Gen 5`, `Champion Gen 15`, etc.).
   - **Ghost Racer**: The past champion runs alongside the active population as a semi-transparent cyan ghost, setting dynamic benchmarks!
   - **Generational Duels**: race historical generations simultaneously to visualize evolutionary leaps on a single screen!
   - **Human vs AI Race**: grab the keyboard and race your best AI model directly to the flagpole!

5. **Curriculum Learning (Progressive Challenges)**:
   - **Stage 1: Beginner Plains** (~2,200m) - gentle gaps, solitary Goombas, ideal for early generation mastery.
   - **Stage 2: Super Mario Bros World 1-1** (~3,600m) - faithful recreation with pipes, staircases, Goombas & Koopas.
   - **Stage 3: Bowser's Gauntlet (Hardcore)** (~3,200m) - tight pit jumps, dense enemy waves, and high pipes.
   - AI auto-promotes as fitness milestones or level completions are achieved!

6. **Interactive Real-Time Dashboard & Overlays**:
   - **Live HUD**: Generation, Alive count, Lead Fitness, Distance % to flagpole, and Mortality breakdown (Pits vs Enemies vs Timeouts).
   - **Neural Brain Visualizer (`[N]`)**: Animated live display of input activations, hidden neurons glowing by intensity, and output motor buttons firing.
   - **Death Tracker**: Visual mortality markers along the course showing where past generations failed.

7. **Dual Platform Support**:
   - **Native Python Desktop App** (`main.py` via Pygame).
   - **Zero-Install Web Browser Client** (`web/index.html` with Canvas graphics and client-side JavaScript neuroevolution).

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Pygame & NumPy:
  ```bash
  pip install pygame numpy
  ```

### Running the Modes

#### 1. Interactive Visual Training (Default)
Watch the population of 40 Marios learn live on screen:
```bash
python main.py --mode train
```

#### 2. Headless Turbo Training (Ultra-Fast)
Train 20 generations in just a few seconds without graphics overhead:
```bash
python main.py --mode headless --generations 20
```

#### 3. Generational Self-Play Race
Watch historical champions (e.g., Gen 0 vs Gen 5 vs Best AI) race head-to-head:
```bash
python main.py --mode race
```

#### 4. Champion Replay
Watch the all-time best AI navigate the stage smoothly:
```bash
python main.py --mode replay
```

#### 5. Human Play vs AI Champion
Take control of Mario and race head-to-head against the AI:
```bash
python main.py --mode play
```

#### 6. In-Browser Web Version
Simply open `web/index.html` in any web browser!

---

## 🎮 Keyboard Controls (Desktop Pygame App)

| Key | Action |
|---|---|
| `[SPACE]` | Pause / Resume simulation |
| `[1]` - `[5]` | Set simulation speed (`1x`, `2x`, `5x`, `10x`, `20x`) |
| `[H]` | Fast-forward 10 generations in headless turbo mode |
| `[N]` | Toggle Real-Time Neural Network Brain visualizer overlay |
| `[G]` | Toggle Ghost Champion racer (Self-Play) |
| `[P]` | Cycle mode (`Training` ➔ `Champion Replay` ➔ `Race` ➔ `Human Play`) |
| `[C]` | Cycle Curriculum Challenge Stage (Stage 1 ➔ 2 ➔ 3) |
| `[S]` | Save evolution checkpoint to `checkpoints/` |
| `[L]` | Load evolution checkpoint from `checkpoints/` |
| `[R]` | Reset current generation |
| `[ESC]` | Quit application |

*In Human Play mode*:
- `[Arrow Keys]` or `[WASD]`: Move Left / Right
- `[SPACE]` or `[UP]` or `[W]`: Jump
- `[SHIFT]`: Sprint / Run

---

## 🧠 Evolutionary Fitness Formula

Each agent's fitness $F$ is evaluated upon death or course completion:

$$F = \max\left(0, \; D + B_{\text{speed}} + 300 \cdot N_{\text{stomps}} + 100 \cdot N_{\text{coins}} + B_{\text{goal}} - P_{\text{death}} - P_{\text{timeout}}\right)$$

Where:
- $D = \max(0, x_{\max} - x_{\text{spawn}})$: Total horizontal distance traversed.
- $B_{\text{speed}} = \left(\frac{x_{\max}}{\text{frames}}\right) \times 12$: Velocity bonus rewarding decisive, swift movement over stalling.
- $N_{\text{stomps}}$: Number of Goombas squished or Koopas kicked.
- $B_{\text{goal}} = 6000$: Massive reward for reaching the flagpole.
- $P_{\text{death}} = 60$: Penalty for falling in pits or getting touched by enemies.
- $P_{\text{timeout}} = 40$: Penalty for standing idle without forward progress for > 3 seconds.

---

## 📁 Repository Structure

```
aiproject/
├── main.py                     # Primary launcher (train, headless, race, replay, play)
├── README.md                   # Full guide, controls, architecture, and mathematics
├── game/
│   ├── constants.py            # Physics constants, tile dimensions, palettes
│   ├── sound.py                # Procedural 8-bit retro sound synthesizer (NumPy waveforms)
│   ├── sprites.py              # Procedural pixel-art generator (Mario, Goomba, Koopa, tiles)
│   ├── blocks.py               # Ground, Brick, Question Block, Pipe, Flagpole, Castle
│   ├── entities.py             # Goombas, Koopas (sliding shells), Coins, Floating Text
│   ├── player.py               # Authentic Mario physics, variable jumping, collision resolution
│   ├── level.py                # Stage 1 (Tutorial), Stage 2 (World 1-1), Stage 3 (Bowser Gauntlet)
│   └── environment.py          # Gymnasium-style multi-agent & single-agent simulation engine
├── ai/
│   ├── neural_network.py       # NumPy MLP with live activation logging
│   ├── sensors.py              # 50-dimensional observation extractor (grid vision + radar + kinematics)
│   ├── genome.py               # Chromosome representation, crossover, and Gaussian mutation
│   ├── neuroevolution.py       # Population manager, tournament selection, elitism, checkpointing
│   ├── self_play.py            # Self-Play arena, historical ghost racers, and duel leagues
│   └── curriculum.py           # Curriculum auto-advancement manager
├── ui/
│   ├── hud.py                  # High-fidelity on-screen HUD (generation telemetry & stats)
│   ├── neural_visualizer.py    # Animated real-time neural network brain diagram
│   └── death_tracker.py        # Graveyard death markers across the terrain
├── web/
│   ├── index.html              # Standalone web browser HTML5 client
│   ├── style.css               # Modern dark-mode UI stylesheet
│   └── mario_ai.js             # Complete JavaScript port of the game & Neuroevolution engine
└── checkpoints/                # Saved champion models and evolution history JSONs
```
"# mlshit" 
