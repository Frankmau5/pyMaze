# pyMaze

**Version:** `1.1.0`

### Description

**pyMaze** is an automated terminal-based maze solver rendered in truecolor using the [Rich](https://github.com/Textualize/rich) library. The player (`S`) autonomously explores multi-level ASCII mazes, locates the key (`K`), and navigates to the exit (`E`) while displaying live telemetry centered at the bottom of the terminal.

![pyMaze Screenshot](Image.PNG)

---

### Features

- **Dual Pathfinding Modes (`greedy` vs `astar`)**:
  - **Greedy Least-Visited (`default`)**: Explores neighboring corridors by selecting the least-visited adjacent tile (`Player_count`), gradually filling dead ends and backtracking until it finds the key and exit.
  - **A\* Shortest Path (`--astar` / `-a`)**: Uses A\* search (`heapq`) with a Manhattan distance heuristic to compute the optimal path from `S` $\rightarrow$ `K` and then `K` $\rightarrow$ `E`.
- **2D Visual Map Files**: Maps (`map.txt`, `map2.txt`) are stored as human-readable 25-row by 79-column 2D ASCII grids that can be viewed and edited directly in any text editor (while remaining backwards-compatible with legacy 1-character-per-line map files).
- **Flicker-Free `Rich.Live` Rendering**: Uses Rich's alternate-screen `Live` display to atomically render each frame without tearing or scrollback clutter.
- **Full-Terminal Responsive Scaling**: Automatically scales the maze horizontally and vertically to fill the active terminal dimensions while preserving wall alignment and centering the status lines across the exact map width.
- **Direct $O(1)$ Position Tracking**: Tracks `PlayerIndex`, `KeyIndex`, and `ExitIndex` directly as the map loads and as the player moves.

---

### Pathfinding Comparison

You can compare how the two algorithms solve both levels using `python main.py` (Greedy) vs. `python main.py --astar` (A\*):

| Algorithm | CLI Command | Level 1 (`map.txt`) Moves | Level 2 (`map2.txt`) Moves | Behavior |
| :--- | :--- | :---: | :---: | :--- |
| **Greedy Least-Visited** | `python main.py` | **1,054** *(key at 456)* | **1,576** *(key at 698)* | Local exploration using tile visit counts (`Player_count`) |
| **A\* Search** | `python main.py --astar` | **140** *(63 to `K` + 77 to `E`)* | **154** *(59 to `K` + 95 to `E`)* | Optimal shortest path (`S` $\rightarrow$ `K` $\rightarrow$ `E`) via Manhattan heuristic |

---

### Command-Line Options

| Flag | Long Flag | Description |
| :---: | :--- | :--- |
| `-a` | `--astar` | Use the **A\*** pathfinding algorithm instead of the default least-visited greedy walk |
| `-p` | `--pathfinding {greedy,astar}` | Explicitly select the pathfinding algorithm (`greedy` or `astar`) |
| `-v` | `--version` | Print the program version (`pyMaze 1.1.0`) and exit |
| `-h` | `--help` | Show the help message and exit |

---

### Map Legend & 2D File Format

Each map file (`map.txt`, `map2.txt`) is a 25-row by 79-column 2D ASCII grid:

| Symbol | Meaning |
| :---: | :--- |
| `S` | Player start / current position |
| `K` | Level key (required to unlock the exit) |
| `E` | Level exit |
| Space (` `) or `@` | Walkable corridor tile |
| `-` / `\|` | Horizontal and vertical maze walls |
| `~` | Interior wall block fill |

Example snippet from `map.txt`:
```text
-------------------------------------------------------------------------------
S                   |~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
|----- -------------|~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
|~~~~| |~~~~~~~~~~~~~~~~|   |~~~~~~~~~~~~~~~~~~~~~~| |~~~~~~~~~~~~~~~~~~~~~~~~|
```

---

### How It Works

1. **Initialization (`App.init_data`)**: Loads the 2D ASCII map file into `MapObj` cells, automatically detecting the row stride (`Split_num`), player start (`PlayerIndex`), key (`KeyIndex`), and exit (`ExitIndex`).
2. **Rendering (`App.build_frame` & `App.draw`)**: Scales the maze rows horizontally and vertically to fit `Console.size`, appends the centered red telemetry lines, and updates the `rich.live.Live` display in a single atomic frame.
3. **Movement (`App.make_move`)**:
   - In **Greedy** mode (`default`), inspects the 4 cardinal neighbors (`right`, `left`, `up`, `down`) around `S` and selects the walkable neighbor with the lowest `Player_count`.
   - In **A\*** mode (`--astar`), runs `App.find_astar_direction` toward `KeyIndex` until the key is collected, and then toward `ExitIndex`.

---

### Installation & Usage

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Frankmau5/pyMaze.git
   cd pyMaze
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the program**:
   ```bash
   # Default greedy least-visited pathfinding
   python main.py

   # A* shortest-path pathfinding
   python main.py --astar
   ```
   Press `Ctrl+C` at any time to stop the simulation and restore the terminal.
