import pyxel
import random
from typing import List, Tuple

def find_valid_position(map_data: List[List[int]], tile_size: int) -> Tuple[float, float]:
    """
    マップ内の通路（値が0）からランダムな位置を返す
    
    Args:
        map_data (List[List[int]]): マップデータ
        tile_size (int): タイルのサイズ
    
    Returns:
        Tuple[float, float]: 選択された位置のピクセル座標（x, y）
    """
    # 通路の座標リストを作成
    valid_positions = [
        (x, y) for y, row in enumerate(map_data)
        for x, cell in enumerate(row)
        if cell == 0
    ]
    
    # ランダムな通路を選択
    x, y = random.choice(valid_positions)
    
    # タイル座標をピクセル座標に変換（タイルの中心に配置）
    pixel_x = x * tile_size + tile_size // 2
    pixel_y = y * tile_size + tile_size // 2
    
    return pixel_x, pixel_y

class Character:
    """
    キャラクターの基本クラス
    
    Attributes:
        x (float): X座標（ピクセル単位）
        y (float): Y座標（ピクセル単位）
        speed (float): 移動速度（ピクセル/フレーム）
        half_size (int): キャラクターの半径（ピクセル）
    """
    
    def __init__(self, x: float, y: float, speed: float):
        """
        キャラクターの初期化
        
        Args:
            x (float): 初期X座標（ピクセル単位）
            y (float): 初期Y座標（ピクセル単位）
            speed (float): 移動速度
        """
        self.x = x
        self.y = y
        self.speed = speed
        self.half_size = 2  # 4x4ピクセルの半分

class Player(Character):
    """
    プレイヤーキャラクターを管理するクラス
    """
    
    def __init__(self, x: float, y: float):
        """
        プレイヤーの初期化
        
        Args:
            x (float): 初期X座標（ピクセル単位）
            y (float): 初期Y座標（ピクセル単位）
        """
        super().__init__(x, y, speed=1.0)

    def update(self, can_move_to) -> None:
        """
        プレイヤーの状態を更新
        
        Args:
            can_move_to: 移動可能判定関数（座標を受け取りboolを返す）
        """
        # 移動量の計算
        dx = dy = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            dx = -self.speed
        elif pyxel.btn(pyxel.KEY_RIGHT):
            dx = self.speed
        if pyxel.btn(pyxel.KEY_UP):
            dy = -self.speed
        elif pyxel.btn(pyxel.KEY_DOWN):
            dy = self.speed

        # 移動可能なら位置を更新
        new_x = self.x + dx
        new_y = self.y + dy
        if can_move_to(new_x, new_y):
            self.x = new_x
            self.y = new_y

    def draw(self) -> None:
        """プレイヤーを描画（赤い4x4ピクセルの四角形）"""
        pyxel.rect(int(self.x - self.half_size),
                  int(self.y - self.half_size),
                  4, 4, 8)  # 色8は赤

class Enemy(Character):
    """
    敵キャラクターを管理するクラス
    """
    
    def __init__(self, x: float, y: float):
        """
        敵キャラクターの初期化
        
        Args:
            x (float): 初期X座標（ピクセル単位）
            y (float): 初期Y座標（ピクセル単位）
        """
        super().__init__(x, y, speed=0.8)  # プレイヤーより遅い速度に設定
        self.direction = random.randint(0, 3)  # ランダムな初期方向
        self.direction_timer = random.randint(30, 90)  # 方向転換までのタイマー

    def update(self, can_move_to) -> None:
        """
        敵キャラクターの状態を更新
        
        Args:
            can_move_to: 移動可能判定関数（座標を受け取りboolを返す）
        """
        # 移動方向に基づく移動量を計算
        dx = dy = 0
        if self.direction == 0:    # 左
            dx = -self.speed
        elif self.direction == 1:  # 右
            dx = self.speed
        elif self.direction == 2:  # 上
            dy = -self.speed
        else:                      # 下
            dy = self.speed

        # 移動後の座標を計算
        new_x = self.x + dx
        new_y = self.y + dy

        # 移動可能なら位置を更新
        if can_move_to(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            # 壁にぶつかった場合は方向をランダムに変更
            self.direction = random.randint(0, 3)

        # 方向転換タイマーの更新
        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.randint(0, 3)
            self.direction_timer = random.randint(30, 90)

    def draw(self) -> None:
        """敵キャラクターを描画（青い4x4ピクセルの四角形）"""
        pyxel.rect(int(self.x - self.half_size),
                  int(self.y - self.half_size),
                  4, 4, 12)  # 色12は青

class App:
    """
    ゲームの主要クラス
    
    マップ、プレイヤー、敵の管理と描画を行う
    """
    def __init__(self):
        """
        ゲームの初期化
        - ウィンドウとグラフィックスの設定
        - マップデータの定義
        - プレイヤーとエネミーの初期化
        """
        # ウィンドウを240x240で初期化（fpsは30）
        pyxel.init(240, 240, title="Maze Walk", fps=30)

        # タイル1個のサイズ（16ピクセル）
        self.tile_size = 16

        # マップデータ（2次元リスト）
        # 1 = 壁、0 = 通路
        # 15x7のシンプルな迷路デザイン
        self.map_data = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

        # プレイヤーとエネミーの初期化
        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player = Player(player_x, player_y)
        
        # エネミーの初期化（3体）
        self.enemies = []
        for _ in range(3):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))

        # アプリケーション開始
        pyxel.run(self.update, self.draw)

    def is_wall(self, grid_x: int, grid_y: int) -> bool:
        """
        指定されたマス（タイル）が壁かどうかを返す
        範囲外も壁として扱う
        
        Args:
            grid_x (int): X座標（タイル単位）
            grid_y (int): Y座標（タイル単位）
        Returns:
            bool: 壁ならTrue
        """
        if 0 <= grid_x < len(self.map_data[0]) and 0 <= grid_y < len(self.map_data):
            return self.map_data[grid_y][grid_x] == 1
        return True

    def can_move_to(self, x: float, y: float, half_size: int = 2) -> bool:
        """
        指定されたピクセル座標(x, y)に移動できるかを判定
        キャラの4つの角をチェックする
        
        Args:
            x (float): X座標（ピクセル単位）
            y (float): Y座標（ピクセル単位）
            half_size (int): キャラクターの半径
        Returns:
            bool: 移動可能ならTrue
        """
        corners = [
            (int((x - half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x - half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
        ]
        return all(not self.is_wall(cx, cy) for cx, cy in corners)

    def update(self):
        """
        ゲームの状態を更新
        - プレイヤーの移動処理
        - エネミーの移動処理
        """
        self.player.update(self.can_move_to)
        for enemy in self.enemies:
            enemy.update(self.can_move_to)

    def draw(self):
        """
        ゲーム画面の描画
        - 背景（黒）
        - マップ（壁は灰色）
        - エネミー（青）
        - プレイヤー（赤）
        """
        # 背景クリア（黒）
        pyxel.cls(0)

        # マップ描画（壁のみ）
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    pyxel.rect(x * self.tile_size, y * self.tile_size,
                             self.tile_size, self.tile_size, 7)

        # エネミーの描画
        for enemy in self.enemies:
            enemy.draw()

        # プレイヤーの描画
        self.player.draw()

# アプリ起動
App()
