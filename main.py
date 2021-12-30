from time import sleep
import sys
from rich.console import Console


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

    def init_data(self, file=r'map.txt\map.txt'):
        t = list()
        with open(file) as f_open:
            for line in f_open.readlines():
                m = MapObj(line.strip("\n"))
                t.append(m)
        return t

    def draw(self):
        tmp = ""
        color_count = 0
        for item in self.Data:
            if color_count > 4:
                color_count = 0
            if item.Char == '@':
                tmp = tmp + ' '
            elif item.Char == 'L':
                tmp = tmp + '\n'
            else:
                tmp = tmp + item.Char
            if item.Char == 'L':
                r, g, b = self.Colors[color_count]
                s = f"rgb({r},{g},{b})"

                self.Console.print(tmp, end='', style=s)
                sleep(0.01)
                tmp = ''
                color_count = color_count + 1

    def clear(self):
        sys.stdout.write('\033[2;0f')
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
            player.Char = '@'
            player = self.Data[index + 1]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'

    def player_move_left(self, index):
        if self.Data[index - 1].Char != 'L':
            if self.Data[index - 1].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = '@'
            player = self.Data[index - 1]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1

    def player_move_up(self, index):
        if self.Data[index - self.Split_num].Char == "K":
            self.PlayerKey = True
        if self.Data[index - self.Split_num].Char != 'L':
            player = self.Data[index]
            player.Char = '@'
            player = self.Data[index - self.Split_num]
            player.Player_count = player.Player_count + 1
            player.Char = 'S'

    def player_move_down(self, index):
        if self.Data[index + self.Split_num].Char != 'L':
            if self.Data[index + self.Split_num].Char == "K":
                self.PlayerKey = True
            player = self.Data[index]
            player.Char = '@'
            player = self.Data[index + self.Split_num]
            player.Char = 'S'
            player.Player_count = player.Player_count + 1

    def make_move(self, player_index):
        player_index = self.find_player()

        if player_index == self.ExitIndex and self.PlayerKey == True:
            return 1

        data_ = list()
        # find all the valid moves
        if self.Data[player_index + 1].Char == '@' or self.Data[player_index + 1].Char == 'E' or self.Data[
            player_index + 1].Char == 'K':
            data_.append(('right', self.Data[player_index + 1].Player_count))
        if self.Data[player_index - 1].Char == '@' or self.Data[player_index - 1].Char == 'E' or self.Data[
            player_index - 1].Char == 'K':
            data_.append(('left', self.Data[player_index - 1].Player_count))
        if self.Data[player_index - self.Split_num].Char == '@' or self.Data[
            player_index - self.Split_num].Char == 'E' or self.Data[player_index - self.Split_num].Char == 'K':
            data_.append(('up', self.Data[player_index - self.Split_num].Player_count))
        if self.Data[player_index + self.Split_num].Char == '@' or self.Data[
            player_index + self.Split_num].Char == 'E' or self.Data[player_index + self.Split_num].Char == 'K':
            data_.append(('down', self.Data[player_index + self.Split_num].Player_count))

        smallest = list()
        for item in data_:
            w, p = item
            smallest.append(p)
        smallest.sort()
        small = smallest[0]

        self.Console.print(f"---------------Valid moves{data_}-------------------", style="bold red")
        self.Console.print(f"---------------Player index: {player_index}---------------", style="bold red")
        self.Console.print(f"---------------Moves {self.MoveMade}---------------", style="bold red")
        self.Console.print(f"---------------Player has key {self.PlayerKey}---------------", style="bold red")
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


def main():
    try:
        app = App()
        map_one(app)
        sleep(10)
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
    app.Data = app.init_data(r"map2.txt\map2.txt")
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
