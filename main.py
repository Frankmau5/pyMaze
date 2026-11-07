import argparse
import heapq
import os
import time
from time import sleep
import sys
from rich.console import Console
from rich.live import Live
from rich.text import Text

__version__ = "1.1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------
# Helper: generate simple progressive maze maps (if they don't exist)
# ------------------------------------------------------------

def generate_maps(num_maps=10):
    """Create placeholder maze files map1.txt … mapN.txt.
    Each map is a 25‑row by 79‑col ASCII grid with increasing obstacle density.
    """
    import random
    random.seed(42)
    for i in range(1, num_maps + 1):
        fname = os.path.join(BASE_DIR, f"map{i}.txt")
        if os.path.exists(fname):
            continue
        rows = []
        for r in range(25):
            line = []
            for c in range(79):
                # borders are walls
                if r == 0 or r == 24 or c == 0 or c == 78:
                    line.append('-')
                else:
                    # obstacle density rises with level number
                    if random.random() < (i * 0.03):
                        line.append('~')
                    else:
                        line.append(' ')
            rows.append(''.join(line))
        # place start, key, exit
        rows[1] = 'S' + rows[1][1:]
        rows[12] = rows[12][:39] + 'K' + rows[12][40:]
        rows[23] = rows[23][:77] + 'E'
        with open(fname, 'w') as f:
            f.write('\n'.join(rows) + '\n')

# Ensure the ten maps exist (map1.txt is the original, map2.txt will be overwritten)
generate_maps(10)

class MapObj:
    def __init__(self, char_obj):
        self.Char = char_obj
        self.Player_count = 0

