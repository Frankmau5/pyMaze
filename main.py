import argparse
import heapq
import os
import sys
import time
from time import sleep
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

__version__ = "1.1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOTAL_LEVELS = 10


class MapObj:
    def __init__(self, char_obj):
        self.Char = char_obj
        self.Player_count = 0


# TODO: make sandalone exe file that is only one file
# ANSI escape sequences on terminals that support them
class App:
    def __init__(self, pathfinding="greedy", fps=30.0):
        self.Pathfinding = pathfinding
        self.FPS = float(fps)
        self.CurrentFPS = float(fps)
        self.Level = 1
        self.Split_num = 80
        self.PlayerIndex = None
        self.KeyIndex = None
        self.ExitIndex = 1918
        self.MoveMade = 0
        self.Console = Console(color_system="truecolor")
        self.Colors = [
            (255, 214, 165),
            (253, 255, 182),
            (202, 255, 191),
            (160, 196, 255),
            (189, 178, 255),
        ]
        self.PlayerKey = False
        self.RenderWidth = self.Split_num - 1
        self.LastValidMoves = []
        self.Live = None
        self.last_frame_time = time.perf_counter()
        self.Data = self.init_data("map1.txt")

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

    def init_data(self, file="map1.txt"):
        t = []
        filepath = file if os.path.isabs(file) else os.path.join(BASE_DIR, file)
        if not os.path.exists(filepath) and file == "map1.txt":
            filepath = os.path.join(BASE_DIR, "map.txt")
        with open(filepath) as f_open:
            raw_lines = [line.rstrip("\r\n") for line in f_open.readlines() if line.rstrip("\r\n") != ""]

        self.PlayerIndex = None
        self.KeyIndex = None
        self.ExitIndex = None

        # Support both 2D grid files (one row per line) and legacy 1-char-per-line files
        if any(len(line) > 1 for line in raw_lines):
            row_width = max(len(line) for line in raw_lines)
            self.Split_num = row_width + 1
            for line in raw_lines:
                padded = line.ljust(row_width)
                for ch in padded:
                    cell_char = "@" if ch == " " else ch
                    t.append(MapObj(cell_char))
                t.append(MapObj("L"))
        else:
            for line in raw_lines:
                t.append(MapObj(line))

        for idx, item in enumerate(t):
            if item.Char == "S":
                self.PlayerIndex = idx
            elif item.Char == "K":
                self.KeyIndex = idx
            elif item.Char == "E":
                self.ExitIndex = idx

        return t

    def get_valid_moves(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return []
        data_ = []
        data_len = len(self.Data)
        valid = ("@", "E", "K")
        if player_index + 1 < data_len and self.Data[player_index + 1].Char in valid:
            data_.append(("right", self.Data[player_index + 1].Player_count))
        if player_index - 1 >= 0 and self.Data[player_index - 1].Char in valid:
            data_.append(("left", self.Data[player_index - 1].Player_count))
        if player_index - self.Split_num >= 0 and self.Data[player_index - self.Split_num].Char in valid:
            data_.append(("up", self.Data[player_index - self.Split_num].Player_count))
        if player_index + self.Split_num < data_len and self.Data[player_index + self.Split_num].Char in valid:
            data_.append(("down", self.Data[player_index + self.Split_num].Player_count))
        return data_

    def get_status_lines(self, valid_moves=None, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if valid_moves is None:
            valid_moves = self.get_valid_moves(player_index)
        width = self.RenderWidth
        fps_display = f"FPS: {self.CurrentFPS:.1f}"
        return [
            self.format_status_line(f"Valid moves{valid_moves}", width),
            self.format_status_line(f"Level {self.Level}/{TOTAL_LEVELS} | Player index: {player_index}", width),
            self.format_status_line(f"Moves {self.MoveMade} | {fps_display}", width),
            self.format_status_line(f"Player has key {self.PlayerKey}", width),
        ]

    def build_frame(self):
        rows = []
        cur = []
        for item in self.Data:
            if item.Char == "L":
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

        stretchable = [idx for idx, r in enumerate(rows) if "-" not in r]
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
                filler = [" " if c in ("S", "K", "E") else c for c in row_chars]
                filler_line = self.scale_row(filler, target_w)
                frame.append(filler_line + "\n", style=s)
            color_idx += 1

        if self.Live is not None:
            status_lines = self.get_status_lines()
            for idx, line in enumerate(status_lines):
                frame.append_text(self.Console.render_str(line, style="bold red"))
                if idx < len(status_lines) - 1:
                    frame.append("\n")
        return frame

    def draw(self):
        frame = self.build_frame()
        if self.Live is not None:
            self.Live.update(frame, refresh=True)
        else:
            self.Console.print(frame, end="", overflow="crop", no_wrap=True)

        target_dt = (1.0 / self.FPS) if self.FPS > 0 else 0.0
        now = time.perf_counter()
        elapsed = now - self.last_frame_time
        if elapsed < target_dt:
            sleep(target_dt - elapsed)
        end_time = time.perf_counter()
        frame_dt = max(1e-6, end_time - self.last_frame_time)
        instant_fps = 1.0 / frame_dt
        self.CurrentFPS = 0.7 * self.CurrentFPS + 0.3 * instant_fps
        self.last_frame_time = end_time

    def clear(self):
        if self.Live is None:
            sys.stdout.write("\033[H")
            sys.stdout.flush()

    def find_player(self):
        if (
            self.PlayerIndex is not None
            and 0 <= self.PlayerIndex < len(self.Data)
            and self.Data[self.PlayerIndex].Char == "S"
        ):
            return self.PlayerIndex
        for i, it in enumerate(self.Data):
            if it.Char == "S":
                self.PlayerIndex = i
                return i
        return None

    def update_player(self):
        player_index = self.find_player()
        a = self.make_move(player_index)
        if a == 1:
            return True
        return False

    def player_move_right(self, index):
        target = index + 1
        if self.Data[target].Char != "L":
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = "E" if index == self.ExitIndex else "@"
            self.Data[target].Player_count += 1
            self.Data[target].Char = "S"
            self.PlayerIndex = target

    def player_move_left(self, index):
        target = index - 1
        if self.Data[target].Char != "L":
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = "E" if index == self.ExitIndex else "@"
            self.Data[target].Player_count += 1
            self.Data[target].Char = "S"
            self.PlayerIndex = target

    def player_move_up(self, index):
        target = index - self.Split_num
        if self.Data[target].Char != "L":
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = "E" if index == self.ExitIndex else "@"
            self.Data[target].Player_count += 1
            self.Data[target].Char = "S"
            self.PlayerIndex = target

    def player_move_down(self, index):
        target = index + self.Split_num
        if self.Data[target].Char != "L":
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            self.Data[index].Char = "E" if index == self.ExitIndex else "@"
            self.Data[target].Player_count += 1
            self.Data[target].Char = "S"
            self.PlayerIndex = target

    def find_astar_direction(self, start_index, goal_index):
        if start_index == goal_index or goal_index is None:
            return None
        split = self.Split_num
        data_len = len(self.Data)
        valid = ("@", "E", "K", "S")
        goal_r, goal_c = divmod(goal_index, split)

        def h(idx):
            r, c = divmod(idx, split)
            return abs(r - goal_r) + abs(c - goal_c)

        heap = [(h(start_index), 0, 0, start_index, None)]
        best = {start_index: 0}
        directions = [("right", 1), ("left", -1), ("up", -split), ("down", split)]
        ctr = 0
        while heap:
            _, g, _, cur, first = heapq.heappop(heap)
            if cur == goal_index:
                return first
            for dir_name, delta in directions:
                nxt = cur + delta
                if 0 <= nxt < data_len and self.Data[nxt].Char in valid:
                    ng = g + 1
                    if ng < best.get(nxt, float("inf")):
                        best[nxt] = ng
                        ctr += 1
                        heapq.heappush(
                            heap,
                            (ng + h(nxt), ng, ctr, nxt, dir_name if first is None else first),
                        )
        return None

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

        if self.Live is None:
            for s_line in self.get_status_lines(valid_moves, player_index):
                self.Console.print(s_line, style="bold red", overflow="crop", no_wrap=True)

        chosen = None
        if self.Pathfinding == "astar":
            goal = self.ExitIndex if (self.PlayerKey or self.KeyIndex is None) else self.KeyIndex
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


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="pyMaze - terminal maze explorer with optional A* pathfinding.")
    parser.add_argument("-v", "--version", action="version", version=f"pyMaze {__version__}")
    parser.add_argument(
        "-a",
        "--astar",
        action="store_true",
        help="Use A* pathfinding instead of the default least-visited greedy walk.",
    )
    parser.add_argument(
        "-p",
        "--pathfinding",
        choices=["greedy", "astar"],
        default="greedy",
        help="Select pathfinding algorithm: 'greedy' (default) or 'astar'.",
    )
    parser.add_argument(
        "-l",
        "--loop",
        action="store_true",
        help="Continuously loop through all 10 levels.",
    )
    parser.add_argument(
        "-f",
        "--fps",
        type=float,
        default=30.0,
        help="Target frames-per-second for rendering (default: 30).",
    )
    return parser.parse_args(argv)


def play_level(app, level):
    app.Level = level
    app.Data = app.init_data(f"map{level}.txt")
    app.MoveMade = 0
    app.PlayerKey = False
    app.last_frame_time = time.perf_counter()
    gate = True
    while gate:
        app.draw()
        if app.update_player():
            gate = False
        app.clear()
    app.draw()


def map_one(app):
    play_level(app, 1)


def map_two(app):
    play_level(app, 2)


def read_key_nonblocking(timeout=0.15):
    if not sys.stdin.isatty():
        sleep(timeout)
        return None
    try:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            rlist, _, _ = select.select([sys.stdin], [], [], timeout)
            if not rlist:
                return None
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                rlist2, _, _ = select.select([sys.stdin], [], [], 0.02)
                if rlist2:
                    ch += sys.stdin.read(2)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    except Exception:
        sleep(timeout)
        return None


def final_animation(app):
    """Display an animated victory screen at the end of Level 10 with interactive Restart / Exit buttons."""
    banner_frames = [
        "★  ✦  ★  CONGRATULATIONS! ALL 10 LEVELS COMPLETED!  ★  ✦  ★",
        "✦  ★  ✦  CONGRATULATIONS! ALL 10 LEVELS COMPLETED!  ✦  ★  ✦",
    ]
    trophy_art = [
        "       ___________       ",
        "      '._==_==_=_.'      ",
        "      .-\\:      /-.      ",
        "     | (|:.     |) |     ",
        "      '-|:.     |-'      ",
        "        \\::.    /        ",
        "         '::. .'         ",
        "           ) (           ",
        "         _.' '._         ",
        "        `\"\"\"\"\"\"\"`        ",
    ]
    palette = [
        "rgb(255,214,165)",
        "rgb(253,255,182)",
        "rgb(202,255,191)",
        "rgb(160,196,255)",
        "rgb(189,178,255)",
    ]

    selected = 0  # 0 = Start Again, 1 = Exit
    tick = 0

    if not sys.stdin.isatty():
        return False

    while True:
        color = palette[tick % len(palette)]
        header = banner_frames[tick % len(banner_frames)]

        content = Text(justify="center")
        content.append("\n" + header + "\n\n", style=f"bold {color}")
        for line in trophy_art:
            content.append(line + "\n", style="bold yellow")
        content.append(
            f"\nAlgorithm: {app.Pathfinding.upper()}   |   Target FPS: {app.FPS:g}\n\n",
            style="bold cyan",
        )

        btn_restart_style = "bold black on rgb(202,255,191)" if selected == 0 else "bold rgb(202,255,191)"
        btn_exit_style = "bold black on rgb(255,160,160)" if selected == 1 else "bold rgb(255,160,160)"

        content.append("   [ Start Again (R) ]   ", style=btn_restart_style)
        content.append("     ")
        content.append("   [ Exit Program (Q) ]   \n\n", style=btn_exit_style)
        content.append(
            "Use ← / → or Tab to select a button and press Enter (or press R / Q)",
            style="dim white",
        )

        panel = Panel(
            Align.center(content, vertical="middle"),
            border_style=color,
            title="[bold yellow]pyMaze Victory[/bold yellow]",
            subtitle=f"[bold white]v{__version__}[/bold white]",
            height=max(22, app.Console.size.height - 2),
        )

        if app.Live is not None:
            app.Live.update(panel, refresh=True)
        else:
            app.Console.clear()
            app.Console.print(panel)

        key = read_key_nonblocking(timeout=0.15)
        tick += 1
        if key is None:
            continue
        if key in ("\x03", "q", "Q", "\x1b"):
            return False
        if key in ("r", "R"):
            return True
        if key in ("\x1b[D", "\x1b[C", "\t", "h", "l", "a", "d"):
            selected = 1 - selected
        elif key in ("\r", "\n", " "):
            return selected == 0


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
                play_level(app, level)
                sleep(0.6)
                if level == TOTAL_LEVELS:
                    if args.loop:
                        level = 1
                        continue
                    restart = final_animation(app)
                    if restart:
                        level = 1
                        continue
                    break
                level += 1
    except KeyboardInterrupt:
        pass
    finally:
        app.Live = None
        app.Console.clear()


if __name__ == "__main__":
    main()
