/**
 * Mario Bros Self-Learning AI & Self-Play Framework in JavaScript / HTML5 Canvas.
 * Complete in-browser client engine matching the Python Pygame implementation.
 */

// Canvas & Contexts
const gameCanvas = document.getElementById("gameCanvas");
const ctx = gameCanvas.getContext("2d");
const brainCanvas = document.getElementById("brainCanvas");
const brainCtx = brainCanvas.getContext("2d");

// Constants
const TILE_SIZE = 32;
const GROUND_Y = 448;
const GRAVITY = 0.55;
const TERM_VEL = 11.0;
const WALK_ACCEL = 0.35;
const RUN_ACCEL = 0.55;
const MAX_WALK = 3.6;
const MAX_RUN = 6.2;
const FRICTION = 0.86;
const JUMP_VEL = -10.8;
const POP_SIZE = 40;

// Colors
const COLOR_SKY = "#5c94fc";
const COLOR_GROUND = "#c84c0c";
const COLOR_BRICK = "#b83410";
const COLOR_QUESTION = "#fc9838";
const COLOR_PIPE = "#00a800";
const COLOR_PIPE_DARK = "#006800";
const COLOR_GOOMBA = "#a84600";
const COLOR_KOOPA = "#00b400";

// Simulation State
let stage = 1;
let speed = 1;
let isPaused = false;
let isHumanPlay = false;
let generation = 0;
let frameCount = 0;
let cameraX = 0;
let deathMarkers = [];

// DOM Elements
const valGen = document.getElementById("valGen");
const valStage = document.getElementById("valStage");
const valAlive = document.getElementById("valAlive");
const valBestFit = document.getElementById("valBestFit");
const valAllTimeFit = document.getElementById("valAllTimeFit");
const valDist = document.getElementById("valDist");
const valDeaths = document.getElementById("valDeaths");
const speedSlider = document.getElementById("speedSlider");
const speedLabel = document.getElementById("speedLabel");

// ==================== NEURAL NETWORK ====================
class NeuralNet {
  constructor(layerSizes = [50, 32, 16, 4]) {
    this.layerSizes = layerSizes;
    this.weights = [];
    this.biases = [];
    this.lastActivations = [];

    for (let i = 0; i < layerSizes.length - 1; i++) {
      const fanIn = layerSizes[i];
      const fanOut = layerSizes[i + 1];
      const scale = Math.sqrt(2.0 / fanIn);
      const w = [];
      for (let r = 0; r < fanIn; r++) {
        const row = [];
        for (let c = 0; c < fanOut; c++) {
          row.push((Math.random() * 2 - 1) * scale);
        }
        w.push(row);
      }
      this.weights.push(w);
      this.biases.push(new Array(fanOut).fill(0));
    }
  }

  forward(x) {
    let a = [...x];
    this.lastActivations = [[...a]];

    for (let l = 0; l < this.weights.length - 1; l++) {
      const nextA = [];
      const w = this.weights[l];
      const b = this.biases[l];
      for (let j = 0; j < this.layerSizes[l + 1]; j++) {
        let sum = b[j];
        for (let i = 0; i < a.length; i++) {
          sum += a[i] * w[i][j];
        }
        nextA.push(Math.tanh(sum));
      }
      a = nextA;
      this.lastActivations.push([...a]);
    }

    // Output layer with Sigmoid
    const lastL = this.weights.length - 1;
    const out = [];
    const w = this.weights[lastL];
    const b = this.biases[lastL];
    for (let j = 0; j < this.layerSizes[lastL + 1]; j++) {
      let sum = b[j];
      for (let i = 0; i < a.length; i++) {
        sum += a[i] * w[i][j];
      }
      out.push(1 / (1 + Math.exp(-Math.max(-15, Math.min(15, sum)))));
    }
    this.lastActivations.push([...out]);
    return out;
  }

  getActions(x) {
    const out = this.forward(x);
    let right = out[0] > 0.5;
    let left = out[1] > 0.5;
    const jump = out[2] > 0.5;
    const run = out[3] > 0.5;
    if (right && left) {
      if (out[0] > out[1]) left = false;
      else right = false;
    }
    return [right, left, jump, run];
  }

