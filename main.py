import argparse
import os
from time import sleep
import sys
from rich.console import Console

__version__ = "1.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class MapObj:
    def __init__(self, char_obj):
        self.Char = char_obj
        self.Player_count = 0


# TODO: make sandalone exe file that is only one file
# ANSI escape sequences on terminals that support them
class App:
    def __init__(self):
        self.Split_num = 80
        self.Data = self.init_data()
        self.ExitIndex = 1918
        self.MoveMade = 0
        self.Console = Console(color_system="truecolor")
        self.Colors = [(255, 214, 165), (253, 255, 182), (202, 255, 191), (160, 196, 255), (189, 178, 255)]
        self.PlayerKey = False
        self.RenderWidth = self.Split_num - 1

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
            for line in f_open.readlines():
                m = MapObj(line.strip("\n"))
                t.append(m)
        return t

    def draw(self):
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

        color_count = 0
        for idx, row_chars in enumerate(rows):
            if color_count > 4:
                color_count = 0
            r, g, b = self.Colors[color_count]
            s = f"rgb({r},{g},{b})"

            line = self.scale_row(row_chars, target_w)
            self.Console.print(line + "\n", end='', style=s, overflow="crop", no_wrap=True)

            for _ in range(extra_counts[idx]):
                filler_chars = [' ' if c in ('S', 'K', 'E') else c for c in row_chars]
                filler_line = self.scale_row(filler_chars, target_w)
                self.Console.print(filler_line + "\n", end='', style=s, overflow="crop", no_wrap=True)

            color_count = color_count + 1
        sleep(0.01)

    def clear(self):
        sys.stdout.write('\033[H')
        sys.stdout.flush()

    def find_player(self):
        count = 0
        for item in self.Data:
            if item.Char == 'S':
                return count
            count += 1

    def update_player(self, ):
        player_index = self.find_player()
        a = self.make_move(player_index)

        if a == 1:
            return True
        return False

    def player_move_right(self, index):
        if self.Data[index + 1].Char != 'L':
            if self.Data[index + 1].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[index + 1]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'

    def player_move_left(self, index):
        if self.Data[index - 1].Char != 'L':
            if self.Data[index - 1].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[index - 1]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1

    def player_move_up(self, index):
        if self.Data[index - self.Split_num].Char != 'L':
            if self.Data[index - self.Split_num].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[index - self.Split_num]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'

    def player_move_down(self, index):
        if self.Data[index + self.Split_num].Char != 'L':
            if self.Data[index + self.Split_num].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = 'E' if index == self.ExitIndex else '@'
            player = self.Data[index + self.Split_num]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1

    def make_move(self, player_index=None):
        if player_index is None:
            player_index = self.find_player()
        if player_index is None:
            return 1

        if player_index == self.ExitIndex and self.PlayerKey == True:
            return 1

        data_ = list()
        data_len = len(self.Data)
        valid_chars = ('@', 'E', 'K')
        # find all the valid moves
        if player_index + 1 < data_len and self.Data[player_index + 1].Char in valid_chars:
            data_.append(('right', self.Data[player_index + 1].Player_count))
        if player_index - 1 >= 0 and self.Data[player_index - 1].Char in valid_chars:
            data_.append(('left', self.Data[player_index - 1].Player_count))
        if player_index - self.Split_num >= 0 and self.Data[player_index - self.Split_num].Char in valid_chars:
            data_.append(('up', self.Data[player_index - self.Split_num].Player_count))
        if player_index + self.Split_num < data_len and self.Data[player_index + self.Split_num].Char in valid_chars:
            data_.append(('down', self.Data[player_index + self.Split_num].Player_count))

        if not data_:
            return 1

        smallest = list()
        for item in data_:
            w, p = item
            smallest.append(p)
        smallest.sort()
        small = smallest[0]

        width = self.RenderWidth
        status_lines = [
            self.format_status_line(f"Valid moves{data_}", width),
            self.format_status_line(f"Player index: {player_index}", width),
            self.format_status_line(f"Moves {self.MoveMade}", width),
            self.format_status_line(f"Player has key {self.PlayerKey}", width),
        ]
        for s_line in status_lines:
            self.Console.print(s_line, style="bold red", overflow="crop", no_wrap=True)
        for item in data_:
            w, p = item
            if p == small:
                if w == "right":
                    self.player_move_right(player_index)
                    break
                if w == "left":
                    self.player_move_left(player_index)
                    break
                if w == "up":
                    self.player_move_up(player_index)
                    break
                if w == "down":
                    self.player_move_down(player_index)
                    break
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
    return parser.parse_args(argv)


def main(argv=None):
    parse_args(argv)
    app = App()
    try:
        app.Console.clear()
        map_one(app)
        sleep(10)
        app.Console.clear()
        map_two(app)
        sleep(10)
        app.Console.clear()
    except KeyboardInterrupt:
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
    app.ExitIndex = 158
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