# ------------------------------------------------------------
# Core application
# ------------------------------------------------------------
class App:
    def __init__(self, pathfinding="greedy", fps=30):
        self.Pathfinding = pathfinding
        self.FPS = fps
        self.Split_num = 80  # will be updated after loading a map
        self.PlayerIndex = None
        self.KeyIndex = None
        self.ExitIndex = None
        self.MoveMade = 0
        self.Console = Console(color_system="truecolor")
        self.Colors = [(255, 214, 165), (253, 255, 182), (202, 255, 191), (160, 196, 255), (189, 178, 255)]
        self.PlayerKey = False
        self.RenderWidth = self.Split_num - 1
        self.LastValidMoves = []
        self.Live = None
        self.Data = []
        self.last_frame_time = time.time()

    # ------------------------------------------------------------------
    # Rendering utilities
    # ------------------------------------------------------------------
    def get_render_width(self):
        base_width = self.Split_num - 1
        return max(base_width, self.Console.size.width)

    def scale_row(self, row_chars, target_w):
        n = len(row_chars)
        if target_w <= n:
            return "".join(" " if c == "@" else c for c in row_chars)
        out = []
        for i, c in enumerate(row_chars):
            w = (i + 1) * target_w // n - i * target_w // n
            ch = " " if c == "@" else c
            if ch in ("-", "~", " "):
                out.append(ch * w)
            elif ch == "|":
                prev = " " if (i == 0 or row_chars[i - 1] == "@") else row_chars[i - 1]
                nxt = " " if (i + 1 >= n or row_chars[i + 1] == "@") else row_chars[i + 1]
                if i == n - 1 or (prev in ("-", "~") and nxt not in ("-", "~")):
                    out.append(prev * (w - 1) + "|")
                elif nxt in ("-", "~"):
                    out.append("|" + nxt * (w - 1))
                else:
                    out.append("|" + " " * (w - 1))
            else:
                if i == n - 1:
                    out.append(" " * (w - 1) + ch)
                else:
                    out.append(ch + " " * (w - 1))
        return "".join(out)

    def format_status_line(self, text, width=None):
        if width is None:
            width = self.get_render_width()
        if len(text) >= width:
            return text[:width]
        return text.center(width, " ")

    # ------------------------------------------------------------------
    # Map loading – supports both legacy 1‑char‑per‑line and new 2‑D format
    # ------------------------------------------------------------------
    def init_data(self, file='map1.txt'):
        t = []
        filepath = file if os.path.isabs(file) else os.path.join(BASE_DIR, file)
        with open(filepath) as f_open:
            raw_lines = [line.rstrip('\r\n') for line in f_open.readlines() if line.rstrip('\r\n') != ""]
        # Detect 2D grid (any line longer than 1 char)
        if any(len(line) > 1 for line in raw_lines):
            row_width = max(len(line) for line in raw_lines)
            self.Split_num = row_width + 1
            for line in raw_lines:
                padded = line.ljust(row_width)
                for ch in padded:
                    cell_char = '@' if ch == ' ' else ch
                    t.append(MapObj(cell_char))
                t.append(MapObj('L'))
        else:
            # legacy format – keep existing Split_num (80)
            for line in raw_lines:
                t.append(MapObj(line))
        # locate special tiles
        for idx, item in enumerate(t):
            if item.Char == 'S':
                self.PlayerIndex = idx
            elif item.Char == 'K':
                self.KeyIndex = idx
            elif item.Char == 'E':
                self.ExitIndex = idx
        return t

    # ------------------------------------------------------------------
    # Core game loop helpers
    # ------------------------------------------------------------------
    def get_valid_moves(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return []
        data_ = []
        data_len = len(self.Data)
        valid = ('@', 'E', 'K')
        if player_index + 1 < data_len and self.Data[player_index + 1].Char in valid:
            data_.append(('right', self.Data[player_index + 1].Player_count))
        if player_index - 1 >= 0 and self.Data[player_index - 1].Char in valid:
            data_.append(('left', self.Data[player_index - 1].Player_count))
        if player_index - self.Split_num >= 0 and self.Data[player_index - self.Split_num].Char in valid:
            data_.append(('up', self.Data[player_index - self.Split_num].Player_count))
        if player_index + self.Split_num < data_len and self.Data[player_index + self.Split_num].Char in valid:
            data_.append(('down', self.Data[player_index + self.Split_num].Player_count))
        return data_

    def get_status_lines(self, valid_moves=None, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if valid_moves is None:
            valid_moves = self.get_valid_moves(player_index)
        width = self.RenderWidth
        fps_display = f"FPS: {self.FPS:.1f}" if isinstance(self.FPS, float) else f"FPS: {self.FPS}"
        return [
            self.format_status_line(f"Valid moves{valid_moves}", width),
            self.format_status_line(f"Player index: {player_index}", width),
            self.format_status_line(f"Moves {self.MoveMade}", width),
            self.format_status_line(f"Player has key {self.PlayerKey} | {fps_display}", width),
        ]

    def build_frame(self):
        # split raw data into rows (ignoring L markers)
        rows = []
        cur = []
        for item in self.Data:
            if item.Char == 'L':
                rows.append(cur)
                cur = []
            else:
                cur.append(item.Char)
        if cur:
            rows.append(cur)
        target_w = self.get_render_width()
        self.RenderWidth = target_w
        target_h = max(len(rows), self.Console.size.height - 5)
        extra_h = max(0, target_h - len(rows))
        # rows without horizontal walls are stretchable vertically
        stretchable = [idx for idx, r in enumerate(rows) if '-' not in r]
        extra_counts = {idx: 0 for idx in range(len(rows))}
        if stretchable and extra_h > 0:
            m = len(stretchable)
            for i, row_idx in enumerate(stretchable):
                extra_counts[row_idx] = (i + 1) * extra_h // m - i * extra_h // m
        frame = Text()
        color_idx = 0
        for idx, row_chars in enumerate(rows):
            if color_idx > 4:
                color_idx = 0
            r, g, b = self.Colors[color_idx]
            s = f"rgb({r},{g},{b})"
            line = self.scale_row(row_chars, target_w)
            frame.append(line + "\n", style=s)
            for _ in range(extra_counts[idx]):
                filler = [' ' if c in ('S', 'K', 'E') else c for c in row_chars]
                filler_line = self.scale_row(filler, target_w)
                frame.append(filler_line + "\n", style=s)
            color_idx += 1
        # status lines at bottom
        for line in self.get_status_lines():
            frame.append_text(self.Console.render_str(line, style="bold red"))
            frame.append("\n")
        return frame

    def draw(self):
        frame = self.build_frame()
        if self.Live:
            self.Live.update(frame, refresh=True)
        else:
            self.Console.print(frame, end="", overflow="crop", no_wrap=True)
        # enforce FPS
        now = time.time()
        elapsed = now - self.last_frame_time
        target = 1.0 / self.FPS if self.FPS > 0 else 0
        if elapsed < target:
            sleep(target - elapsed)
        self.last_frame_time = time.time()

    def clear(self):
        if self.Live is None:
            sys.stdout.write('\033[H')
            sys.stdout.flush()

    def find_player(self):
        if self.PlayerIndex is not None and 0 <= self.PlayerIndex < len(self.Data) and self.Data[self.PlayerIndex].Char == 'S':
            return self.PlayerIndex
        for i, it in enumerate(self.Data):
            if it.Char == 'S':
                self.PlayerIndex = i
                return i
        return None

    # ------------------------------------------------------------------
    # Movement helpers (preserve exit tile when stepping off before key)
    # ------------------------------------------------------------------
    def player_move_right(self, index):
        target = index + 1
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = 'E' if index == self.ExitIndex else '@'
            self.Data[target].Player_count += 1
            self.Data[target].Char = 'S'
            self.PlayerIndex = target

    def player_move_left(self, index):
        target = index - 1
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = 'E' if index == self.ExitIndex else '@'
            self.Data[target].Player_count += 1
            self.Data[target].Char = 'S'
            self.PlayerIndex = target

    def player_move_up(self, index):
        target = index - self.Split_num
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = 'E' if index == self.ExitIndex else '@'
            self.Data[target].Player_count += 1
            self.Data[target].Char = 'S'
            self.PlayerIndex = target

    def player_move_down(self, index):
        target = index + self.Split_num
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = 'E' if index == self.ExitIndex else '@'
            self.Data[target].Player_count += 1
            self.Data[target].Char = 'S'
            self.PlayerIndex = target

    # ------------------------------------------------------------------
    # A* helper for shortest‑path mode
    # ------------------------------------------------------------------
    def find_astar_direction(self, start_index, goal_index):
        if start_index == goal_index or goal_index is None:
            return None
        split = self.Split_num
        data_len = len(self.Data)
        valid = ('@', 'E', 'K', 'S')
        goal_r, goal_c = divmod(goal_index, split)
        def h(idx):
            r, c = divmod(idx, split)
            return abs(r - goal_r) + abs(c - goal_c)
        heap = [(h(start_index), 0, 0, start_index, None)]
        best = {start_index: 0}
        directions = [('right', 1), ('left', -1), ('up', -split), ('down', split)]
        ctr = 0
        while heap:
            _, g, _, cur, first = heapq.heappop(heap)
            if cur == goal_index:
                return first
            for dir_name, delta in directions:
                nxt = cur + delta
                if 0 <= nxt < data_len and self.Data[nxt].Char in valid:
                    ng = g + 1
                    if ng < best.get(nxt, 1e9):
                        best[nxt] = ng
                        ctr += 1
                        heapq.heappush(heap, (ng + h(nxt), ng, ctr, nxt, dir_name if first is None else first))
        return None

    # ------------------------------------------------------------------
    # Main move logic – chooses algorithm based on self.Pathfinding
    # ------------------------------------------------------------------
    def make_move(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return 1
        if player_index == self.ExitIndex and self.PlayerKey:
            return 1
        valid_moves = self.get_valid_moves(player_index)
        if not valid_moves:
            return 1
        self.LastValidMoves = valid_moves
        chosen = None
        if self.Pathfinding == "astar":
            goal = self.ExitIndex if self.PlayerKey else self.KeyIndex
            chosen = self.find_astar_direction(player_index, goal)
        if chosen is None:
            smallest = min(p for _, p in valid_moves)
            for w, p in valid_moves:
                if p == smallest:
                    chosen = w
                    break
        if chosen == "right":
            self.player_move_right(player_index)
        elif chosen == "left":
            self.player_move_left(player_index)
        elif chosen == "up":
            self.player_move_up(player_index)
        elif chosen == "down":
            self.player_move_down(player_index)
        self.MoveMade += 1
        return 0

# ------------------------------------------------------------------
# CLI parsing
# ------------------------------------------------------------------
def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="pyMaze – terminal maze explorer with optional A* pathfinding.")
    parser.add_argument("-v", "--version", action="version", version=f"pyMaze {__version__}")
    parser.add_argument("-a", "--astar", action="store_true", help="Use A* pathfinding (overrides --pathfinding).")
    parser.add_argument("-p", "--pathfinding", choices=["greedy", "astar"], default="greedy", help="Select pathfinding algorithm.")
    parser.add_argument("-l", "--loop", action="store_true", help="Loop through all maps (1‑10) continuously.")
    parser.add_argument("-f", "--fps", type=float, default=30.0, help="Target frames‑per‑second for rendering.")
    return parser.parse_args(argv)

# ------------------------------------------------------------------
# Game orchestration
# ------------------------------------------------------------------
def main(argv=None):
    args = parse_args(argv)
    mode = "astar" if args.astar else args.pathfinding
    fps = max(1.0, args.fps)
    app = App(pathfinding=mode, fps=fps)
    try:
        with Live(console=app.Console, refresh_per_second=60, screen=True) as live:
            app.Live = live
            level = 1
            while True:
                map_file = f"map{level}.txt"
                app.Data = app.init_data(map_file)
                # reset per‑level state
                app.MoveMade = 0
                app.PlayerKey = False
                app.PlayerIndex = None
                app.KeyIndex = None
                app.ExitIndex = None
                # re‑scan for indices after loading
                for idx, it in enumerate(app.Data):
                    if it.Char == "S":
                        app.PlayerIndex = idx
                    elif it.Char == "K":
                        app.KeyIndex = idx
                    elif it.Char == "E":
                        app.ExitIndex = idx
                # play level
                gate = True
                while gate:
                    app.draw()
                    if app.update_player():
                        gate = False
                    app.clear()
                # finished level – brief pause
                sleep(1)
                if level == 10:
                    # final animation & prompt
                    final_animation(app)
                    break
                level += 1
                if args.loop and level > 10:
                    level = 1
    except KeyboardInterrupt:
        pass
    finally:
        app.Live = None
        app.Console.clear()

# ------------------------------------------------------------------
# End‑game animation & restart prompt
# ------------------------------------------------------------------
def final_animation(app):
    from itertools import cycle
    frames = cycle(["|", "/", "-", "\\"])
    start = time.time()
    while time.time() - start < 3:
        app.Console.print(f"\n\n   Congratulations! Completed all 10 levels!   {next(frames)}", style="bold magenta", justify="center")
        sleep(0.2)
        app.Console.clear()
    app.Console.print("\n\n   Press [R] to restart or any other key to exit...   ", style="bold green", justify="center")
    try:
        import termios, tty, sys as _sys
        fd = _sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        tty.setraw(fd)
        ch = _sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch.lower() == 'r':
        main()

if __name__ == "__main__":
    main()