  clone() {
    const net = new NeuralNet(this.layerSizes);
    net.weights = this.weights.map(layer => layer.map(row => [...row]));
    net.biases = this.biases.map(b => [...b]);
    return net;
  }
}

// ==================== GENOME ====================
class Genome {
  constructor(net = null, gen = 0) {
    this.network = net || new NeuralNet();
    this.generation = gen;
    this.fitness = 0;
    this.maxDist = 0;
    this.won = false;
    this.deathCause = null;
    this.enemiesStomped = 0;
    this.coins = 0;
  }

  mutate(rate = 0.15, sigma = 0.25) {
    for (let l = 0; l < this.network.weights.length; l++) {
      const w = this.network.weights[l];
      for (let r = 0; r < w.length; r++) {
        for (let c = 0; c < w[r].length; c++) {
          if (Math.random() < rate) {
            w[r][c] += (Math.random() * 2 - 1) * sigma;
            if (Math.random() < 0.02) w[r][c] = (Math.random() * 2 - 1) * 0.5;
            w[r][c] = Math.max(-8, Math.min(8, w[r][c]));
          }
        }
      }
      const b = this.network.biases[l];
      for (let c = 0; c < b.length; c++) {
        if (Math.random() < rate) {
          b[c] += (Math.random() * 2 - 1) * sigma;
        }
      }
    }
  }

  crossover(partner) {
    const childNet = this.network.clone();
    for (let l = 0; l < childNet.weights.length; l++) {
      const w = childNet.weights[l];
      const pW = partner.network.weights[l];
      for (let r = 0; r < w.length; r++) {
        for (let c = 0; c < w[r].length; c++) {
          if (Math.random() < 0.5) {
            w[r][c] = pW[r][c];
          }
        }
      }
    }
    return new Genome(childNet, this.generation + 1);
  }

  clone() {
    const g = new Genome(this.network.clone(), this.generation);
    g.fitness = this.fitness;
    g.maxDist = this.maxDist;
    g.won = this.won;
    return g;
  }
}

// ==================== MARIO PLAYER ====================
class Player {
  constructor(tint = null, alpha = 1.0) {
    this.tint = tint;
    this.alpha = alpha;
    this.reset();
  }

  reset() {
    this.x = 80;
    this.y = GROUND_Y - 40;
    this.w = 24;
    this.h = 32;
    this.vx = 0;
    this.vy = 0;
    this.isGrounded = false;
    this.isJumping = false;
    this.isDead = false;
    this.deathCause = null;
    this.won = false;
    this.facingRight = true;
    this.maxX = 80;
    this.framesAlive = 0;
    this.idleFrames = 0;
    this.enemiesStomped = 0;
    this.coins = 0;
    this.fitness = 0;
  }

  applyAction(right, left, jump, run) {
    if (this.isDead || this.won) return;
    const accel = run ? RUN_ACCEL : WALK_ACCEL;
    const maxSpd = run ? MAX_RUN : MAX_WALK;

    if (right && !left) {
      this.vx = Math.min(this.vx + accel, maxSpd);
      this.facingRight = true;
    } else if (left && !right) {
      this.vx = Math.max(this.vx - accel, -maxSpd);
      this.facingRight = false;
    } else {
      this.vx *= FRICTION;
      if (Math.abs(this.vx) < 0.05) this.vx = 0;
    }

    if (jump && this.isGrounded) {
      this.vy = JUMP_VEL;
      this.isGrounded = false;
      this.isJumping = true;
    }
  }

