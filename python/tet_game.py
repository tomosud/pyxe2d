import pyxel as px
import time as tm

# 符号関数：x > 0 のとき 1、x < 0 のとき -1、x = 0 のとき 0 を返す
def sign(x):
    return (x > 0) - (x < 0)

# ブロックと壁用のリソース（画像）をプログラム内で生成
def create_resources():
    # 色番号に対応する16進カラーコード（RRGGBB）
    block_colors = {
        0: "000000",  # 黒：背景
        1: "999999",  # グレー：壁
        2: "ff7f7f",  # ピンク：ブロック1
        3: "ff3c3c",  # 赤：ブロック2
        4: "ffa500",  # オレンジ：ブロック3
        5: "ffff00",  # 黄色：ブロック4
        6: "00ffff",  # 水色：ブロック5
        7: "0000ff",  # 青：ブロック6
        8: "800080",  # 紫：ブロック7
    }

    # Pyxelのカラーパレットに色を登録
    for color_index, hexcode in block_colors.items():
        r = int(hexcode[0:2], 16)
        g = int(hexcode[2:4], 16)
        b = int(hexcode[4:6], 16)
        # 24ビットカラーに変換してカラーパレットへ設定
        px.colors[color_index] = (r << 16) + (g << 8) + b

    # 各色のブロック画像を16x16で作成（イメージバンクの0番）
    for i in range(9):
        # 1色で埋めた16x16のタイルを作成
        tile = [str(i) * 16 for _ in range(16)]
        px.images[0].set(i * 16, 0, tile)

