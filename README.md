# pyMaze

**Version:** `1.1.0`

### Description

**pyMaze** is an automated terminal‑based maze solver rendered in truecolor using the [Rich](https://github.com/Textualize/rich) library. The player (`S`) autonomously explores multi‑level ASCII mazes, locates the key (`K`), and navigates to the exit (`E`) while displaying live telemetry centered at the bottom of the terminal.

![pyMaze Screenshot](Image.PNG)

---

### Features

- **Dual Pathfinding Modes (`greedy` vs `astar`)**:
  - **Greedy Least‑Visited (default)** – explores neighboring corridors by selecting the least‑visited adjacent tile (`Player_count`).
  - **A\* Shortest Path (`--astar` / `-a`)** – uses A\* search with Manhattan distance heuristic to compute the optimal path from `S → K → E`.
- **10 Progressive Maps** – `map1.txt` … `map10.txt` are generated automatically with increasing obstacle density and a guaranteed exit on each level.
- **FPS Counter** – the current frames‑per‑second is shown in the status bar.
- **Full‑Terminal Responsive Scaling** – maze automatically scales to fill the active terminal dimensions while preserving wall alignment and centering the status lines.
- **Loop Switch (`--loop` / `-l`)** – continuously cycle through all 10 levels.
- **Final Animation & Restart Prompt** – after level 10 a short animation plays and the user can press **R** to restart or any other key to exit.
- **Flicker‑Free `Rich.Live` Rendering** – uses Rich's alternate‑screen Live display for smooth updates.
- **Direct O(1) Position Tracking** – tracks `PlayerIndex`, `KeyIndex`, and `ExitIndex` without scanning the whole map each frame.

---

### Pathfinding Comparison

| Algorithm | CLI Command | Level 1 Moves | Level 2 Moves |
|-----------|-------------|--------------:|--------------:|
| **Greedy** | `python main.py` | **1,054** (key at move 456) | **1,576** (key at move 698) |
| **A\*** | `python main.py --astar` | **140** (63 to K + 77 to E) | **154** (59 to K + 95 to E) |

---

### Command‑Line Options

| Flag | Long Flag | Description |
|------|-----------|-------------|
| `-a` | `--astar` | Use the **A\*** pathfinding algorithm (overrides `--pathfinding`). |
| `-p` | `--pathfinding {greedy,astar}` | Explicitly select the pathfinding algorithm. |
| `-l` | `--loop` | Loop through all maps (1‑10) continuously. |
| `-f` | `--fps <float>` | Target frames‑per‑second for rendering (default 30). |
| `-v` | `--version` | Print program version (`pyMaze 1.1.0`). |
| `-h` | `--help` | Show help message. |

---

### Map Legend & 2D File Format

Each map file (`map1.txt` … `map10.txt`) is a 25‑row by 79‑column ASCII grid:

| Symbol | Meaning |
|:------:|:--------|
| `S` | Player start / current position |
| `K` | Level key (required to unlock the exit) |
| `E` | Level exit |
| Space (` `) or `@` | Walkable corridor tile |
| `-` / `|` | Horizontal and vertical maze walls |
| `~` | Interior wall block fill |

Example snippet from `map1.txt`:
```text
-------------------------------------------------------------------------------
S                   |~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
|----- -------------|~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
|~~~~| |~~~~~~~~~~~~~~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
```
---

### How It Works

1. **Initialization (`App.init_data`)** – loads the 2D ASCII map, detects row stride, and records indices of `S`, `K`, and `E`.
2. **Rendering (`App.build_frame` & `App.draw`)** – scales rows to the terminal width, adds vertical padding, and renders a single frame via `Rich.Live`. The status bar shows valid moves, player index, move count, key status, and FPS.
3. **Movement (`App.make_move`)** – selects the next direction based on the chosen algorithm (greedy or A\*).
4. **Game Loop** – plays each level sequentially; after level 10 the final animation runs and the restart prompt appears.

---

### Installation & Usage

```bash
# Clone the repository
git clone https://github.com/Frankmau5/pyMaze.git
cd pyMaze

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run the program:
```bash
# Default greedy pathfinding (plays all 10 maps once)
python main.py

# Use A* pathfinding
python main.py --astar

# Loop through all maps continuously
python main.py --loop

# Set a custom FPS (e.g., 60)
python main.py --fps 60
```
Press `Ctrl+C` at any time to stop the simulation and restore the terminal.
