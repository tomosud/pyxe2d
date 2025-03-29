import pyxel
import random
import math
from typing import List, Tuple

def find_valid_position(map_data: List[List[int]], tile_size: int) -> Tuple[float, float]:
    """
    マップ内の通路（値が0）の中からランダムな位置を返す関数
    """
    valid_positions = [
        (x, y) for y, row in enumerate(map_data)
        for x, cell in enumerate(row)
        if cell == 0
    ]
    x, y = random.choice(valid_positions)
    pixel_x = x * tile_size + tile_size // 2
    pixel_y = y * tile_size + tile_size // 2
    return pixel_x, pixel_y

def generate_maze(cols: int, rows: int) -> List[List[int]]:
    """
    再帰的バックトラッキングを用いて迷路の二次元配列を生成する関数
    - 外周は必ず壁（1）となる
    - 内部は通路（0）が連結した迷路になる
    """
    # 迷路全体を壁で初期化（1が壁、0が通路）
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def carve_passages(cx: int, cy: int):
        """
        現在のセル(cx,cy)から隣接セルへ通路を掘っていく再帰関数
        ※セル座標は必ず奇数となる前提
        """
        # 上下左右（2マス先）の方向リスト
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        # ランダムに並び替え（必要に応じて進行方向のバイアスも調整可能）
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            # 隣のセルが外枠以外かつ未訪問（壁）の場合
            if 0 < nx < cols - 1 and 0 < ny < rows - 1 and maze[ny][nx] == 1:
                # 現在のセルと隣のセルの間の壁も通路にする
                maze[cy + dy // 2][cx + dx // 2] = 0
                maze[ny][nx] = 0
                carve_passages(nx, ny)

    # 開始位置を (1,1) に固定して通路を掘る
    maze[1][1] = 0
    carve_passages(1, 1)

    # 加速用に、中央行をすべて通路にして長い直線通路を確保する
    mid_row = rows // 2
    for x in range(1, cols - 1):
        maze[mid_row][x] = 0

    return maze

def generate_map_data(screen_width: int, screen_height: int, tile_size: int) -> List[List[int]]:
    """
    画面サイズとタイルサイズから迷路のサイズ（列数・行数）を計算し、
    連結した迷路となる二次元配列を生成する関数
    - 外周は必ず壁になるように調整する
    - 生成後、加速用の長い通路も確保する
    """
    # タイルの個数を計算
    cols = screen_width // tile_size
    rows = screen_height // tile_size
    # 迷路生成には奇数サイズが望ましいので、偶数の場合は1減らす
    if cols % 2 == 0:
        cols -= 1
    if rows % 2 == 0:
        rows -= 1
    return generate_maze(cols, rows)

class Particle:
    """パーティクルエフェクト用のクラス"""
    def __init__(self, x: float, y: float, angle: float, speed: float, color: int, is_spark: bool = False):
        self.x = x
        self.y = y
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.color = color
        self.life = 50  # 1秒間表示
        self.is_spark = is_spark
        self.wall_hits = 0 if is_spark else -1  # -1は壁判定なし、火花は2回まで
        self.half_size = 1  # パーティクルサイズの半分

    def check_enemy_collision(self, enemies):
        """エネミーとの衝突判定"""
        if not self.is_spark:
            return []
        
        killed_enemies = []
        for enemy in enemies:
            if abs(self.x - enemy.x) < 4 and abs(self.y - enemy.y) < 4:
                killed_enemies.append(enemy)
        return killed_enemies

    def update(self, can_move_to):
        if self.wall_hits < 0:  # 通常パーティクルの場合
            self.x += self.dx
            self.y += self.dy
            self.life -= 1
            return self.life > 0
        
        # 火花パーティクルの場合
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        if can_move_to(new_x, new_y, self.half_size):
            self.x = new_x
            self.y = new_y
        else:
            # 壁との衝突処理
            self.wall_hits += 1
            if self.wall_hits >= 8:
                return False

            # 反射角度の計算
            if not can_move_to(new_x, self.y, self.half_size):
                self.dx = -self.dx  # X方向の反転
            if not can_move_to(self.x, new_y, self.half_size):
                self.dy = -self.dy  # Y方向の反転

        self.life -= 1
        return self.life > 0 and self.wall_hits < 2

    def draw(self):
        pyxel.rect(int(self.x - self.half_size), 
                   int(self.y - self.half_size),
                   2, 2, self.color)

class Character:
    """
    キャラクターの基本クラス
    """
    def __init__(self, x: float, y: float, speed: float):
        self.x = x
        self.y = y
        self.speed = speed
        self.half_size = 2  # 4x4ピクセルの半分

class Player(Character):
    """
    プレイヤーキャラクターを管理するクラス
    """
    def __init__(self, x: float, y: float):
        # 基本パラメータ
        self.base_speed = 0.1               # 初期速度（ピクセル/フレーム）
        self.max_speed = self.base_speed * 65.0  # 最大速度
        self.acceleration_time = 5.0        # 最大速度に達するまでの時間（秒）
        self.powerd_speed = self.max_speed * 0.3 # 攻撃可能な速度
        self.fps = 30                     # フレームレート（fps）
        
        # パワード状態の制御用パラメータ
        self.wall_hits = 0                # 壁への衝突回数
        self.MAX_WALL_HITS = 2           # パワー解除までの壁衝突回数
        self.WALL_BOUNCE = 4             # 壁衝突時のはじき返し距離（ピクセル）
        self.kill_boost_timer = 0        # エネミー撃破後のブースト時間
        self.KILL_BOOST_DURATION = 30    # ブースト継続時間（1秒）

        # 各フレームごとに加える加速度を計算
        frames_needed = self.acceleration_time * self.fps
        self.acceleration = (self.max_speed - self.base_speed) / frames_needed
        
        # 揺れパラメータ
        self.wave_amplitude = 0.2          # 基本の揺れ幅
        self.speed_wave_factor = 1.5       # 速度による揺れの増加係数
        self.wave_time = 0                 # 揺れの時間経過
        
        # パワー状態の円エフェクトパラメータ
        self.circle_animation_time = 0     # アニメーション用タイマー
        self.BASE_MIN_CIRCLE_SIZE = 6     # 基本の最小円サイズ
        self.BASE_MAX_CIRCLE_SIZE = 8     # 基本の最大円サイズ
        
        super().__init__(x, y, speed=self.base_speed)
        self.current_speed = self.base_speed

    def reset_power_state(self):
        """パワード状態をリセットする"""
        self.current_speed = self.base_speed
        self.wall_hits = 0
        self.kill_boost_timer = 0

    def update(self, can_move_to) -> None:
        import math
        
        # ブースト時間の更新
        if self.kill_boost_timer > 0:
            self.kill_boost_timer -= 1

        base_dx = base_dy = 0
        is_moving = False

        if pyxel.btn(pyxel.KEY_LEFT):
            base_dx = -self.current_speed
            is_moving = True
        elif pyxel.btn(pyxel.KEY_RIGHT):
            base_dx = self.current_speed
            is_moving = True
        if pyxel.btn(pyxel.KEY_UP):
            base_dy = -self.current_speed
            is_moving = True
        elif pyxel.btn(pyxel.KEY_DOWN):
            base_dy = self.current_speed
            is_moving = True

        if is_moving:
            # キー入力中は加速度分だけ速度を増加（最大速度に達するまで）
            self.current_speed = min(self.current_speed + self.acceleration, self.max_speed)
            
            # パワード状態以降は揺れを適用する
            if self.current_speed >= self.powerd_speed:
                # 速度に応じて揺れ幅を増加
                speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
                current_amplitude = self.wave_amplitude * (1 + speed_ratio * self.speed_wave_factor)
                
                # サイン波による揺れの計算
                wave = math.sin(self.wave_time) * current_amplitude
                
                # 進行方向に対して垂直に揺れを適用する
                if base_dx != 0:  # 左右移動の場合
                    base_dy += wave
                elif base_dy != 0:  # 上下移動の場合
                    base_dx += wave
                
                self.wave_time += 0.2
        else:
            # キー入力がない場合は基本速度にリセットする
            self.current_speed = self.base_speed

        # 移動値を返す（実際の移動はAppクラスで行う）
        return base_dx, base_dy

    def draw(self) -> None:
        # パワー状態の円エフェクトを描画する
        if self.current_speed >= self.powerd_speed:
            # 速度に応じて円のサイズ範囲を計算する
            speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
            min_size = self.BASE_MIN_CIRCLE_SIZE * (1 + speed_ratio)  # 最大で2倍
            max_size = self.BASE_MAX_CIRCLE_SIZE * (1 + speed_ratio)  # 最大で2倍
            
            # サインカーブで円のサイズをアニメーションさせる
            circle_size = min_size + (math.sin(self.circle_animation_time) + 1) * (max_size - min_size) / 2
            self.circle_animation_time += 0.2
            
            # プレイヤーの周りに円を描画する
            center_x = int(self.x)
            center_y = int(self.y)
            radius = int(circle_size)
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        if (x - center_x) ** 2 + (y - center_y) ** 2 >= (radius - 1) ** 2:
                            pyxel.pset(x, y, 10)  # 黄色で円を描画する

        # プレイヤー本体を描画する
        color = 10 if self.current_speed >= self.powerd_speed else 8
        pyxel.rect(int(self.x - self.half_size),
                   int(self.y - self.half_size),
                   4, 4, color)

class Enemy(Character):
    """
    敵キャラクターを管理するクラス
    """
    def __init__(self, x: float, y: float):
        super().__init__(x, y, speed=0.8)
        self.direction = random.randint(0, 3)
        self.direction_timer = random.randint(30, 90)
        # 揺れ動きのパラメータ
        self.wave_offset = random.uniform(0, 6.28)  # 0〜2πのランダムな初期位相
        self.wave_amplitude = 0.3  # 揺れの振幅
        self.time = 0  # 時間経過
        
        # 出現エフェクトのパラメータ
        self.SPAWN_DURATION = 30  # 出現エフェクトの継続フレーム数（30fps = 1秒）
        self.spawn_timer = 0      # 出現からの経過フレーム
        
        # 増殖クールダウンのパラメータ
        self.MULTIPLY_COOLDOWN = 150  # 増殖後のクールダウン時間（30fps = 1秒）
        self.multiply_cooldown = 0   # 増殖クールダウンタイマー

    def update(self, can_move_to) -> None:
        import math
        
        # 各種タイマーを更新する
        if self.spawn_timer < self.SPAWN_DURATION:
            self.spawn_timer += 1
        if self.multiply_cooldown > 0:
            self.multiply_cooldown -= 1
        
        # 基本の移動量を計算する
        base_dx = base_dy = 0
        if self.direction == 0:    # 左に移動
            base_dx = -self.speed
        elif self.direction == 1:  # 右に移動
            base_dx = self.speed
        elif self.direction == 2:  # 上に移動
            base_dy = -self.speed
        else:                      # 下に移動
            base_dy = self.speed

        # サイン波による揺れを計算する
        wave = math.sin(self.time + self.wave_offset) * self.wave_amplitude
        
        # 進行方向に対して垂直の揺れを適用する
        if self.direction in [0, 1]:  # 左右移動の場合
            dy = wave
            dx = base_dx
        else:  # 上下移動の場合
            dx = wave
            dy = base_dy

        new_x = self.x + dx
        new_y = self.y + dy

        if can_move_to(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            self.direction = random.randint(0, 3)
            self.wave_offset = random.uniform(0, 6.28)  # 壁との衝突時に位相をリセットする

        # 時間を更新する
        self.time += 0.1

        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.randint(0, 3)
            self.direction_timer = random.randint(30, 90)
            self.wave_offset = random.uniform(0, 6.28)  # 方向変更時に位相をリセットする

    def draw(self) -> None:
        # 状態に応じてエネミーの色を決定する
        if self.spawn_timer < self.SPAWN_DURATION:
            # 出現後1秒間は緑色で描画する
            color = 11
        elif self.multiply_cooldown > 0:
            # クールダウン中は暗い青と青の点滅（10フレームごと）
            color = 1 if (pyxel.frame_count // 10) % 2 == 0 else 12
        else:
            # 通常時は青色で描画する
            color = 12

        # 4x4サイズでエネミーを描画する
        pyxel.rect(int(self.x - self.half_size),
                   int(self.y - self.half_size),
                   4, 4, color)

class App:
    """
    ゲームの主要クラス
    """
    def __init__(self):
        # 画面サイズの設定
        screen_width = 240
        screen_height = 340
        pyxel.init(screen_width, screen_height, title="Maze Walk", fps=30)
        # pyxel.init(240, 340, title="Maze Walk", fps=30)  # デバッグ用（コメントアウト済み）
        self.tile_size = 16
        self.max_enemies = 200  # エネミーの最大数
        self.initial_enemies = 30  # 初期エネミー数
        
        # 壁衝突のデバッグ表示用タイマー
        self.wall_flash_timer = 0  # 点滅タイマー

        # 画面サイズとタイルサイズからマップの大きさを計算し、迷路を自動生成する
        self.map_data = generate_map_data(screen_width, screen_height, self.tile_size)

        # プレイヤーの初期位置を決定する
        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player = Player(player_x, player_y)
        
        # エネミーおよびパーティクルの初期化
        self.enemies = []
        self.particles = []  # パーティクルエフェクト用リスト
        for _ in range(self.initial_enemies):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))
        
        # NEXT STAGE表示用タイマー（0のときは通常状態）
        self.stage_clear_timer = 0

        pyxel.run(self.update, self.draw)

    def reset_stage(self):
        """ステージリセット処理（プレイヤー・エネミー・パーティクルを初期状態に戻す）"""
        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player.x, self.player.y = player_x, player_y
        self.player.reset_power_state()
        self.particles = []
        self.enemies = []
        for _ in range(self.initial_enemies):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))
        # print("ステージリセット完了")  # デバッグ用出力（コメントアウト済み）

    def create_death_effect(self, x: float, y: float, color: int):
        """エネミー消滅時のエフェクトを生成する"""
        angles = [i * math.pi / 4 for i in range(8)]  # 8方向にエフェクトを生成
        for angle in angles:
            self.particles.append(Particle(x, y, angle, 2.0, color))

    def create_spark_effect(self, x: float, y: float, speed: float):
        """壁衝突時の火花エフェクトを生成する"""
        # print(f"火花生成開始: 位置({x:.1f}, {y:.1f}), 速度: {speed:.2f}")  # デバッグ用出力（コメントアウト済み）
        for i in range(3):
            angle = random.uniform(0, math.pi * 2)
            # print(f"火花{i + 1}: 角度: {angle:.2f}rad")  # デバッグ用出力（コメントアウト済み）
            p = Particle(x, y, angle, speed, 10, True)  # 黄色で火花を生成
            self.particles.append(p)
            # print(f"火花{i + 1}: dx={p.dx:.2f}, dy={p.dy:.2f}")  # デバッグ用出力（コメントアウト済み）
        # print(f"火花生成完了: 総パーティクル数 {len(self.particles)}")  # デバッグ用出力（コメントアウト済み）

    def is_wall(self, grid_x: int, grid_y: int) -> bool:
        if 0 <= grid_x < len(self.map_data[0]) and 0 <= grid_y < len(self.map_data):
            return self.map_data[grid_y][grid_x] == 1
        return True

    def can_move_to(self, x: float, y: float, half_size: int = 2) -> bool:
        """
        指定されたピクセル座標が移動可能かどうかを判定する
        （四隅のセルがすべて壁でない場合、移動可能とする）
        """
        corners = [
            (int((x - half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x - half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
        ]
        return all(not self.is_wall(cx, cy) for cx, cy in corners)

    def check_collision(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """2つのキャラクター間の衝突を判定する"""
        return abs(x1 - x2) < 4 and abs(y1 - y2) < 4

    def update(self):
        # ステージクリア中は通常の更新を行わず、タイマーが0になったらステージをリセットする
        if self.stage_clear_timer > 0:
            self.stage_clear_timer -= 1
            if self.stage_clear_timer == 0:
                self.reset_stage()
            return

        # プレイヤーの位置を保存（衝突時に元の位置に戻すため）
        old_x = self.player.x
        old_y = self.player.y
        
        # プレイヤーの移動値を取得する
        dx, dy = self.player.update(self.can_move_to)
        
        # 移動可能かどうかの判定と壁衝突時の処理
        if self.can_move_to(self.player.x + dx, self.player.y + dy):
            self.player.x += dx
            self.player.y += dy
        else:
            # print("壁衝突検知")  # デバッグ用出力（コメントアウト済み）
            # print(f"現在速度: {self.player.current_speed:.2f}, パワー速度: {self.player.powerd_speed:.2f}")  # デバッグ用出力（コメントアウト済み）
            
            if self.player.current_speed >= self.player.powerd_speed:
                # print("火花生成処理開始")  # デバッグ用出力（コメントアウト済み）
                self.wall_flash_timer = 5  # 5フレーム間、壁の色を点滅させる
                
                # パワー状態での壁衝突時に火花エフェクトを生成する
                self.create_spark_effect(
                    self.player.x, self.player.y, 
                    self.player.current_speed
                )
                
                # print("パワー状態での壁衝突！")  # デバッグ用出力（コメントアウト済み）
                # ブースト中は壁衝突の回数をカウントしない
                if self.player.kill_boost_timer <= 0:
                    self.player.wall_hits += 1
                
                # はじき返し処理（壁から離れるように移動する）
                bounce_x = -dx * self.player.WALL_BOUNCE if dx != 0 else 0
                bounce_y = -dy * self.player.WALL_BOUNCE if dy != 0 else 0
                
                # はじき返し先が移動可能な場合のみ適用する
                if self.can_move_to(self.player.x + bounce_x, self.player.y + bounce_y):
                    self.player.x += bounce_x
                    self.player.y += bounce_y
                
                # 設定回数以上の壁衝突でパワー状態を解除する（ブースト中は無効）
                if (self.player.wall_hits >= self.player.MAX_WALL_HITS and 
                    self.player.kill_boost_timer <= 0):
                    self.player.reset_power_state()

        # エネミーの更新と衝突判定
        collision_occurred = False
        remaining_enemies = []

        for enemy in self.enemies:
            enemy.update(self.can_move_to)
            
            # プレイヤーとエネミーの衝突判定
            if self.check_collision(self.player.x, self.player.y, enemy.x, enemy.y):
                if self.player.current_speed >= self.player.powerd_speed:
                    # パワー状態でエネミーを撃破する
                    self.create_death_effect(enemy.x, enemy.y, 12)  # 青色でエフェクトを生成
                    # ブースト時間をリセット（延長）する
                    self.player.kill_boost_timer = self.player.KILL_BOOST_DURATION
                    continue
                else:
                    # 通常状態の場合
                    collision_occurred = True
                    enemy.direction = random.randint(0, 3)
                    
                    # エネミーが増殖可能な状態なら新たなエネミーを生成する
                    total_enemies = len(self.enemies)
                    if total_enemies < self.max_enemies and enemy.multiply_cooldown == 0:
                        # 2体のエネミーを生成する
                        for _ in range(2):
                            if total_enemies + _ < self.max_enemies:
                                new_x, new_y = find_valid_position(self.map_data, self.tile_size)
                                new_enemy = Enemy(new_x, new_y)
                                remaining_enemies.append(new_enemy)
                        # 親エネミーにクールダウンを設定する
                        enemy.multiply_cooldown = enemy.MULTIPLY_COOLDOWN
            
            remaining_enemies.append(enemy)

        # パーティクルとエネミーの衝突判定および更新処理
        updated_particles = []
        for particle in self.particles:
            # エネミーとの衝突判定を行う
            killed_enemies = particle.check_enemy_collision(remaining_enemies)
            for killed_enemy in killed_enemies:
                if killed_enemy in remaining_enemies:
                    remaining_enemies.remove(killed_enemy)
                    self.create_death_effect(killed_enemy.x, killed_enemy.y, 12)

            # パーティクルの更新を行う
            if particle.update(self.can_move_to):
                updated_particles.append(particle)
        
        # 更新後のパーティクルリストを反映する
        self.particles = updated_particles
        
        # エネミー衝突時、通常状態の場合はプレイヤーの位置を元に戻す
        if collision_occurred and not self.player.current_speed >= self.player.powerd_speed:
            self.player.x = old_x
            self.player.y = old_y
            self.player.current_speed = self.player.base_speed

        # 生存中のエネミーリストを更新する
        self.enemies = remaining_enemies

        # すべてのエネミーが消滅した場合、次のステージへ遷移する
        if not self.enemies:
            self.stage_clear_timer = 60  # 60フレーム（約2秒）表示

    def draw(self):
        pyxel.cls(0)
        # マップデータに基づいて壁を描画する
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    # 壁は、点滅時は黄色、通常はグレーで描画する
                    color = 10 if self.wall_flash_timer > 0 else 7
                    pyxel.rect(x * self.tile_size, y * self.tile_size,
                               self.tile_size, self.tile_size, color)
        
        # 点滅タイマーの更新
        if self.wall_flash_timer > 0:
            self.wall_flash_timer -= 1

        # エネミーの描画
        for enemy in self.enemies:
            enemy.draw()

        # パーティクルの描画
        for particle in self.particles:
            particle.draw()

        # UI情報の表示
        speed_ratio = self.player.current_speed / self.player.base_speed
        speed_text = f"SPEED: x{speed_ratio:.2f}"
        enemy_text = f"ENEMY: {len(self.enemies)}/{self.max_enemies}"
        
        # 速度表示（画面中央上部）
        x = 240 // 2 - len(speed_text) * 2
        pyxel.text(x, 4, speed_text, 0)  # 黒色テキスト
        
        # エネミー数表示（画面右上）
        x = 240 - len(enemy_text) * 4 - 4
        pyxel.text(x, 4, enemy_text, 0)  # 黒色テキスト
        
        # プレイヤーの描画
        self.player.draw()

        # ステージクリア時のメッセージ表示
        if self.stage_clear_timer > 0:
            text = "NEXT STAGE"
            x = 240 // 2 - len(text) * 2
            y = 240 // 2
            pyxel.text(x, y, text, 7)

App()