# メインアプリクラス（ゲームのロジック・状態管理）
class App():
    def __init__(self):
        # ゲーム画面のサイズを決定（行数、列数）
        self.row = 23        # 高さ（行数）
        self.clmn = 14       # 幅（列数）

        # Pyxelを初期化（画面サイズ320x行×16ピクセル）
        px.init(320, self.row * 16 + 16, title="Tetris", display_scale=2)

        # 自前で画像・色などのリソースを作成
        create_resources()

        # ブロック落下速度の初期値（小さいほど速い）
        self.distinit = 20

        # ブロック定義（色番号, 回転数, サイズ, 各回転パターン）
        self.l = []
        self.l.append([2, 4, 3, ("001","111","000"), ("010","010","011"), ("000","111","100"), ("110","010","010")])
        self.l.append([3, 4, 3, ("100","111","000"), ("011","010","010"), ("000","111","001"), ("010","010","110")])
        self.l.append([4, 4, 3, ("010","111","000"), ("010","011","010"), ("000","111","010"), ("010","110","010")])
        self.l.append([5, 2, 4, ("0000","1111","0000","0000"), ("0100","0100","0100","0100")])
        self.l.append([6, 2, 3, ("000","110","011"), ("010","110","100")])
        self.l.append([7, 2, 3, ("000","011","110"), ("010","011","001")])
        self.l.append([8, 1, 2, ("11","11")])  # 正方形ブロック（回転なし）

        # 初期座標
        self.tinit = 0
        self.linit = 5

        # ゲーム状態を初期化して開始
        self.gameinit()

        # Pyxelアプリケーションの実行開始（メインループ）
        px.run(self.update, self.draw)

    # ゲームの状態をリセット（初期化）
    def gameinit(self):
        self.dist = self.distinit   # 落下速度
        self.score = 0              # 得点
        self.linecnt = 0            # 消したライン数
        self.blkcnt = 1             # 落としたブロック数
        self.mh = 0                 # マウスホイール値
        self.gmovflg = 0            # ゲームオーバーフラグ
        self.t0 = tm.time()         # タイマー用基準時間
        self.bx = self.linit        # ブロックのX座標
        self.by = self.tinit        # ブロックのY座標
        self.set = 0                # ブロックの回転状態
        self.typ = px.rndi(0, 6)    # ブロックの種類（ランダム）

        # 操作エリアのマップ（2D配列）を作成
        self.lbox = [[0 for i in range(self.clmn)] for j in range(self.row + 1)]

        # 左右の壁を作成（色1）
        for i in range(self.row):
            self.lbox[i][1] = 1
            self.lbox[i][self.clmn - 2] = 1

        # 底面の壁
        for i in range(1, self.clmn - 1):
            self.lbox[self.row][i] = 1

    # ブロックを1段落とす処理
    def blkdrop(self):
        oldby = self.by
        self.by += 1
        if not self.chkbox():  # 衝突チェック
            self.by = oldby
            self.lockbox()  # 固定化

    # ブロックを固定（マップに書き込む）
    def lockbox(self):
        for j in range(self.l[self.typ][2]):
            for i in range(self.l[self.typ][2]):
                if self.l[self.typ][3 + self.set][j][i] == "1":
                    self.lbox[self.by + j][self.bx + i] = self.l[self.typ][0]
        self.chkline()

    # ラインが揃ったかをチェックし、消去処理
    def chkline(self):
        lll = []
        sc = 0
        for j in range(self.row):
            cnt = 0
            for i in range(2, self.clmn - 2):
                cnt += sign(self.lbox[j][i])
            lll.append(cnt)

        for j in range(self.row):
            if lll[j] == 10:
                sc += 1
                self.linecnt += 1
                for i in range(j, 0, -1):
                    self.lbox[i] = self.lbox[i - 1]
                self.lbox[0] = [0, 1] + [0]*(self.clmn - 4) + [1, 0]

        if sc > 0:
            self.score += 10 * 2 ** sc

        self.newblk()

    # 新しいブロックを出現させる処理
    def newblk(self):
        self.typ = px.rndi(0, 6)
        self.set = 0
        self.bx, self.by = self.linit, self.tinit
        self.blkcnt += 1
        if not self.chkbox():
            self.gameover()
        self.dist = max(1, self.distinit - self.blkcnt // 10)

    # ゲームオーバー処理
    def gameover(self):
        self.gmovflg = 1

    # ブロックが他と重なっていないかをチェック
    def chkbox(self):
        for j in range(self.l[self.typ][2]):
            for i in range(self.l[self.typ][2]):
                if self.l[self.typ][3 + self.set][j][i] == "1":
                    if self.lbox[self.by + j][self.bx + i] >= 1:
                        return False
        return True

    # フレーム毎に呼ばれる更新処理
    def update(self):
        if self.gmovflg == 0:
            # ブロック落下タイミング
            if tm.time() - self.t0 >= self.dist / 10:
                self.blkdrop()
                self.t0 = tm.time()

            # 左右移動（マウスホイール）
            self.mh = -sign(px.mouse_wheel)
            if self.mh:
                oldbx = self.bx
                self.bx += self.mh
                if not self.chkbox():
                    self.bx = oldbx

            # 左右キー移動
            elif px.btnp(px.KEY_LEFT) or px.btnp(px.KEY_RIGHT):
                oldbx = self.bx
                if px.btnp(px.KEY_LEFT):
                    self.bx -= 1
                else:
                    self.bx += 1
                if not self.chkbox():
                    self.bx = oldbx

            # 落下（右クリックまたは下キー）
            elif px.btn(px.MOUSE_BUTTON_RIGHT) or px.btn(px.KEY_DOWN):
                self.blkdrop()
                self.t0 = tm.time()

            # 回転（左クリック、スペース、上キー）
            if px.btnp(px.MOUSE_BUTTON_LEFT) or px.btnp(px.KEY_SPACE) or px.btnp(px.KEY_UP):
                oldset = self.set
                self.set = (self.set + 1) % self.l[self.typ][1]
                if not self.chkbox():
                    self.set = oldset
        else:
            # ゲームオーバー後のリトライ処理
            if px.btnp(px.MOUSE_BUTTON_LEFT) or px.btnp(px.KEY_RETURN) or px.btnp(px.KEY_KP_ENTER):
                self.gameinit()

    # 描画処理（毎フレーム呼ばれる）
    def draw(self):
        px.cls(0)  # 背景を黒でクリア

        # 左右と下の壁を描画
        for i in range(self.row):
            px.blt(0, i * 16, 0, 16, 0, 16, 16)
            px.blt(11 * 16, i * 16, 0, 16, 0, 16, 16)
        for i in range(1, self.clmn - 3):
            px.blt(i * 16, self.row * 16, 0, 16, 0, 16, 16)

        # 固定ブロックの描画
        for j in range(self.row):
            for i in range(2, self.clmn - 2):
                val = self.lbox[j][i]
                if val >= 1:
                    px.blt(i * 16 - 16, j * 16, 0, 16 * val, 0, 16, 16)

        # 操作中ブロックの描画
        for j in range(self.l[self.typ][2]):
            for i in range(self.l[self.typ][2]):
                if self.l[self.typ][3 + self.set][j][i] == "1":
                    val = self.l[self.typ][0]
                    px.blt((self.bx + i) * 16 - 16, (self.by + j) * 16, 0, 16 * val, 0, 16, 16)

        # スコア表示
        px.text(210, 40, f"SCORE: {self.score: >8}", 7)
        px.text(210, 60, f"LINE : {self.linecnt: >8}", 7)

        # ゲームオーバー表示
        if self.gmovflg == 1:
            px.text(100, 150, "GAME OVER", 7)
            px.text(80, 170, "Click or Enter to Retry", 7)

# 実行開始
App()
