import pyxel

class App:
    def __init__(self):
        px.init(160, 256, title="Pyxel Caver")
        self.x = pyxel.width // 2  # キャラクターの初期X位置
        self.y = pyxel.height // 2  # キャラクターの初期Y位置
        pyxel.mouse(True)  # マウス（タッチ）を有効化
        pyxel.run(self.update, self.draw)

    def update(self):
        # マウス（タッチ）位置をキャラクターの位置として更新
        self.x = pyxel.mouse_x
        self.y = pyxel.mouse_y

    def draw(self):
        pyxel.cls(0)  # 画面クリア（黒）
        pyxel.rect(self.x - 4, self.y - 4, 8, 8, 9)  # 8x8のキャラ（青）

App()