  update(blocks, enemies, flagpole) {
    if (this.isDead) return;
    this.framesAlive++;
    this.vy = Math.min(this.vy + GRAVITY, TERM_VEL);

    // Horizontal Move & Collide
    this.x += this.vx;
    for (const b of blocks) {
      if (b.solid && this.collides(b)) {
        if (this.vx > 0) {
          this.x = b.x - this.w;
          this.vx = 0;
        } else if (this.vx < 0) {
          this.x = b.x + b.w;
          this.vx = 0;
        }
      }
    }

    // Vertical Move & Collide
    this.y += this.vy;
    this.isGrounded = false;
    for (const b of blocks) {
      if (b.solid && this.collides(b)) {
        if (this.vy > 0) {
          this.y = b.y - this.h;
          this.vy = 0;
          this.isGrounded = true;
          this.isJumping = false;
        } else if (this.vy < 0) {
          this.y = b.y + b.h;
          this.vy = 0;
          if (b.bump) b.bump();
        }
      }
    }

    // Enemy Collisions
    for (const e of enemies) {
      if (!e.alive) continue;
      if (this.collides(e)) {
        if (this.vy > 0 && this.y + this.h <= e.y + 16) {
          e.alive = false;
          this.vy = -7.5;
          this.enemiesStomped++;
        } else {
          this.die("enemy");
          return;
        }
      }
    }

    // Pit Death
    if (this.y > 540) {
      this.die("pit");
      return;
    }

    // Flagpole Goal
    if (flagpole && !this.won && this.collides(flagpole)) {
      this.won = true;
    }

    // Idle Timer
    if (this.x > this.maxX + 2) {
      this.maxX = this.x;
      this.idleFrames = 0;
    } else {
      this.idleFrames++;
      if (this.idleFrames > 180) {
        this.die("timeout");
      }
    }
  }

  collides(r) {
    return (
      this.x < r.x + r.w &&
      this.x + this.w > r.x &&
      this.y < r.y + r.h &&
      this.y + this.h > r.y
    );
  }

  die(cause) {
    if (!this.isDead && !this.won) {
      this.isDead = true;
      this.deathCause = cause;
      deathMarkers.push({ x: this.x, y: this.y, cause });
      if (deathMarkers.length > 150) deathMarkers.shift();
    }
  }

  calcFitness() {
    const dist = Math.max(0, this.maxX - 80);
    const speed = (this.maxX / Math.max(1, this.framesAlive)) * 12;
    const stomps = this.enemiesStomped * 300;
    const winBonus = this.won ? 6000 : 0;
    const deathPen = (this.isDead && !this.won) ? -60 : 0;
    this.fitness = Math.max(0, dist + speed + stomps + winBonus + deathPen);
    return this.fitness;
  }

  draw(ctx, camX) {
    const dx = this.x - camX;
    if (dx < -40 || dx > 1000) return;

    ctx.save();
    ctx.globalAlpha = this.alpha;

    const red = this.tint || "#e40058";
    const skin = "#fca044";
    const blue = "#0044dc";
    const brown = "#684600";

    if (this.isDead) {
      ctx.fillStyle = red;
      ctx.fillRect(dx + 6, this.y, 12, 16);
      ctx.fillStyle = skin;
      ctx.fillRect(dx + 4, this.y + 6, 16, 10);
    } else {
      // Hat
      ctx.fillStyle = red;
      ctx.fillRect(dx + 7, this.y + 2, 12, 5);
      // Face
      ctx.fillStyle = skin;
      ctx.fillRect(dx + 7, this.y + 7, 12, 8);
      // Hair & mustache
      ctx.fillStyle = brown;
      ctx.fillRect(dx + (this.facingRight ? 13 : 5), this.y + 11, 6, 3);
      // Shirt
      ctx.fillStyle = red;
      ctx.fillRect(dx + 5, this.y + 15, 14, 8);
      // Overalls
      ctx.fillStyle = blue;
      ctx.fillRect(dx + 6, this.y + 22, 12, 6);
      // Shoes
      ctx.fillStyle = brown;
      ctx.fillRect(dx + 4, this.y + 27, 7, 5);
      ctx.fillRect(dx + 13, this.y + 27, 7, 5);
    }
    ctx.restore();
  }
}

