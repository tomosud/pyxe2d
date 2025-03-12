import pyxel

class App:
    def __init__(self):
        pyxel.init(120, 200, title="Touch Move Vertical", fps=60)  # 縦長の画面
        self.x = pyxel.width // 2  # キャラのX座標（中央）
        self.y = pyxel.height // 2  # キャラのY座標（中央）
        pyxel.mouse(True)  # マウス（タッチ）を有効化
        pyxel.run(self.update, self.draw)

    def update(self):
        # タッチ位置（マウス位置）をキャラの位置に更新
        self.x = pyxel.mouse_x
        self.y = pyxel.mouse_y

    def draw(self):
        pyxel.cls(0)  # 画面クリア（黒）
        pyxel.rect(self.x - 5, self.y - 5, 10, 10, 11)  # 10x10のキャラ（青）

App()
