import pyxel

class App:
    def __init__(self):
        # ウィンドウを240x240で初期化（fpsは30）
        pyxel.init(240, 240, title="Maze Walk", fps=30)

        # タイル1個のサイズ（16ピクセル）
        self.tile_size = 16

        # マップデータ（2次元リスト）
        # 1 = 壁、0 = 通路
        self.map_data = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

        # プレイヤーのスタート位置（ピクセル単位の座標）
        self.player_x = 1 * self.tile_size + self.tile_size // 2
        self.player_y = 1 * self.tile_size + self.tile_size // 2
        
        # プレイヤーの移動速度（ピクセル/フレーム）
        self.speed = 2.0

        # アプリケーション開始
        pyxel.run(self.update, self.draw)

    def update(self):
        # プレイヤーの移動量（初期値は0）
        dx = 0
        dy = 0

        # 矢印キーが押されている間、移動方向を設定
        if pyxel.btn(pyxel.KEY_LEFT):
            dx = -self.speed
        elif pyxel.btn(pyxel.KEY_RIGHT):
            dx = self.speed
        if pyxel.btn(pyxel.KEY_UP):
            dy = -self.speed
        elif pyxel.btn(pyxel.KEY_DOWN):
            dy = self.speed

        # 移動後の座標を計算
        new_x = self.player_x + dx
        new_y = self.player_y + dy

        # 移動先のマス目の座標を計算
        grid_x = int(new_x // self.tile_size)
        grid_y = int(new_y // self.tile_size)

        # 移動先が通路（=0）なら移動を許可
        if 0 <= grid_x < len(self.map_data[0]) and 0 <= grid_y < len(self.map_data):
            # 移動先のタイルの四隅をチェック
            corners = [
                (int((new_x - 4) // self.tile_size), int((new_y - 4) // self.tile_size)),
                (int((new_x + 4) // self.tile_size), int((new_y - 4) // self.tile_size)),
                (int((new_x - 4) // self.tile_size), int((new_y + 4) // self.tile_size)),
                (int((new_x + 4) // self.tile_size), int((new_y + 4) // self.tile_size))
            ]
            
            can_move = True
            for corner_x, corner_y in corners:
                if (0 <= corner_x < len(self.map_data[0]) and 
                    0 <= corner_y < len(self.map_data) and 
                    self.map_data[corner_y][corner_x] == 1):
                    can_move = False
                    break
            
            if can_move:
                self.player_x = new_x
                self.player_y = new_y

    def draw(self):
        # 画面を黒（0）でクリア
        pyxel.cls(0)

        # マップを描画（壁だけ描く）
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    # 壁（1）は灰色（7）で塗る
                    pyxel.rect(x * self.tile_size, y * self.tile_size,
                               self.tile_size, self.tile_size, 7)

        # プレイヤーのドットを表示（4x4ピクセル、赤色=8）
        px = int(self.player_x - 2)
        py = int(self.player_y - 2)
        pyxel.rect(px, py, 4, 4, 8)

# アプリ起動
App()
