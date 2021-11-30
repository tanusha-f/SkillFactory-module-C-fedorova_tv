from random import randint
from time import sleep


class Dot:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Dot({self.x}, {self.y})"


class BoardException(Exception):
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Клетка с такими координатами за пределами поля! Введите корректные координаты."


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эту клетку! Введите другой ход"


class BoardWrongShipException(BoardException):
    pass


class Ship:
    def __init__(self, bow, le, o):
        self.bow = bow
        self.le = le
        self.o = o
        self.lives = le

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.le):
            cur_x = self.bow.x
            cur_y = self.bow.y

            if self.o == 0:
                cur_x += i
            elif self.o == 1:
                cur_y += i

            ship_dots.append(Dot(cur_x, cur_y))
        return ship_dots


class Board:
    def __init__(self, hid=False, size=10):
        self.size = size
        self.hid = hid

        self.count = 0

        self.field = [[" "] * size for _ in range(size)]
        self.busy = []
        self.ships = []

    def __str__(self):
        res = "   "
        for i in range(1, self.size+1):
            res += f"|{i:2d} "
        res += "| "
        for i, row in enumerate(self.field):
            res += f"\n{i + 1:2d} | " + " | ".join(row) + " | "

        if self.hid:
            res = res.replace("■", " ")
        return res

    def out(self, d):
        return not ((0 <= d.x < self.size) and (0 <= d.y < self.size))

    def contour(self, ship, verb=False):
        near = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for d in ship.dots:
            for dx, dy in near:
                cur = Dot(d.x + dx, d.y + dy)
                if not self.out(cur) and cur not in self.busy:
                    if verb:
                        self.field[cur.x][cur.y] = "."
                    self.busy.append(cur)

    def cont_diag(self, d):
        diag = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dx, dy in diag:
            cur = Dot(d.x + dx, d.y + dy)
            if not self.out(cur) and cur not in self.busy:
                self.field[cur.x][cur.y] = "."
                self.busy.append(cur)

    def add_ship(self, ship):
        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()

        for d in ship.dots:
            self.field[d.x][d.y] = "■"
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    def begin(self):
        self.busy = []

    def shot(self, d):
        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.field[d.x][d.y] = "x"
                if ship.lives == 0:
                    self.count += 1
                    self.contour(ship, verb=True)
                    print("Корабль уничтожен!!! ", end='')
                    if self.count != 10:
                        print("Сделайте следующий ход.")
                    return True
                else:
                    print("Корабль ранен! Сделайте следующий ход.")
                    self.cont_diag(d)
                    return True

        self.field[d.x][d.y] = "."
        print("Мимо!")
        return False


class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy
        self.size = board.size

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)


class AI(Player):
    def ask(self):
        while True:
            d = Dot(randint(0, self.size - 1), randint(0, self.size - 1))
            if d in self.enemy.busy:
                continue
            print(d.x + 1, d.y + 1)
            return d


class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()

            if len(cords) != 2:
                print("Введите две координаты!")
                continue

            x, y = cords

            if not x.isdigit() or not y.isdigit():
                print("Введите числа!")
                continue

            d = Dot(int(x) - 1, int(y) - 1)

            if self.enemy.out(d):
                raise BoardOutException()

            if d in self.enemy.busy:
                raise BoardUsedException()

            return d


