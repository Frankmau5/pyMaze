import argparse
import heapq
import os
from time import sleep
import sys
from rich.console import Console
from rich.live import Live
from rich.text import Text

__version__ = "1.1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class MapObj:
    def __init__(self, char_obj):
        self.Char = char_obj
        self.Player_count = 0


# TODO: make sandalone exe file that is only one file
# ANSI escape sequences on terminals that support them
class App:
    def __init__(self, pathfinding="greedy"):
        self.Pathfinding = pathfinding
        self.Split_num = 80
        self.PlayerIndex = None
        self.KeyIndex = None
        self.ExitIndex = 1918
        self.MoveMade = 0
        self.Console = Console(color_system="truecolor")
        self.Colors = [(255, 214, 165), (253, 255, 182), (202, 255, 191), (160, 196, 255), (189, 178, 255)]
        self.PlayerKey = False
        self.RenderWidth = self.Split_num - 1
        self.LastValidMoves = []
        self.Live = None
        self.Data = self.init_data()

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

    def init_data(self, file='map.txt'):
        t = list()
        filepath = file if os.path.isabs(file) else os.path.join(BASE_DIR, file)
        with open(filepath) as f_open:
            raw_lines = [line.rstrip("\r\n") for line in f_open.readlines() if line.rstrip("\r\n") != ""]

        # Support both 2D grid files (one row per line) and legacy 1-char-per-line files
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
            for line in raw_lines:
                t.append(MapObj(line))

        for idx, item in enumerate(t):
            if item.Char == 'S':
                self.PlayerIndex = idx
            elif item.Char == 'K':
                self.KeyIndex = idx
            elif item.Char == 'E':
                self.ExitIndex = idx

        return t

    def get_valid_moves(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return []
        data_ = list()
        data_len = len(self.Data)
        valid_chars = ('@', 'E', 'K')
        if player_index + 1 < data_len and self.Data[player_index + 1].Char in valid_chars:
            data_.append(('right', self.Data[player_index + 1].Player_count))
        if player_index - 1 >= 0 and self.Data[player_index - 1].Char in valid_chars:
            data_.append(('left', self.Data[player_index - 1].Player_count))
        if player_index - self.Split_num >= 0 and self.Data[player_index - self.Split_num].Char in valid_chars:
            data_.append(('up', self.Data[player_index - self.Split_num].Player_count))
        if player_index + self.Split_num < data_len and self.Data[player_index + self.Split_num].Char in valid_chars:
            data_.append(('down', self.Data[player_index + self.Split_num].Player_count))
        return data_

    def get_status_lines(self, valid_moves=None, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if valid_moves is None:
            valid_moves = self.get_valid_moves(player_index)
        width = self.RenderWidth
        return [
            self.format_status_line(f"Valid moves{valid_moves}", width),
            self.format_status_line(f"Player index: {player_index}", width),
            self.format_status_line(f"Moves {self.MoveMade}", width),
            self.format_status_line(f"Player has key {self.PlayerKey}", width),
        ]

    def build_frame(self):
        rows = []
        current_row = []
        for item in self.Data:
            if item.Char == 'L':
                rows.append(current_row)
                current_row = []
            else:
                current_row.append(item.Char)
        if current_row:
            rows.append(current_row)

        target_w = self.get_render_width()
        self.RenderWidth = target_w
        target_h = max(len(rows), self.Console.size.height - 5)
        extra_h = max(0, target_h - len(rows))

        stretchable = [idx for idx, r in enumerate(rows) if '-' not in r]
        extra_counts = {idx: 0 for idx in range(len(rows))}
        if stretchable and extra_h > 0:
            m = len(stretchable)
            for i, row_idx in enumerate(stretchable):
                extra_counts[row_idx] = (i + 1) * extra_h // m - i * extra_h // m

        frame = Text()
        color_count = 0
        for idx, row_chars in enumerate(rows):
            if color_count > 4:
                color_count = 0
            r, g, b = self.Colors[color_count]
            s = f"rgb({r},{g},{b})"

            line = self.scale_row(row_chars, target_w)
            frame.append(line + "\n", style=s)

            for _ in range(extra_counts[idx]):
                filler_chars = [' ' if c in ('S', 'K', 'E') else c for c in row_chars]
                filler_line = self.scale_row(filler_chars, target_w)
                frame.append(filler_line + "\n", style=s)

            color_count = color_count + 1

        if self.Live is not None:
            status_lines = self.get_status_lines()
            for idx, s_line in enumerate(status_lines):
                rendered = self.Console.render_str(s_line, style="bold red")
                frame.append_text(rendered)
                if idx < len(status_lines) - 1:
                    frame.append("\n")

        return frame

    def draw(self):
        frame = self.build_frame()
        if self.Live is not None:
            self.Live.update(frame, refresh=True)
        else:
            self.Console.print(frame, end='', overflow="crop", no_wrap=True)
        sleep(0.01)

    def clear(self):
        if self.Live is None:
            sys.stdout.write('\033[H')
            sys.stdout.flush()

    def find_player(self):
        if (
            self.PlayerIndex is not None
            and 0 <= self.PlayerIndex < len(self.Data)
            and self.Data[self.PlayerIndex].Char == 'S'
        ):
            return self.PlayerIndex
        for count, item in enumerate(self.Data):
            if item.Char == 'S':
                self.PlayerIndex = count
                return count
        return None

    def update_player(self):
        player_index = self.find_player()
        a = self.make_move(player_index)

        if a == 1:
            return True
        return False

    def player_move_right(self, index):
        target = index + 1
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[target]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'
            self.PlayerIndex = target

    def player_move_left(self, index):
        target = index - 1
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[target]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1
            self.PlayerIndex = target

    def player_move_up(self, index):
        target = index - self.Split_num
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[target]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'
            self.PlayerIndex = target

    def player_move_down(self, index):
        target = index + self.Split_num
        if self.Data[target].Char != 'L':
            if self.Data[target].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[target]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1
            self.PlayerIndex = target

    def find_astar_direction(self, start_index, goal_index):
        if start_index == goal_index or goal_index is None:
            return None

        split_num = self.Split_num
        data_len = len(self.Data)
        valid_chars = ('@', 'E', 'K', 'S')
        goal_r, goal_c = divmod(goal_index, split_num)

        def heuristic(idx):
            r, c = divmod(idx, split_num)
            return abs(r - goal_r) + abs(c - goal_c)

        counter = 0
        open_heap = [(heuristic(start_index), 0, counter, start_index, None)]
        best_g = {start_index: 0}
        neighbors = [
            ('right', 1),
            ('left', -1),
            ('up', -split_num),
            ('down', split_num),
        ]

        while open_heap:
            _, g_cost, _, current, first_dir = heapq.heappop(open_heap)
            if current == goal_index:
                return first_dir

            for direction, delta in neighbors:
                nxt = current + delta
                if 0 <= nxt < data_len and self.Data[nxt].Char in valid_chars:
                    new_g = g_cost + 1
                    if new_g < best_g.get(nxt, float('inf')):
                        best_g[nxt] = new_g
                        counter += 1
                        step_dir = direction if first_dir is None else first_dir
                        heapq.heappush(
                            open_heap,
                            (new_g + heuristic(nxt), new_g, counter, nxt, step_dir),
                        )
        return None

    def make_move(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return 1

        if player_index == self.ExitIndex and self.PlayerKey == True:
            return 1

        # find all the valid moves
        data_ = self.get_valid_moves(player_index)

        if not data_:
            return 1

        self.LastValidMoves = data_
        if self.Live is None:
            for s_line in self.get_status_lines(data_, player_index):
                self.Console.print(s_line, style="bold red", overflow="crop", no_wrap=True)

        chosen_dir = None
        if self.Pathfinding == "astar":
            goal = self.ExitIndex if self.PlayerKey or self.KeyIndex is None else self.KeyIndex
            chosen_dir = self.find_astar_direction(player_index, goal)

        if chosen_dir is None:
            smallest = [p for _, p in data_]
            smallest.sort()
            small = smallest[0]
            for w, p in data_:
                if p == small:
                    chosen_dir = w
                    break

        if chosen_dir == "right":
            self.player_move_right(player_index)
        elif chosen_dir == "left":
            self.player_move_left(player_index)
        elif chosen_dir == "up":
            self.player_move_up(player_index)
        elif chosen_dir == "down":
            self.player_move_down(player_index)

        self.MoveMade = self.MoveMade + 1
        return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="pyMaze - A terminal maze app where the player finds their way out.")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"pyMaze {__version__}",
    )
    parser.add_argument(
        "-a",
        "--astar",
        action="store_true",
        help="Use the A* pathfinding algorithm instead of the default least-visited greedy walk.",
    )
    parser.add_argument(
        "-p",
        "--pathfinding",
        choices=["greedy", "astar"],
        default="greedy",
        help="Select pathfinding algorithm: 'greedy' (default) or 'astar'.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    mode = "astar" if args.astar else args.pathfinding
    app = App(pathfinding=mode)
    try:
        with Live(console=app.Console, refresh_per_second=60, screen=True) as live:
            app.Live = live
            map_one(app)
            sleep(10)
            map_two(app)
            sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        app.Live = None
        app.Console.clear()


def map_one(app):
    gate = True
    while gate:
        app.draw()
        a = app.update_player()
        if a:
            gate = False

        app.clear()


def map_two(app):
    # level 2
    gate = True
    app.Data = app.init_data("map2.txt")
    app.MoveMade = 0
    app.PlayerKey = False
    while gate:
        app.draw()
        a = app.update_player()
        if a:
            gate = False
        app.clear()


if __name__ == "__main__":
    main()
