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
    ・外周は必ず壁（1）となる
    ・内部は通路（0）が連結した迷路になる
    """
    maze = [[1 for _ in range(cols)] for _ in range(rows)]

    def carve_passages(cx: int, cy: int):
        """
        現在のセル(cx, cy)から2マス先のセルへ通路を掘っていく再帰関数
        ※セル座標は必ず奇数となる前提
        """
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < cols - 1 and 0 < ny < rows - 1 and maze[ny][nx] == 1:
                maze[cy + dy // 2][cx + dx // 2] = 0
                maze[ny][nx] = 0
                carve_passages(nx, ny)

    maze[1][1] = 0
    carve_passages(1, 1)

    mid_row = rows // 2
    for x in range(1, cols - 1):
        maze[mid_row][x] = 0

    return maze

def generate_map_data(screen_width: int, screen_height: int, tile_size: int) -> List[List[int]]:
    """
    画面サイズとタイルサイズから迷路のサイズを計算し、迷路を生成する
    """
    cols = screen_width // tile_size
    rows = screen_height // tile_size
    if cols % 2 == 0:
        cols -= 1
    if rows % 2 == 0:
        rows -= 1
    return generate_maze(cols, rows)

class TouchController:
    """タッチ操作を管理するクラス"""
    def __init__(self):
        self.touch_start_x = None
        self.touch_start_y = None
        self.current_direction = [0, 0]  # [dx, dy]

    def update(self) -> Tuple[float, float]:
        """タッチ入力を更新し、移動方向を返す"""
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.touch_start_x = pyxel.mouse_x
            self.touch_start_y = pyxel.mouse_y
            self.current_direction = [0, 0]
        elif pyxel.btn(pyxel.MOUSE_BUTTON_LEFT) and self.touch_start_x is not None:
            dx = pyxel.mouse_x - self.touch_start_x
            dy = pyxel.mouse_y - self.touch_start_y
            
            # 最小移動距離（デッドゾーン）
            min_distance = 5
            length = math.sqrt(dx * dx + dy * dy)
            
            if length >= min_distance:
                # 方向の正規化
                self.current_direction = [dx / length, dy / length]
            else:
                self.current_direction = [0, 0]
        else:
            self.touch_start_x = None
            self.touch_start_y = None
            self.current_direction = [0, 0]
            
        return tuple(self.current_direction)

class Particle:
    """パーティクルエフェクト用のクラス"""
    def __init__(self, x: float, y: float, angle: float, speed: float, color: int, is_spark: bool = False):
        self.x = x
        self.y = y
        self.dx = math.cos(angle) * speed
        self.dy = math.sin(angle) * speed
        self.color = color
        self.life = 50
        self.is_spark = is_spark
        self.wall_hits = 0 if is_spark else -1
        self.half_size = 1

    def check_enemy_collision(self, enemies):
        if not self.is_spark:
            return []
        
        killed_enemies = []
        for enemy in enemies:
            if abs(self.x - enemy.x) < 4 and abs(self.y - enemy.y) < 4:
                killed_enemies.append(enemy)
        return killed_enemies

    def update(self, can_move_to):
        if self.wall_hits < 0:
            self.x += self.dx
            self.y += self.dy
            self.life -= 1
            return self.life > 0
        
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        if can_move_to(new_x, new_y, self.half_size):
            self.x = new_x
            self.y = new_y
        else:
            self.wall_hits += 1
            if self.wall_hits >= 8:
                return False
            if not can_move_to(new_x, self.y, self.half_size):
                self.dx = -self.dx
            if not can_move_to(self.x, new_y, self.half_size):
                self.dy = -self.dy

        self.life -= 1
        return self.life > 0 and self.wall_hits < 2

    def draw(self):
        pyxel.rect(int(self.x - self.half_size), 
                   int(self.y - self.half_size),
                   2, 2, self.color)

class Character:
    """キャラクターの基本クラス"""
    def __init__(self, x: float, y: float, speed: float):
        self.x = x
        self.y = y
        self.speed = speed
        self.half_size = 2

class Player(Character):
    """プレイヤーキャラクターを管理するクラス"""
    def __init__(self, x: float, y: float):
        self.base_speed = 0.1
        self.max_speed = self.base_speed * 65.0
        self.acceleration_time = 5.0
        self.powerd_speed = self.max_speed * 0.3
        self.fps = 30
        
        self.wall_hits = 0
        self.MAX_WALL_HITS = 2
        self.WALL_BOUNCE = 4
        self.kill_boost_timer = 0
        self.KILL_BOOST_DURATION = 30

        frames_needed = self.acceleration_time * self.fps
        self.acceleration = (self.max_speed - self.base_speed) / frames_needed
        
        self.wave_amplitude = 0.2
        self.speed_wave_factor = 1.5
        self.wave_time = 0
        
        self.circle_animation_time = 0
        self.circle_min_size = 4  # コリジョンサイズと同じ
        self.circle_max_size = 5  # わずかに大きく
        
        super().__init__(x, y, speed=self.base_speed)
        self.current_speed = self.base_speed
        self.direction = [0, 0]  # 現在の進行方向

    def reset_power_state(self):
        self.current_speed = self.base_speed
        self.wall_hits = 0
        self.kill_boost_timer = 0

    def update(self, dx: float, dy: float) -> Tuple[float, float]:
        if self.kill_boost_timer > 0:
            self.kill_boost_timer -= 1

        is_moving = dx != 0 or dy != 0

        if is_moving:
            # 進行方向を保存
            self.direction = [dx, dy]
            
            # ベクトルの正規化
            length = math.sqrt(dx * dx + dy * dy)
            normalized_dx = (dx / length) * self.current_speed
            normalized_dy = (dy / length) * self.current_speed

            self.current_speed = min(self.current_speed + self.acceleration, self.max_speed)
            if self.current_speed >= self.powerd_speed:
                speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
                current_amplitude = self.wave_amplitude * (1 + speed_ratio * self.speed_wave_factor)
                wave = math.sin(self.wave_time) * current_amplitude
                if abs(normalized_dx) > abs(normalized_dy):
                    normalized_dy += wave
                else:
                    normalized_dx += wave
                self.wave_time += 0.2
            return normalized_dx, normalized_dy
        else:
            self.direction = [0, 0]
            self.current_speed = self.base_speed
            return 0, 0

    def draw(self):
        if self.current_speed >= self.powerd_speed:
            speed_ratio = (self.current_speed - self.powerd_speed) / (self.max_speed - self.powerd_speed)
            min_size = self.circle_min_size * (1 + speed_ratio)
            max_size = self.circle_max_size * (1 + speed_ratio)
            circle_size = min_size + (math.sin(self.circle_animation_time) + 1) * (max_size - min_size) / 2
            self.circle_animation_time += 0.2
            
            center_x = int(self.x)
            center_y = int(self.y)
            radius = int(circle_size)
            for y in range(center_y - radius, center_y + radius + 1):
                for x in range(center_x - radius, center_x + radius + 1):
                    if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                        if (x - center_x) ** 2 + (y - center_y) ** 2 >= (radius - 1) ** 2:
                            pyxel.pset(x, y, 10)

        color = 10 if self.current_speed >= self.powerd_speed else 8
        pyxel.rect(int(self.x - self.half_size),
                   int(self.y - self.half_size),
                   4, 4, color)

        # 進行方向の表示
        if self.direction[0] != 0 or self.direction[1] != 0:
            line_length = 20
            end_x = self.x + self.direction[0] * line_length
            end_y = self.y + self.direction[1] * line_length
            pyxel.line(int(self.x), int(self.y),
                      int(end_x), int(end_y), 10)

class Enemy(Character):
    """敵キャラクターを管理するクラス"""
    def __init__(self, x: float, y: float):
        super().__init__(x, y, speed=0.8)
        self.direction = random.randint(0, 3)
        self.direction_timer = random.randint(30, 90)
        self.wave_offset = random.uniform(0, 6.28)
        self.wave_amplitude = 0.3
        self.time = 0
        
        self.SPAWN_DURATION = 30
        self.spawn_timer = 0
        
        self.MULTIPLY_COOLDOWN = 150
        self.multiply_cooldown = 0

    def update(self, can_move_to):
        if self.spawn_timer < self.SPAWN_DURATION:
            self.spawn_timer += 1
        if self.multiply_cooldown > 0:
            self.multiply_cooldown -= 1
        
        base_dx = base_dy = 0
        if self.direction == 0:
            base_dx = -self.speed
        elif self.direction == 1:
            base_dx = self.speed
        elif self.direction == 2:
            base_dy = -self.speed
        else:
            base_dy = self.speed

        wave = math.sin(self.time + self.wave_offset) * self.wave_amplitude
        if self.direction in [0, 1]:
            dx = base_dx
            dy = wave
        else:
            dx = wave
            dy = base_dy

        new_x = self.x + dx
        new_y = self.y + dy

        if can_move_to(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            self.direction = random.randint(0, 3)
            self.wave_offset = random.uniform(0, 6.28)

        self.time += 0.1
        self.direction_timer -= 1
        if self.direction_timer <= 0:
            self.direction = random.randint(0, 3)
            self.direction_timer = random.randint(30, 90)
            self.wave_offset = random.uniform(0, 6.28)

    def draw(self):
        if self.spawn_timer < self.SPAWN_DURATION:
            # 生成直後は白色
            color = 7
        elif self.multiply_cooldown > 0:
            color = 1 if (pyxel.frame_count // 10) % 2 == 0 else 12
        else:
            color = 12
            
        pyxel.rect(int(self.x - self.half_size),
                   int(self.y - self.half_size),
                   4, 4, color)

class App:
    """ゲームの主要クラス"""
    def __init__(self):
        self.screen_width = 240
        self.screen_height = 340
        pyxel.init(self.screen_width, self.screen_height, title="Maze Walk", fps=30, capture_sec=0)
        
        self.tile_size = 16
        self.max_enemies = 250
        self.initial_enemies = 30
        
        self.proliferation_probability = 0.1
        self.proliferation_interval = 5 * 30
        self.proliferation_count = 1
        self.proliferation_timer = 0
        
        self.wall_flash_timer = 0
        self.wall_green_timer = 0  # 壁を緑色にするタイマー

        # タッチコントローラーの設定
        self.touch_controller = TouchController()

        self.map_data = generate_map_data(self.screen_width, self.screen_height, self.tile_size)
        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player = Player(player_x, player_y)
        
        self.enemies = []
        self.particles = []
        for _ in range(self.initial_enemies):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))
        
        self.stage_clear_timer = 0

        pyxel.run(self.update, self.draw)

    def reset_stage(self):
        self.map_data = generate_map_data(self.screen_width, self.screen_height, self.tile_size)
        player_x, player_y = find_valid_position(self.map_data, self.tile_size)
        self.player.x, self.player.y = player_x, player_y
        self.player.reset_power_state()
        self.particles = []
        self.enemies = []
        for _ in range(self.initial_enemies):
            enemy_x, enemy_y = find_valid_position(self.map_data, self.tile_size)
            self.enemies.append(Enemy(enemy_x, enemy_y))

    def create_death_effect(self, x: float, y: float, color: int):
        angles = [i * math.pi / 4 for i in range(8)]
        for angle in angles:
            self.particles.append(Particle(x, y, angle, 2.0, color))

    def create_spark_effect(self, x: float, y: float, speed: float):
        for i in range(3):
            angle = random.uniform(0, math.pi * 2)
            p = Particle(x, y, angle, speed, 10, True)
            self.particles.append(p)

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
        return abs(x1 - x2) < 4 and abs(y1 - y2) < 4

    def update(self):
        if self.stage_clear_timer > 0:
            self.stage_clear_timer -= 1
            if self.stage_clear_timer == 0:
                self.reset_stage()
            return

        old_x = self.player.x
        old_y = self.player.y

        # キーボードとタッチ入力の処理
        dx = dy = 0
        if pyxel.btn(pyxel.KEY_LEFT):
            dx = -1
        elif pyxel.btn(pyxel.KEY_RIGHT):
            dx = 1
        if pyxel.btn(pyxel.KEY_UP):
            dy = -1
        elif pyxel.btn(pyxel.KEY_DOWN):
            dy = 1

        # タッチ入力の処理
        if dx == 0 and dy == 0:  # キーボード入力がない場合のみタッチ操作を処理
            dx, dy = self.touch_controller.update()

        dx, dy = self.player.update(dx, dy)
        
        if self.can_move_to(self.player.x + dx, self.player.y + dy):
            self.player.x += dx
            self.player.y += dy
        else:
            if self.player.current_speed >= self.player.powerd_speed:
                self.wall_flash_timer = 5
                self.create_spark_effect(self.player.x, self.player.y, self.player.current_speed)
                if self.player.kill_boost_timer <= 0:
                    self.player.wall_hits += 1
                bounce_x = -dx * self.player.WALL_BOUNCE if dx != 0 else 0
                bounce_y = -dy * self.player.WALL_BOUNCE if dy != 0 else 0
                if self.can_move_to(self.player.x + bounce_x, self.player.y + bounce_y):
                    self.player.x += bounce_x
                    self.player.y += bounce_y
                if (self.player.wall_hits >= self.player.MAX_WALL_HITS and 
                    self.player.kill_boost_timer <= 0):
                    self.player.reset_power_state()

        collision_occurred = False
        remaining_enemies = []

        for enemy in self.enemies:
            enemy.update(self.can_move_to)
            if self.check_collision(self.player.x, self.player.y, enemy.x, enemy.y):
                if self.player.current_speed >= self.player.powerd_speed:
                    self.create_death_effect(enemy.x, enemy.y, 12)
                    self.player.kill_boost_timer = self.player.KILL_BOOST_DURATION
                    continue
                else:
                    collision_occurred = True
                    enemy.direction = random.randint(0, 3)
                    total_enemies = len(self.enemies)
                    if total_enemies < self.max_enemies and enemy.multiply_cooldown == 0:
                        for _ in range(2):
                            if total_enemies + _ < self.max_enemies:
                                new_x, new_y = find_valid_position(self.map_data, self.tile_size)
                                new_enemy = Enemy(new_x, new_y)
                                remaining_enemies.append(new_enemy)
                        enemy.multiply_cooldown = enemy.MULTIPLY_COOLDOWN
                        self.wall_green_timer = 21  # 約0.7秒（30FPS × 0.7）
            remaining_enemies.append(enemy)

        updated_particles = []
        for particle in self.particles:
            killed_enemies = particle.check_enemy_collision(remaining_enemies)
            for killed_enemy in killed_enemies:
                if killed_enemy in remaining_enemies:
                    remaining_enemies.remove(killed_enemy)
                    self.create_death_effect(killed_enemy.x, killed_enemy.y, 12)
            if particle.update(self.can_move_to):
                updated_particles.append(particle)
        self.particles = updated_particles

        if collision_occurred and not self.player.current_speed >= self.player.powerd_speed:
            self.player.x = old_x
            self.player.y = old_y
            self.player.current_speed = self.player.base_speed

        self.enemies = remaining_enemies

        self.proliferation_timer += 1
        if self.proliferation_timer >= self.proliferation_interval:
            self.proliferation_timer = 0
            new_enemies = []
            for enemy in self.enemies:
                if (enemy.multiply_cooldown == 0 and 
                    random.random() < self.proliferation_probability):
                    for _ in range(self.proliferation_count):
                        if len(self.enemies) + len(new_enemies) < self.max_enemies:
                            new_enemies.append(Enemy(enemy.x, enemy.y))
                    enemy.multiply_cooldown = enemy.MULTIPLY_COOLDOWN
            self.enemies.extend(new_enemies)

        if not self.enemies:
            self.stage_clear_timer = 60

    def draw(self):
        pyxel.cls(0)
        
        # 迷路の描画
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    if self.wall_green_timer > 0:
                        color = 11  # 緑色
                    else:
                        color = 10 if self.wall_flash_timer > 0 else 7
                    pyxel.rect(x * self.tile_size, y * self.tile_size,
                             self.tile_size, self.tile_size, color)
        
        if self.wall_flash_timer > 0:
            self.wall_flash_timer -= 1
        if self.wall_green_timer > 0:
            self.wall_green_timer -= 1

        # エネミーとパーティクルの描画
        for enemy in self.enemies:
            enemy.draw()

        for particle in self.particles:
            particle.draw()

        # UI情報の描画
        speed_ratio = self.player.current_speed / self.player.base_speed
        speed_text = f"SPEED: x{speed_ratio:.2f}"
        enemy_text = f"ENEMY: {len(self.enemies)}/{self.max_enemies}"
        
        x = self.screen_width // 2 - len(speed_text) * 2
        pyxel.text(x, 4, speed_text, 0)
        
        x = self.screen_width - len(enemy_text) * 4 - 4
        pyxel.text(x, 4, enemy_text, 0)
        
        # プレイヤーの描画
        self.player.draw()

        # ステージクリア表示
        if self.stage_clear_timer > 0:
            text = "NEXT STAGE"
            x = self.screen_width // 2 - len(text) * 2
            y = self.screen_height // 2
            pyxel.text(x, y, text, 0)

App()