class Game:
    def __init__(self, size=10):
        self.size = size
        self.lens = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

        self.greet()

        ans = input("Хотите сами создать свое поле? (Да/Нет)   ").replace(" ", "")
        if ans == "Да":
            pl = self.create_board()
        elif ans == "Нет":
            pl = self.random_board()
        else:
            pl = self.random_board()
            print("Некорректный ответ! Поле будет создано случайным образом.")

        co = self.random_board()
        print("\nПоля созданы! Игра начинается!!!\n")
        co.hid = True

        self.us = User(pl, co)
        self.ai = AI(co, pl)

    def ask_ship(self, le):
        while True:
            if le > 1:
                xy = input(f"\nВведите координаты носа корабля из {le} клеток: ").split()
            else:
                xy = input(f"\nВведите координаты корабля из {le} клетки: ").split()

            if len(xy) != 2:
                print("Введите две координаты!")
                continue

            x, y = xy

            if not (x.isdigit()) or not (y.isdigit()):
                print("Введите числа!")
                continue

            x, y = int(x), int(y)
            return Dot(x - 1, y - 1)

    def ask_ship_dir(self):
        while True:
            di = input("Введите положение (1 - горизонтальное, 0 - вертикальное): ").replace(" ", "")

            if di != "1" and di != "0":
                print("Введите 1 или 0!")
                continue

            return int(di)

    def ask_new(self):
        while True:
            ans = input("Хотите начать всё заново? (Да/Нет)   ").replace(" ", "")

            if ans != "Да" and ans != "Нет":
                print("Введите Да или Нет!")
                continue

            return ans

    def try_board(self):
        board = Board(size=self.size)
        attempts = 0
        for le in self.lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), le, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass

        board.begin()
        return board

    def create_board(self):
        board = None
        le = 0
        di = 0
        print("\nИтак, начинаем создавать Ваше поле.")
        print("Коордитаны клетки вводятся в виде: номер строки и номер столбца через пробел.\n")
        while le < len(self.lens):
            if le == 0:
                board = Board(size=self.size)
                print(board)

            xy = self.ask_ship(self.lens[le])
            if self.lens[le] != 1:
                di = self.ask_ship_dir()

            ship = Ship(xy, self.lens[le], di)
            try:
                board.add_ship(ship)
                print(board)
            except BoardWrongShipException:
                print("Так нельзя поставить корабль!")
                ans = self.ask_new()
                if ans == "Да":
                    le = -1
                    print("\nНачинаем заново:")
                else:
                    le -= 1
                    print("Повторите попытку размещения корабля:")
            le += 1

        board.begin()
        return board

    def random_board(self):
        board = None
        while board is None:
            board = self.try_board()
        return board

    def print_two(self):
        us_b = str(self.us.board).split("\n")
        ai_b = str(self.ai.board).split("\n")

        res = "\n" + "  " * self.size + "Ваше поле:" + "    " * self.size + "Поле компьютера:"
        for row1, row2 in zip(us_b, ai_b):
            res += f"\n  {row1}           {row2} "
        res += "\n" + "-" * 105
        return res

    def start(self):
        num = 0
        print(self.print_two())
        while True:
            if num % 2 == 0:
                repeat = self.us.move()
            else:
                print("Ход компьютера: ", end='')
                sleep(1.5)
                repeat = self.ai.move()

            print(self.print_two())

            if repeat:
                num -= 1

            if self.ai.board.count == len(self.lens):
                print("Вы выиграли!!!")
                break

            if self.us.board.count == len(self.lens):
                print("Компьютер выиграл!!!")
                break

            num += 1

    def greet(self):
        print("-" * 105)
        print('''                                Добро пожаловать в игру "Морской бой" !!!\n
    Ваш противник - компьютер!\n
    Основные правила:\n
    1) На поле располагаются следующие корабли: 1 корабль на 4 клетки, 2 корабля на 3 клетки,
3 корабля на 2 клетки и 4 корябля на 1 клетку.
    2) Корабли должны находиться на расстоянии минимум одна клетка друг от друга.
    3) Есть выбор: самостоятельно расставить корабли на поле или поле будет создано случайным образом.
    4) Чтобы сделать ход, необходимо ввести координаты клетки через пробел:
первое число - номер строки, второе число - номер столбца.
    5) Переход хода противнику происходит в случае промаха.
    6) Побеждает тот, кто быстрее разгромит корабли противника.\n
    Удачи!!!\n''')
        print("-" * 105)


g = Game()
g.start()
