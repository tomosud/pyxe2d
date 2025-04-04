import pyxel
import time
import random

# 文字ブロック定義（1ドット=1ピクセル）
KANA_BLOCKS = {
    "テ": [
        "000000000000000",
        "001111111111100",
        "001111111111100",
        "000000000000000",
        "000000000000000",
        "000000000000000",
        "111111111111111",
        "111111111111111",
        "000000111000000",
        "000000111000000",
        "000000111000000",
        "000001111000000",
        "000011110000000",
        "000111100000000",
        "000111000000000",
        "000000000000000"
    ],
    "ト": [
        "000000000000000",
        "001100000000000",
        "001100000000000",
        "001100000000000",
        "001100000000000",
        "001111000000000",
        "001111111000000",
        "001111111110000",
        "001100011111100",
        "001100000111100",
        "001100000000000",
        "001100000000000",
        "001100000000000",
        "001100000000000",
        "001100000000000",
        "000000000000000"
    ],
    "リ": [
        "000000000000000",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "011100000011100",
        "000000000111110",
        "000000000111000",
        "000000111111000",
        "000011111110000",
        "000011110000000",
        "000000000000000"
    ],
    "ス": [
        "000000000000000",
        "000000000000000",
        "011111111111110",
        "011111111111110",
        "000000000011100",
        "000000000111110",
        "000000000111000",
        "000000001111000",
        "000000011110000",
        "000000111111000",
        "000011111111100",
        "000111100111110",
        "011111000001111",
        "111110000000111",
        "011000000000011",
        "000000000000000"
    ]
}

# カラーパレット（Pyxel の 0〜15番）
BLOCK_COLORS = {
    "テ": "ff66cc",
    "ト": "66ccff",
    "リ": "ffcc66",
    "ス": "99ff99",
    "bg": "000000"
}

# 定数
CELL_SIZE = 1
PLAY_WIDTH = 100
PLAY_HEIGHT = 120

class App:
    def __init__(self):
        pyxel.init(PLAY_WIDTH, PLAY_HEIGHT, title="カタカナテトリス（高解像度）", display_scale=4)
        self.set_colors()
        self.set_blocks()
        self.reset()
        pyxel.run(self.update, self.draw)

    def set_colors(self):
        for i, (key, hexcode) in enumerate(BLOCK_COLORS.items()):
            r, g, b = int(hexcode[0:2], 16), int(hexcode[2:4], 16), int(hexcode[4:6], 16)
            pyxel.colors[i] = (r << 16) + (g << 8) + b
        for i in range(6):
            tile = [str(i) * CELL_SIZE for _ in range(CELL_SIZE)]
            pyxel.images[0].set(i * CELL_SIZE, 0, tile)

    def rotate_block(self, grid):
        h, w = len(grid), len(grid[0])
        return [''.join(grid[h - x - 1][y] for x in range(h)) for y in range(w)]

    def set_blocks(self):
        self.blocks = []
        for idx, (char, lines) in enumerate(KANA_BLOCKS.items()):
            rots = [lines]
            for _ in range(3):
                rots.append(self.rotate_block(rots[-1]))
            self.blocks.append({
                "char": char,
                "color": idx + 1,
                "rotations": rots
            })

    def reset(self):
        self.board = [[0 for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]
        self.spawn_new_block()
        self.gmovflg = 0
        self.t0 = time.time()

    def spawn_new_block(self):
        self.block = random.choice(self.blocks)
        self.set = 0
        grid = self.block["rotations"][self.set]
        self.bx = PLAY_WIDTH // 2 - len(grid[0]) // 2
        self.by = 0

    def chkbox(self):
        grid = self.block["rotations"][self.set]
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == "1":
                    gx, gy = self.bx + x, self.by + y
                    if gx < 0 or gx >= PLAY_WIDTH or gy >= PLAY_HEIGHT:
                        return False
                    if gy >= 0 and self.board[gy][gx] != 0:
                        return False
        return True

    def lock_block(self):
        grid = self.block["rotations"][self.set]
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == "1":
                    gx, gy = self.bx + x, self.by + y
                    if 0 <= gx < PLAY_WIDTH and 0 <= gy < PLAY_HEIGHT:
                        self.board[gy][gx] = self.block["color"]
        self.spawn_new_block()
        if not self.chkbox():
            self.gmovflg = 1

    def update(self):
        if self.gmovflg:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.reset()
            return

        if pyxel.btn(pyxel.KEY_DOWN) or (time.time() - self.t0 > 0.3):
            self.by += 1
            if not self.chkbox():
                self.by -= 1
                self.lock_block()
            self.t0 = time.time()

        if pyxel.btnp(pyxel.KEY_LEFT):
            self.bx -= 1
            if not self.chkbox():
                self.bx += 1
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.bx += 1
            if not self.chkbox():
                self.bx -= 1

        if pyxel.btnp(pyxel.KEY_SPACE):
            old = self.set
            self.set = (self.set + 1) % 4
            if not self.chkbox():
                self.set = old

    def draw(self):
        pyxel.cls(0)
        for y in range(PLAY_HEIGHT):
            for x in range(PLAY_WIDTH):
                color = self.board[y][x]
                if color != 0:
                    pyxel.blt(x, y, 0, color * CELL_SIZE, 0, CELL_SIZE, CELL_SIZE)

        grid = self.block["rotations"][self.set]
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == "1":
                    gx = self.bx + x
                    gy = self.by + y
                    if 0 <= gx < PLAY_WIDTH and 0 <= gy < PLAY_HEIGHT:
                        color = self.block["color"]
                        pyxel.blt(gx, gy, 0, color * CELL_SIZE, 0, CELL_SIZE, CELL_SIZE)

        if self.gmovflg:
            pyxel.text(30, 50, "GAME OVER", 7)
            pyxel.text(20, 60, "Press ENTER to restart", 7)

App()
