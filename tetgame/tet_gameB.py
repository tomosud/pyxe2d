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

BLOCK_COLORS = {
    "テ": "ff66cc",
    "ト": "66ccff",
    "リ": "ffcc66",
    "ス": "99ff99",
    "bg": "000000"
}

CELL_SIZE = 1
PLAY_WIDTH = 100
PLAY_HEIGHT = 115

FALL_SPEED_INIT = 0.1
MOVE_DELAY_INIT = 0.1
SPEED_MULTIPLIER = 0.75

class App:
    def __init__(self):
        # ボタンの設定を追加
        self.btn_width = 20
        self.btn_height = 16
        self.btn_margin = 5
        screen_height = PLAY_HEIGHT + self.btn_height + self.btn_margin * 2

        # 画面幅に合わせてボタンの合計幅を調整
        total_margin = self.btn_margin * 3  # 3つの間隔
        self.btn_width = (PLAY_WIDTH - total_margin) // 4  # 4つのボタンで均等に分割
        
        pyxel.init(PLAY_WIDTH, screen_height, title="テトリス", display_scale=4)
        self.set_colors()
        self.set_blocks()
        self.reset()
        
        # ボタンの位置を設定（画面幅一杯に配置）
        button_base_y = PLAY_HEIGHT + self.btn_margin
        
        self.buttons = [
            {"x": 0, "y": button_base_y, "w": self.btn_width, "h": self.btn_height, "text": "<", "key": pyxel.KEY_LEFT},
            {"x": self.btn_width + self.btn_margin, "y": button_base_y, "w": self.btn_width, "h": self.btn_height, "text": ">", "key": pyxel.KEY_RIGHT},
            {"x": (self.btn_width + self.btn_margin) * 2, "y": button_base_y, "w": self.btn_width, "h": self.btn_height, "text": "v", "key": pyxel.KEY_DOWN},
            {"x": (self.btn_width + self.btn_margin) * 3, "y": button_base_y, "w": self.btn_width, "h": self.btn_height, "text": "R", "key": pyxel.KEY_SPACE}
        ]
        
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
        self.board = [[None for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]
        self.settled_blocks = []
        self.block_counter = 1
        self.tetris_chain_ids = set()
        self.spawn_new_block()
        self.gmovflg = 0
        self.t0 = time.time()
        self.t_move = time.time()
        self.score = 0
        self.stage = 1
        self.fall_speed = FALL_SPEED_INIT
        self.move_delay = MOVE_DELAY_INIT
        self.exploding = False
        self.explode_timer = 0
        self.explode_phase = 0
        self.explode_particles = []
        self.pause_phase = 0
        self.pause_duration = 0.6

    def reset_after_chain(self):
        self.board = [[None for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]
        self.settled_blocks = []
        self.block_counter = 1
        self.spawn_new_block()
        self.gmovflg = 0
        self.t0 = time.time()
        self.t_move = time.time()

    def spawn_new_block(self):
        self.block = random.choice(self.blocks)
        self.set = 0
        self.block_id = self.block_counter
        self.block_counter += 1
        self.char_type = self.block["char"]
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
                    if gy >= 0 and self.board[gy][gx] is not None:
                        return False
        return True

    def lock_block(self):
        grid = self.block["rotations"][self.set]
        positions = []
        for y, row in enumerate(grid):
            for x, val in enumerate(row):
                if val == "1":
                    gx = self.bx + x
                    gy = self.by + y
                    if 0 <= gx < PLAY_WIDTH and 0 <= gy < PLAY_HEIGHT:
                        self.board[gy][gx] = {
                            "block_id": self.block_id,
                            "char_type": self.char_type,
                            "color": self.block["color"]
                        }
                        positions.append((gx, gy))
        self.settled_blocks.append({
            "block_id": self.block_id,
            "char_type": self.char_type,
            "positions": positions
        })

        self.check_tetris_chain()

        if self.tetris_chain_ids:
            self.start_explosion()
        else:
            self.spawn_new_block()
            if not self.chkbox():
                self.gmovflg = 1

    def check_tetris_chain(self):
        id_to_char = {blk["block_id"]: blk["char_type"] for blk in self.settled_blocks}
        char_to_blocks = {"テ": [], "ト": [], "リ": [], "ス": []}
        position_map = {}
        for blk in self.settled_blocks:
            char_to_blocks[blk["char_type"]].append(blk)
            for pos in blk["positions"]:
                position_map[pos] = blk["block_id"]

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for te_blk in char_to_blocks["テ"]:
            te_id = te_blk["block_id"]
            te_neighbors = set()

            for x, y in te_blk["positions"]:
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    neighbor_id = position_map.get((nx, ny))
                    if neighbor_id and id_to_char.get(neighbor_id) == "ト":
                        te_neighbors.add(neighbor_id)

            for to_id in te_neighbors:
                to_blk = next(blk for blk in char_to_blocks["ト"] if blk["block_id"] == to_id)
                to_neighbors = set()
                for x, y in to_blk["positions"]:
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        neighbor_id = position_map.get((nx, ny))
                        if neighbor_id and id_to_char.get(neighbor_id) == "リ":
                            to_neighbors.add(neighbor_id)

                for ri_id in to_neighbors:
                    ri_blk = next(blk for blk in char_to_blocks["リ"] if blk["block_id"] == ri_id)
                    ri_neighbors = set()
                    for x, y in ri_blk["positions"]:
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            neighbor_id = position_map.get((nx, ny))
                            if neighbor_id and id_to_char.get(neighbor_id) == "ス":
                                ri_neighbors.add(neighbor_id)

                    for su_id in ri_neighbors:
                        chain_ids = [te_id, to_id, ri_id, su_id]
                        print(f"テトリス連鎖: {chain_ids}")
                        self.tetris_chain_ids.update(chain_ids)

    def start_explosion(self):
        self.exploding = True
        self.explode_timer = time.time()
        self.explode_phase = 0
        self.explode_particles = []
        self.pause_phase = 0
        self.pause_duration = 0.6

        for y in range(PLAY_HEIGHT):
            for x in range(PLAY_WIDTH):
                cell = self.board[y][x]
                if cell is not None:
                    is_chain = cell["block_id"] in self.tetris_chain_ids
                    self.explode_particles.append({
                        "x": x,
                        "y": y,
                        "vx": random.uniform(-3, 3),
                        "vy": random.uniform(-5, -1),
                        "color": 7 if is_chain else cell["color"],
                        "remove_phase": 2 if is_chain else 1
                    })

        self.board = [[None for _ in range(PLAY_WIDTH)] for _ in range(PLAY_HEIGHT)]

    def check_button_press(self, x, y, button):
        return (button["x"] <= x <= button["x"] + button["w"] and
                button["y"] <= y <= button["y"] + button["h"])

    def update(self):
        now = time.time()

        if self.gmovflg:
            # キーボードとタッチ両方でリスタート可能に
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                self.reset()
            return

        # マウス/タッチ入力の処理
        if pyxel.btn(pyxel.MOUSE_BUTTON_LEFT):
            mx, my = pyxel.mouse_x, pyxel.mouse_y
            for button in self.buttons:
                if self.check_button_press(mx, my, button):
                    if button["key"] == pyxel.KEY_SPACE and pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
                        # 回転は一回だけ
                        old = self.set
                        self.set = (self.set + 1) % 4
                        if not self.chkbox():
                            self.set = old
                    elif button["key"] == pyxel.KEY_DOWN:
                        # 下キーは加速
                        if now - self.t0 > self.fall_speed * 0.2:  # 感度調整
                            self.by += 1
                            if not self.chkbox():
                                self.by -= 1
                                self.lock_block()
                            self.t0 = now
                    elif now - self.t_move > self.move_delay * 0.5:  # 感度調整
                        # 左右移動
                        if button["key"] == pyxel.KEY_LEFT:
                            self.bx -= 1
                            if not self.chkbox():
                                self.bx += 1
                        elif button["key"] == pyxel.KEY_RIGHT:
                            self.bx += 1
                            if not self.chkbox():
                                self.bx -= 1
                        self.t_move = now

        if self.exploding:
            if self.pause_phase == 0:
                if time.time() - self.explode_timer > self.pause_duration:
                    self.pause_phase = 1
                    self.explode_timer = time.time()
                return
            elif self.pause_phase == 1:
                if time.time() - self.explode_timer > 0.2:
                    self.explode_phase += 1
                    self.explode_timer = time.time()
                    if self.explode_phase > 2:
                        self.exploding = False
                        self.score += 100
                        self.stage += 1
                        self.fall_speed *= SPEED_MULTIPLIER
                        self.move_delay *= SPEED_MULTIPLIER
                        self.tetris_chain_ids.clear()
                        self.explode_particles.clear()
                        self.reset_after_chain()
                return

        now = time.time()
        if pyxel.btn(pyxel.KEY_DOWN) or (now - self.t0 > self.fall_speed):
            self.by += 1
            if not self.chkbox():
                self.by -= 1
                self.lock_block()
            self.t0 = now

        if now - self.t_move > self.move_delay:
            if pyxel.btn(pyxel.KEY_LEFT):
                self.bx -= 2
                if not self.chkbox():
                    self.bx += 2
                self.t_move = now
            if pyxel.btn(pyxel.KEY_RIGHT):
                self.bx += 2
                if not self.chkbox():
                    self.bx -= 2
                self.t_move = now

        if pyxel.btnp(pyxel.KEY_SPACE):
            old = self.set
            self.set = (self.set + 1) % 4
            if not self.chkbox():
                self.set = old

    def draw_arrow(self, x, y, direction):
        # ボタンの中心座標を計算
        cx = x + self.btn_width // 2
        cy = y + self.btn_height // 2

        if direction == "left":
            # 左向き三角形
            pyxel.tri(cx + 5, cy - 5, cx + 5, cy + 5, cx - 5, cy, 7)
        elif direction == "right":
            # 右向き三角形
            pyxel.tri(cx - 5, cy - 5, cx - 5, cy + 5, cx + 5, cy, 7)
        elif direction == "down":
            # 下向き三角形
            pyxel.tri(cx - 5, cy - 5, cx + 5, cy - 5, cx, cy + 5, 7)
        elif direction == "rotate":
            # 回転アイコン（矢印付き円）
            pyxel.circb(cx, cy, 4, 7)
            # 矢印
            pyxel.tri(cx + 4, cy - 2, cx + 4, cy + 2, cx + 7, cy, 7)

    def draw(self):
        pyxel.cls(0)

        for y in range(PLAY_HEIGHT):
            for x in range(PLAY_WIDTH):
                cell = self.board[y][x]
                if cell is not None:
                    color = cell["color"]
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

        if self.exploding:
            if self.pause_phase == 0:
                for blk in self.settled_blocks:
                    if blk["block_id"] in self.tetris_chain_ids:
                        for (x, y) in blk["positions"]:
                            pyxel.pset(x, y, 7)
            else:
                for p in self.explode_particles:
                    if self.explode_phase >= p["remove_phase"]:
                        p["x"] += p["vx"]
                        p["y"] += p["vy"]
                        pyxel.pset(int(p["x"]), int(p["y"]), p["color"])

            pyxel.text(PLAY_WIDTH // 2 - 20, 40, "テトリス！", pyxel.frame_count % 16)

        pyxel.text(5, 5, f"SCORE: {self.score}", 7)
        pyxel.text(5, 15, f"STAGE: {self.stage}", 7)

        # ボタンの描画
        for i, button in enumerate(self.buttons):
            # ボタンの背景
            pyxel.rectb(button["x"], button["y"], button["w"], button["h"], 5)
            pyxel.rect(button["x"] + 1, button["y"] + 1, button["w"] - 2, button["h"] - 2, 1)
            
            # 矢印の描画
            if i == 0:  # 左
                self.draw_arrow(button["x"], button["y"], "left")
            elif i == 1:  # 右
                self.draw_arrow(button["x"], button["y"], "right")
            elif i == 2:  # 下
                self.draw_arrow(button["x"], button["y"], "down")
            else:  # 回転
                self.draw_arrow(button["x"], button["y"], "rotate")

        if self.gmovflg:
            pyxel.text(30, 50, "GAME OVER", 7)
            pyxel.text(20, 60, "Press ENTER \nto restart", 7)

App()
