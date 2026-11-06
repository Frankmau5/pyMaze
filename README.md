# pyMaze

**Version:** `1.0.1`

### Description

**pyMaze** is an automated terminal-based maze solver rendered in truecolor using the [Rich](https://github.com/Textualize/rich) library. The player (`S`) autonomously explores multi-level ASCII mazes, locates the key (`K`), and navigates to the exit (`E`) while displaying live telemetry centered at the bottom of the terminal.

![pyMaze Screenshot](Image.PNG)

---

### Features

- **Autonomous Exploration**: Uses a least-visited neighbor heuristic (`Player_count`) to explore corridors, backtrack out of dead ends, collect the level key, and reach the exit.
- **Full-Terminal Responsive Scaling**: Automatically scales the maze horizontally and vertically to fill the active terminal dimensions while preserving wall alignment and centering the status lines across the exact map width.
- **Truecolor Rendering**: Cycles through a 5-color pastel RGB palette row-by-row with live status lines showing valid moves, current player index, total moves made, and key status.
- **Multi-Level Progression**: Automatically transitions from Level 1 (`map.txt`) to Level 2 (`map2.txt`) upon completion.
- **CLI Support**: Includes `-v` / `--version` (`pyMaze 1.0.1`) and `-h` / `--help` command-line switches.

---

### Map Legend & File Format

Each map file (`map.txt`, `map2.txt`) encodes an 80-column by 25-row grid (2,000 lines total, 1 cell per line):

| Symbol | Meaning | Rendered As |
| :---: | :--- | :--- |
| `S` | Player current position | `S` |
| `K` | Level key (required to unlock the exit) | `K` |
| `E` | Level exit | `E` |
| `@` | Walkable corridor tile | Space (` `) |
| `-` / `\|` | Horizontal and vertical maze walls | `-` / `\|` |
| `~` | Interior wall block fill | `~` |
| `L` | End-of-row marker | Newline (`\n`) |

---

### How It Works

1. **Initialization (`App.init_data`)**: Loads the map file into a list of `MapObj` instances, each storing its tile character (`Char`) and visit counter (`Player_count`).
2. **Rendering (`App.draw`)**: Splits the map at `L` markers into rows, scales the rows horizontally and vertically to fit the terminal window (`Console.size`), and prints each row in pastel RGB colors.
3. **Movement (`App.make_move`)**:
   - Inspects the 4 cardinal neighbors (`right`, `left`, `up`, `down`) around `S`.
   - Filters for walkable tiles (`@`, `K`, `E`) and selects the neighbor with the lowest `Player_count`.
   - When stepping onto `K`, sets `PlayerKey = True`.
   - Preserves the exit tile (`E`) if visited before picking up the key, and completes the level once `S` reaches `ExitIndex` with `PlayerKey == True`.

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
   python main.py
   ```
   Press `Ctrl+C` at any time to stop the simulation and clear the terminal.

4. **Command-line options**:
   ```bash
   python main.py --version   # or -v (prints: pyMaze 1.0.1)
   python main.py --help      # or -h
   ```
