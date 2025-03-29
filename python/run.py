import pyxel
import random
import math
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
    valid_positions = [
        (x, y) for y, row in enumerate(map_data)
        for x, cell in enumerate(row)
        if cell == 0
    ]
    x, y = random.choice(valid_positions)
    pixel_x = x * tile_size + tile_size // 2
    pixel_y = y * tile_size + tile_size // 2
    return pixel_x, pixel_y

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
        if self.wall_hits < 0:  # 通常パーティクル
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
    
    Attributes:
        x (float): X座標（ピクセル単位）
        y (float): Y座標（ピクセル単位）
        speed (float): 移動速度（ピクセル/フレーム）
        half_size (int): キャラクターの半径（ピクセル）
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
        """パワード状態をリセット"""
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
            
            # パワード状態以降は揺れを適用
            if self.current_speed >= self.powerd_speed:
                # 速度に応じて揺れ幅を増加
                speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
                current_amplitude = self.wave_amplitude * (1 + speed_ratio * self.speed_wave_factor)
                
                # サイン波による揺れの計算
                wave = math.sin(self.wave_time) * current_amplitude
                
                # 進行方向に対して垂直に揺れを適用
                if base_dx != 0:  # 左右移動の場合
                    base_dy += wave
                elif base_dy != 0:  # 上下移動の場合
                    base_dx += wave
                
                self.wave_time += 0.2
        else:
            # キー入力がない場合は基本速度にリセット
            self.current_speed = self.base_speed

        # 移動値を返す（実際の移動はAppクラスで行う）
        return base_dx, base_dy

    def draw(self) -> None:
        # パワー状態の円エフェクト描画
        if self.current_speed >= self.powerd_speed:
            # 速度に応じて円のサイズ範囲を計算
            speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
            min_size = self.BASE_MIN_CIRCLE_SIZE * (1 + speed_ratio)  # 最大で2倍
            max_size = self.BASE_MAX_CIRCLE_SIZE * (1 + speed_ratio)  # 最大で2倍
            
            # サインカーブで円のサイズをアニメーション
            circle_size = min_size + (math.sin(self.circle_animation_time) + 1) * (max_size - min_size) / 2
            self.circle_animation_time += 0.2
            
            # 円を描画（プレイヤーの周りに）
            center_x = int(self.x)
            center_y = int(self.y)
            radius = int(circle_size)
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        if (x - center_x) ** 2 + (y - center_y) ** 2 >= (radius - 1) ** 2:
                            pyxel.pset(x, y, 10)  # 黄色で円を描画

        # プレイヤー本体の描画
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
        
        # 各種タイマーの更新
        if self.spawn_timer < self.SPAWN_DURATION:
            self.spawn_timer += 1
        if self.multiply_cooldown > 0:
            self.multiply_cooldown -= 1
        
        # 基本移動量の計算
        base_dx = base_dy = 0
        if self.direction == 0:    # 左
            base_dx = -self.speed
        elif self.direction == 1:  # 右
            base_dx = self.speed
        elif self.direction == 2:  # 上
            base_dy = -self.speed
        else:                      # 下
            base_dy = self.speed

        # サイン波による揺れの計算
        wave = math.sin(self.time + self.wave_offset) * self.wave_amplitude
        
        # 進行方向に対して垂直に揺れを適用
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
            self.wave_offset = random.uniform(0, 6.28)  # 衝突時に位相をリセット

        # 時間更新
        self.time += 0.1

        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.randint(0, 3)
            self.direction_timer = random.randint(30, 90)
            self.wave_offset = random.uniform(0, 6.28)  # 方向変更時に位相をリセット

    def draw(self) -> None:
        # エネミーの色状態を決定
        if self.spawn_timer < self.SPAWN_DURATION:
            # 生まれて1秒は緑
            color = 11
        elif self.multiply_cooldown > 0:
            # クールダウン中は暗い青と青の点滅（10フレームごと）
            color = 1 if (pyxel.frame_count // 10) % 2 == 0 else 12
        else:
            # 通常時は青
            color = 12

        # 4x4サイズで描画
        pyxel.rect(int(self.x - self.half_size),
                   int(self.y - self.half_size),
                   4, 4, color)

class App:
    """
    ゲームの主要クラス
    """
    def __init__(self):
        pyxel.init(240, 240, title="Maze Walk", fps=30)
        self.tile_size = 16
        self.max_enemies = 60  # エネミーの最大数
        self.initial_enemies = 6  # 初期エネミー数
        
        # 壁衝突のデバッグ表示用
        self.wall_flash_timer = 0  # 点滅タイマー

        self.map_data = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player = Player(player_x, player_y)
        
        # エネミーの初期化
        self.enemies = []
        self.particles = []  # パーティクルエフェクト用リスト
        for _ in range(self.initial_enemies):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))

        pyxel.run(self.update, self.draw)

    def create_death_effect(self, x: float, y: float, color: int):
        """エネミー消滅時のエフェクトを生成"""
        angles = [i * math.pi / 4 for i in range(8)]  # 8方向
        for angle in angles:
            self.particles.append(Particle(x, y, angle, 2.0, color))

    def create_spark_effect(self, x: float, y: float, speed: float):
        """壁衝突時の火花エフェクトを生成"""
        print(f"火花生成開始: 位置({x:.1f}, {y:.1f}), 速度: {speed:.2f}")
        for i in range(3):
            angle = random.uniform(0, math.pi * 2)
            print(f"火花{i + 1}: 角度: {angle:.2f}rad")
            p = Particle(x, y, angle, speed, 10, True)  # 黄色で火花を生成
            self.particles.append(p)
            print(f"火花{i + 1}: dx={p.dx:.2f}, dy={p.dy:.2f}")
        print(f"火花生成完了: 総パーティクル数 {len(self.particles)}")

    def is_wall(self, grid_x: int, grid_y: int) -> bool:
        if 0 <= grid_x < len(self.map_data[0]) and 0 <= grid_y < len(self.map_data):
            return self.map_data[grid_y][grid_x] == 1
        return True

    def can_move_to(self, x: float, y: float, half_size: int = 2) -> bool:
        corners = [
            (int((x - half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y - half_size) // self.tile_size)),
            (int((x - half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
            (int((x + half_size) // self.tile_size), int((y + half_size) // self.tile_size)),
        ]
        return all(not self.is_wall(cx, cy) for cx, cy in corners)

    def check_collision(self, x1: float, y1: float, x2: float, y2: float) -> bool:
        """2つのキャラクター間の衝突判定"""
        return abs(x1 - x2) < 4 and abs(y1 - y2) < 4

    def update(self):
        # プレイヤーの位置を保存（衝突時の位置戻し用）
        old_x = self.player.x
        old_y = self.player.y
        
        # プレイヤーの移動値を取得
        dx, dy = self.player.update(self.can_move_to)
        
        # 移動判定と壁衝突チェック
        if self.can_move_to(self.player.x + dx, self.player.y + dy):
            self.player.x += dx
            self.player.y += dy
        else:
            print("壁衝突検知")
            print(f"現在速度: {self.player.current_speed:.2f}, パワー速度: {self.player.powerd_speed:.2f}")
            
            if self.player.current_speed >= self.player.powerd_speed:
                print("火花生成処理開始")
                self.wall_flash_timer = 5  # 5フレームの点滅
                
                # パワー状態での壁衝突時に火花を生成
                self.create_spark_effect(
                    self.player.x, self.player.y, 
                    self.player.current_speed
                )
                
                print("パワー状態での壁衝突！")
                # ブースト中は壁衝突をカウントしない
                if self.player.kill_boost_timer <= 0:
                    self.player.wall_hits += 1
                
                # はじき返し処理
                bounce_x = -dx * self.player.WALL_BOUNCE if dx != 0 else 0
                bounce_y = -dy * self.player.WALL_BOUNCE if dy != 0 else 0
                
                # はじき返し先が移動可能な場合のみ適用
                if self.can_move_to(self.player.x + bounce_x, self.player.y + bounce_y):
                    self.player.x += bounce_x
                    self.player.y += bounce_y
                
                # 設定回数以上の壁衝突でパワー解除（ブースト中は無効）
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
                    # パワー状態でエネミーを撃破
                    self.create_death_effect(enemy.x, enemy.y, 12)  # 青色で粒子を生成
                    # ブースト時間をリセット（延長）
                    self.player.kill_boost_timer = self.player.KILL_BOOST_DURATION
                    continue
                else:
                    # 通常状態の場合
                    collision_occurred = True
                    enemy.direction = random.randint(0, 3)
                    
                    # エネミーが増殖可能な状態なら新しいエネミーを生成
                    total_enemies = len(self.enemies)
                    if total_enemies < self.max_enemies and enemy.multiply_cooldown == 0:
                        # 2体のエネミーを生成
                        for _ in range(2):
                            if total_enemies + _ < self.max_enemies:
                                new_x, new_y = find_valid_position(self.map_data, self.tile_size)
                                new_enemy = Enemy(new_x, new_y)
                                remaining_enemies.append(new_enemy)
                        # 親エネミーにクールダウンを設定
                        enemy.multiply_cooldown = enemy.MULTIPLY_COOLDOWN
            
            remaining_enemies.append(enemy)

        # パーティクルとエネミーの衝突判定＆更新
        updated_particles = []
        for particle in self.particles:
            # エネミーとの衝突判定
            killed_enemies = particle.check_enemy_collision(remaining_enemies)
            for killed_enemy in killed_enemies:
                remaining_enemies.remove(killed_enemy)
                self.create_death_effect(killed_enemy.x, killed_enemy.y, 12)

            # パーティクルの更新
            if particle.update(self.can_move_to):
                updated_particles.append(particle)
        
        # パーティクルの更新を反映
        self.particles = updated_particles
        
        # エネミー衝突時の処理
        if collision_occurred and not self.player.current_speed >= self.player.powerd_speed:
            self.player.x = old_x
            self.player.y = old_y
            self.player.current_speed = self.player.base_speed

        # 生存エネミーのリストを更新
        self.enemies = remaining_enemies

    def draw(self):
        pyxel.cls(0)
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    # すべての壁を一時的に黄色に
                    color = 10 if self.wall_flash_timer > 0 else 7
                    pyxel.rect(x * self.tile_size, y * self.tile_size,
                               self.tile_size, self.tile_size, color)
        
        # 点滅タイマーの更新
        if self.wall_flash_timer > 0:
            self.wall_flash_timer -= 1

        for enemy in self.enemies:
            enemy.draw()

        # パーティクルの描画
        for particle in self.particles:
            particle.draw()

        # UI情報の表示
        speed_ratio = self.player.current_speed / self.player.base_speed
        speed_text = f"SPEED: x{speed_ratio:.2f}"
        enemy_text = f"ENEMY: {len(self.enemies)}/{self.max_enemies}"
        
        # 速度表示（中央）
        x = 240 // 2 - len(speed_text) * 2
        pyxel.text(x, 4, speed_text, 0)  # 黒色テキスト
        
        # エネミー数表示（右上）
        x = 240 - len(enemy_text) * 4 - 4
        pyxel.text(x, 4, enemy_text, 0)  # 黒色テキスト
        
        self.player.draw()

App()