// ==================== LEVEL GENERATOR ====================
function createLevel(stageNum) {
  const blocks = [];
  const enemies = [];
  const pits = [];
  let length = 2200;

  function addGround(startT, endT) {
    for (let tx = startT; tx < endT; tx++) {
      const x = tx * TILE_SIZE;
      blocks.push({ x, y: GROUND_Y, w: TILE_SIZE, h: TILE_SIZE, solid: true, type: "ground" });
      blocks.push({ x, y: GROUND_Y + TILE_SIZE, w: TILE_SIZE, h: TILE_SIZE, solid: true, type: "ground" });
    }
  }

  function addPipe(tileX, heightTiles) {
    const x = tileX * TILE_SIZE;
    const h = heightTiles * TILE_SIZE;
    const y = GROUND_Y - h;
    blocks.push({ x, y, w: 64, h, solid: true, type: "pipe", heightTiles });
  }

  if (stageNum === 1) {
    length = 2200;
    addGround(0, 22);
    pits.push([22 * TILE_SIZE, 24 * TILE_SIZE]);
    addGround(24, 45);
    pits.push([45 * TILE_SIZE, 48 * TILE_SIZE]);
    addGround(48, 75);

    addPipe(28, 2);
    addPipe(38, 3);

    enemies.push({ x: 12 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 33 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 54 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
  } else if (stageNum === 2) {
    length = 3600;
    addGround(0, 69);
    pits.push([69 * TILE_SIZE, 71 * TILE_SIZE]);
    addGround(71, 86);
    pits.push([86 * TILE_SIZE, 89 * TILE_SIZE]);
    addGround(89, 155);

    addPipe(28, 2);
    addPipe(38, 3);
    addPipe(46, 4);

    enemies.push({ x: 22 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 41 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 52 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 82 * TILE_SIZE, y: GROUND_Y - 36, w: 28, h: 36, alive: true, vx: -1.4, type: "koopa" });
  } else {
    length = 3200;
    addGround(0, 18);
    pits.push([18 * TILE_SIZE, 22 * TILE_SIZE]);
    addGround(22, 35);
    pits.push([35 * TILE_SIZE, 39 * TILE_SIZE]);
    addGround(39, 52);
    pits.push([52 * TILE_SIZE, 57 * TILE_SIZE]);
    addGround(57, 100);

    addPipe(26, 3);
    addPipe(44, 4);

    enemies.push({ x: 14 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 24 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
    enemies.push({ x: 31 * TILE_SIZE, y: GROUND_Y - 36, w: 28, h: 36, alive: true, vx: -1.4, type: "koopa" });
    enemies.push({ x: 48 * TILE_SIZE, y: GROUND_Y - 28, w: 28, h: 28, alive: true, vx: -1.2, type: "goomba" });
  }

  const flagX = (stageNum === 1 ? 65 : (stageNum === 2 ? 135 : 90)) * TILE_SIZE;
  const flagpole = { x: flagX, y: GROUND_Y - 320, w: 48, h: 320, solid: false, type: "flag" };
  const castle = { x: flagX + 120, y: GROUND_Y - 160, w: 160, h: 160, solid: false, type: "castle" };

  return { blocks, enemies, pits, flagpole, castle, length };
}

// ==================== SENSORS ====================
function extractObservation(player, level) {
  const obs = new Array(50).fill(0);
  const mtx = Math.floor(player.x / TILE_SIZE);
  const mty = Math.floor(player.y / TILE_SIZE);

  let idx = 0;
  const colOffsets = [-1, 0, 1, 2, 3, 4, 5];
  const rowOffsets = [-3, -2, -1, 0, 1, 2];

  for (const ro of rowOffsets) {
    const ty = mty + ro;
    for (const co of colOffsets) {
      const tx = mtx + co;
      const cx = tx * TILE_SIZE;
      const cy = ty * TILE_SIZE;
      let val = 0;

      for (const b of level.blocks) {
        if (b.solid && b.x <= cx && cx < b.x + b.w && b.y <= cy && cy < b.y + b.h) {
          val = 1;
          break;
        }
      }

      if (val === 0) {
        for (const e of level.enemies) {
          if (e.alive && Math.abs(e.x - cx) < 20 && Math.abs(e.y - cy) < 20) {
            val = -1;
            break;
          }
        }
      }
      obs[idx++] = val;
    }
  }

  // Nearest enemy radar
  let minDx = 9999;
  let eDist = 1;
  let eDy = 0;
  for (const e of level.enemies) {
    if (!e.alive) continue;
    const dx = e.x - player.x;
    if (dx >= 0 && dx < 360 && dx < minDx) {
      minDx = dx;
      eDist = dx / 360;
      eDy = Math.max(-1, Math.min(1, (e.y - player.y) / 120));
    }
  }
  obs[42] = eDist;
  obs[43] = eDy;

  // Pit radar
  let pitDist = 1;
  let pitWidth = 0;
  for (const [pStart, pEnd] of level.pits) {
    const dx = pStart - (player.x + player.w);
    if (dx >= 0 && dx < 360) {
      pitDist = dx / 360;
      pitWidth = Math.min(1, (pEnd - pStart) / 128);
      break;
    }
  }
  obs[44] = pitDist;
  obs[45] = pitWidth;

  // Kinematics
  obs[46] = Math.max(-1, Math.min(1, player.vx / MAX_RUN));
  obs[47] = Math.max(-1, Math.min(1, player.vy / TERM_VEL));
  obs[48] = player.isGrounded ? 1 : 0;
  obs[49] = (player.isGrounded && !player.isJumping) ? 1 : 0;

  return obs;
}

// ==================== ENGINE & POPULATION ====================
let level = createLevel(stage);
let population = Array.from({ length: POP_SIZE }, () => new Genome(new NeuralNet(), 0));
let players = population.map((_, i) => new Player(i === 0 ? "#ffcc00" : null, i < 3 ? 1.0 : 0.6));
let allTimeChamp = null;
let ghostChampPlayer = null;
let humanPlayer = new Player("#ef4444", 1.0);

// Keyboard controls for Human Play mode
const keys = {};
window.addEventListener("keydown", (e) => {
  keys[e.key] = true;
  if (e.key === " ") {
    if (!isHumanPlay) isPaused = !isPaused;
  }
  if (e.key.toLowerCase() === "p") toggleHumanPlay();
  if (e.key.toLowerCase() === "c") cycleStage();
});
window.addEventListener("keyup", (e) => { keys[e.key] = false; });

function evolveNextGen() {
  // 1. Calculate fitness
  players.forEach((p, i) => {
    population[i].fitness = p.calcFitness();
    population[i].maxDist = p.maxX;
    population[i].won = p.won;
    population[i].deathCause = p.deathCause;
  });

  population.sort((a, b) => b.fitness - a.fitness);

  const best = population[0].clone();
  if (!allTimeChamp || best.fitness > allTimeChamp.fitness) {
    allTimeChamp = best.clone();
  }

  // Self-play ghost setup
  ghostChampPlayer = new Player("#7dd3fc", 0.55);

  // Stats update
  const bestFit = population[0].fitness;
  const avgFit = population.reduce((acc, g) => acc + g.fitness, 0) / POP_SIZE;
  valGen.innerText = `GEN ${generation}`;
  valBestFit.innerText = bestFit.toFixed(1);
  valAllTimeFit.innerText = allTimeChamp.fitness.toFixed(1);

  // Curriculum progression
  if ((best.won || bestFit > (stage === 1 ? 2000 : 4000)) && stage < 3) {
    stage++;
    valStage.innerText = `Stage ${stage}`;
  }

  // Reproduction (Elitism + Tournament + Crossover + Mutation)
  const newPop = [];
  const eliteCount = 3;
  for (let i = 0; i < eliteCount; i++) {
    const elite = population[i].clone();
    elite.generation = generation + 1;
    newPop.push(elite);
  }

  while (newPop.length < POP_SIZE) {
    const cand1 = population.slice(0, 12)[Math.floor(Math.random() * 12)];
    const cand2 = population.slice(0, 12)[Math.floor(Math.random() * 12)];
    const p1 = cand1.fitness > cand2.fitness ? cand1 : cand2;

    const cand3 = population.slice(0, 12)[Math.floor(Math.random() * 12)];
    const cand4 = population.slice(0, 12)[Math.floor(Math.random() * 12)];
    const p2 = cand3.fitness > cand4.fitness ? cand3 : cand4;

    const child = Math.random() < 0.75 ? p1.crossover(p2) : p1.clone();
    child.mutate(0.15, 0.25);
    child.generation = generation + 1;
    newPop.push(child);
  }

  population = newPop;
  generation++;

  // Reset World
  level = createLevel(stage);
  players = population.map((_, i) => new Player(i === 0 ? "#ffcc00" : null, i < 3 ? 1.0 : 0.6));
  frameCount = 0;
  cameraX = 0;
}

function updateSim() {
  frameCount++;

  // Update enemies
  for (const e of level.enemies) {
    if (!e.alive) continue;
    e.x += e.vx;
    for (const b of level.blocks) {
      if (b.solid && e.x < b.x + b.w && e.x + e.w > b.x && e.y < b.y + b.h && e.y + e.h > b.y) {
        e.vx = -e.vx;
      }
    }
  }

  if (isHumanPlay) {
    const r = keys["ArrowRight"] || keys["d"];
    const l = keys["ArrowLeft"] || keys["a"];
    const j = keys["ArrowUp"] || keys["w"] || keys[" "];
    const run = keys["Shift"];
    humanPlayer.applyAction(r, l, j, run);
    humanPlayer.update(level.blocks, level.enemies, level.flagpole);

    if (ghostChampPlayer && allTimeChamp && !ghostChampPlayer.isDead) {
      const obs = extractObservation(ghostChampPlayer, level);
      const act = allTimeChamp.network.getActions(obs);
      ghostChampPlayer.applyAction(...act);
      ghostChampPlayer.update(level.blocks, level.enemies, level.flagpole);
    }
    cameraX += (Math.max(0, humanPlayer.x - 300) - cameraX) * 0.1;
    if (humanPlayer.isDead) humanPlayer.reset();
    return;
  }

  // AI Population step
  let anyAlive = false;
  let leadX = 0;

  players.forEach((p, idx) => {
    if (!p.isDead && !p.won) {
      anyAlive = true;
      const obs = extractObservation(p, level);
      const act = population[idx].network.getActions(obs);
      p.applyAction(...act);
      p.update(level.blocks, level.enemies, level.flagpole);
    }
    if (p.x > leadX) leadX = p.x;
  });

  // Ghost racer step
  if (ghostChampPlayer && allTimeChamp && !ghostChampPlayer.isDead && !ghostChampPlayer.won) {
    const obs = extractObservation(ghostChampPlayer, level);
    const act = allTimeChamp.network.getActions(obs);
    ghostChampPlayer.applyAction(...act);
    ghostChampPlayer.update(level.blocks, level.enemies, level.flagpole);
  }

  cameraX += (Math.max(0, leadX - 300) - cameraX) * 0.1;

  if (!anyAlive) {
    evolveNextGen();
  }
}

// ==================== RENDERING ====================
function render() {
  ctx.fillStyle = COLOR_SKY;
  ctx.fillRect(0, 0, gameCanvas.width, gameCanvas.height);

  // Scenery clouds & hills
  ctx.fillStyle = "#ffffff";
  for (let cx = 100; cx < level.length; cx += 500) {
    const dx = cx - cameraX * 0.3;
    ctx.beginPath();
    ctx.arc(dx, 80, 24, 0, Math.PI * 2);
    ctx.arc(dx + 25, 75, 30, 0, Math.PI * 2);
    ctx.arc(dx + 50, 80, 24, 0, Math.PI * 2);
    ctx.fill();
  }

  // Blocks & Pipes
  for (const b of level.blocks) {
    const dx = b.x - cameraX;
    if (dx < -64 || dx > 1000) continue;

    if (b.type === "ground") {
      ctx.fillStyle = COLOR_GROUND;
      ctx.fillRect(dx, b.y, b.w, b.h);
      ctx.strokeStyle = "#882800";
      ctx.strokeRect(dx, b.y, b.w, b.h);
    } else if (b.type === "pipe") {
      ctx.fillStyle = COLOR_PIPE;
      ctx.fillRect(dx, b.y, b.w, b.h);
      ctx.strokeStyle = COLOR_PIPE_DARK;
      ctx.lineWidth = 2;
      ctx.strokeRect(dx, b.y, b.w, b.h);
      ctx.fillStyle = "#80d010";
      ctx.fillRect(dx + 6, b.y + 4, 8, b.h - 8);
    }
  }

  // Flagpole & Castle
  if (level.flagpole) {
    const fdx = level.flagpole.x - cameraX;
    ctx.fillStyle = "#d8d8d8";
    ctx.fillRect(fdx + 13, level.flagpole.y + 20, 6, level.flagpole.h - 20);
    ctx.fillStyle = "#fcd800";
    ctx.beginPath();
    ctx.arc(fdx + 16, level.flagpole.y + 12, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#00b400";
    ctx.beginPath();
    ctx.moveTo(fdx + 13, level.flagpole.y + 24);
    ctx.lineTo(fdx + 46, level.flagpole.y + 36);
    ctx.lineTo(fdx + 13, level.flagpole.y + 48);
    ctx.fill();
  }

  if (level.castle) {
    const cdx = level.castle.x - cameraX;
    ctx.fillStyle = "#b84c20";
    ctx.fillRect(cdx + 20, level.castle.y + 60, 120, 100);
    ctx.fillStyle = "#000000";
    ctx.fillRect(cdx + 64, level.castle.y + 108, 32, 52);
  }

  // Enemies
  for (const e of level.enemies) {
    if (!e.alive) continue;
    const edx = e.x - cameraX;
    ctx.fillStyle = e.type === "koopa" ? COLOR_KOOPA : COLOR_GOOMBA;
    ctx.beginPath();
    ctx.ellipse(edx + 14, e.y + 12, 12, 10, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(edx + 8, e.y + 8, 3, 5);
    ctx.fillRect(edx + 17, e.y + 8, 3, 5);
    ctx.fillStyle = "#000000";
    ctx.fillRect(edx + 9, e.y + 9, 2, 4);
    ctx.fillRect(edx + 17, e.y + 9, 2, 4);
  }

  // Death Markers
  for (const dm of deathMarkers) {
    const dmx = dm.x - cameraX;
    if (dmx > -20 && dmx < 1000) {
      ctx.strokeStyle = dm.cause === "pit" ? "#ef4444" : "#f59e0b";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(dmx - 4, dm.y - 4);
      ctx.lineTo(dmx + 4, dm.y + 4);
      ctx.moveTo(dmx + 4, dm.y - 4);
      ctx.lineTo(dmx - 4, dm.y + 4);
      ctx.stroke();
    }
  }

  // Ghost racer
  if (ghostChampPlayer && !ghostChampPlayer.isDead) {
    ghostChampPlayer.draw(ctx, cameraX);
  }

  // Players
  if (isHumanPlay) {
    humanPlayer.draw(ctx, cameraX);
  } else {
    players.forEach(p => p.draw(ctx, cameraX));
  }

  // Update UI Stats
  const aliveCnt = players.filter(p => !p.isDead && !p.won).length;
  valAlive.innerText = `${aliveCnt} / ${POP_SIZE}`;
  const leadX = Math.max(...players.map(p => p.x));
  const pct = Math.min(100, (leadX / level.length) * 100).toFixed(1);
  valDist.innerText = `${leadX.toFixed(0)}m / ${level.length}m (${pct}%)`;

  renderBrainVisualizer();
}

function renderBrainVisualizer() {
  brainCtx.fillStyle = "#0b1120";
  brainCtx.fillRect(0, 0, brainCanvas.width, brainCanvas.height);

  let activeNet = null;
  if (!isHumanPlay && players.length > 0) {
    const aliveP = players.filter(p => !p.isDead);
    const topIdx = aliveP.length > 0 ? players.indexOf(aliveP[0]) : 0;
    activeNet = population[topIdx]?.network;
  } else if (allTimeChamp) {
    activeNet = allTimeChamp.network;
  }

  if (!activeNet || !activeNet.lastActivations || activeNet.lastActivations.length === 0) return;

  const acts = activeNet.lastActivations;
  const colXs = [25, 95, 175, 255];
  const labels = ["R", "L", "J", "S"];

  // Synapses
  for (let l = 0; l < activeNet.weights.length; l++) {
    const w = activeNet.weights[l];
    const x1 = colXs[l];
    const x2 = colXs[l + 1];
    const count1 = Math.min(6, activeNet.layerSizes[l]);
    const count2 = Math.min(6, activeNet.layerSizes[l + 1]);

    for (let i = 0; i < count1; i++) {
      const y1 = 30 + (i * (150 / (count1 - 1 || 1)));
      for (let j = 0; j < count2; j++) {
        const y2 = 30 + (j * (150 / (count2 - 1 || 1)));
        const val = w[i][j];
        if (Math.abs(val) > 0.4) {
          brainCtx.strokeStyle = val > 0 ? "rgba(16, 185, 129, 0.4)" : "rgba(239, 68, 68, 0.4)";
          brainCtx.lineWidth = 1;
          brainCtx.beginPath();
          brainCtx.moveTo(x1, y1);
          brainCtx.lineTo(x2, y2);
          brainCtx.stroke();
        }
      }
    }
  }

  // Neurons
  acts.forEach((act, l) => {
    const x = colXs[l];
    const count = Math.min(6, act.length);
    for (let i = 0; i < count; i++) {
      const y = 30 + (i * (150 / (count - 1 || 1)));
      const v = act[i];
      const intensity = Math.floor(Math.max(0, Math.min(1, l < 3 ? (v + 1) * 0.5 : v)) * 255);
      brainCtx.fillStyle = `rgb(${intensity}, ${intensity * 0.8}, ${255 - intensity})`;
      brainCtx.beginPath();
      brainCtx.arc(x, y, l === 3 ? 7 : 5, 0, Math.PI * 2);
      brainCtx.fill();

      if (l === 3) {
        brainCtx.fillStyle = v > 0.5 ? "#10b981" : "#94a3b8";
        brainCtx.font = "bold 10px monospace";
        brainCtx.fillText(`${labels[i]} ${(v).toFixed(2)}`, x - 20, y + 3);
      }
    }
  });
}

// ==================== LOOP & CONTROLS ====================
function loop() {
  if (!isPaused) {
    for (let s = 0; s < speed; s++) {
      updateSim();
    }
  }
  render();
  requestAnimationFrame(loop);
}

// Button Hooks
document.getElementById("btnPause").onclick = () => {
  isPaused = !isPaused;
  document.getElementById("btnPause").innerText = isPaused ? "Resume [Space]" : "Pause [Space]";
};

document.getElementById("btnNextGen").onclick = () => evolveNextGen();

document.getElementById("btnFastForward").onclick = () => {
  for (let g = 0; g < 10; g++) {
    for (let f = 0; f < 1000; f++) {
      updateSim();
      if (!players.some(p => !p.isDead && !p.won)) break;
    }
    evolveNextGen();
  }
};

function toggleHumanPlay() {
  isHumanPlay = !isHumanPlay;
  document.getElementById("btnHumanPlay").innerText = isHumanPlay ? "AI Mode [P]" : "Human Play [P]";
  if (isHumanPlay) humanPlayer.reset();
}
document.getElementById("btnHumanPlay").onclick = toggleHumanPlay;

function cycleStage() {
  stage = (stage % 3) + 1;
  valStage.innerText = `Stage ${stage}`;
  level = createLevel(stage);
  players.forEach(p => p.reset());
}
document.getElementById("btnStage").onclick = cycleStage;

document.getElementById("btnReset").onclick = () => {
  generation = 0;
  stage = 1;
  population = Array.from({ length: POP_SIZE }, () => new Genome(new NeuralNet(), 0));
  allTimeChamp = null;
  deathMarkers = [];
  level = createLevel(1);
  players = population.map((_, i) => new Player(i === 0 ? "#ffcc00" : null, i < 3 ? 1.0 : 0.6));
  valGen.innerText = "GEN 0";
  valStage.innerText = "Stage 1";
};

speedSlider.oninput = (e) => {
  speed = parseInt(e.target.value);
  speedLabel.innerText = `${speed}x`;
};

// Start simulation loop
loop();
