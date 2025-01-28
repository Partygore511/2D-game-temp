import math
import random
import time
import tkinter as tk
import sys
from types import SimpleNamespace

def find_occurrences(s, char, n):
    count = 0
    for i, c in enumerate(s):
        if c == char:
            count += 1
            if count == n:
                return i
    return -1


class Game:
    """创建一个游戏t"""
    def __init__(self, canvas):
        self.canvas = canvas
        self.master = self.canvas.master
        self.update_instance = 25  # 40 fps
        self.players = []
        self.bullets = []

    def setup(self):
        """
        设置游戏
        """
        #为什么不放在__init__里？因为我不知道在哪定义玩家
        #地图也放里面纯粹是懒
        
        # 地图
        self.terrain = (
            ((400, 700), (400, 570), (800, 570), (800, 700)),
            ((0, 470), (0, 520), (300, 520), (300, 470)), 
            ((400, 700), (400, 450), (600, 450), (600, 700)), 
            ((400, 420), (400, 450), (700, 450), (700, 420)),
            ((500, 270), (500, 320), (900, 320), (900, 270)),
            ((200, 420), (200, 520), (300, 520), (300, 420)), 
            )

        self.operations = {}
        
        for num, player in enumerate(self.players):
            # 玩家操作
            self.operations[player] = {
                'w': lambda: player.jump(
                    player.x_velocity*1.5 if 'q' in player.key_pressed else 0, 
                    -45, self.terrain), 
                'a': lambda: player.speed_up(-1, 0), 
                's': lambda: player.jump_charging(0, 0.6, 5.2, self.terrain), 
                'd': lambda: player.speed_up(1, 0), 
                'e': player.refill, 
                'q': lambda: player.dash(9, self.terrain), 
                'space': lambda: self.speed(500), 
                'b': lambda: self.speed(25), 
                }
            if type(player) == Enemy:
                # 敌人操作和颜色
                #player.player = self.players[1 if num == 0 else 0]
                self.canvas.itemconfig(
                    player.body, fill='light blue' if num == 0 else 'dark cyan'
                                       )
                player.player = self.players[-1]

        # 绘制地图
        for blocks in self.terrain:
            self.canvas.create_polygon(*blocks, fill='green')

        # 显示文字
        self.bullet_text = self.canvas.create_text(
            900,
            550,
            text="子弹数: 25",
            fill="black",
            font=("Arial", 12)
        )

        self.death_text = self.canvas.create_text(
            500,
            50,
            text="0:0",
            fill="black",
            font=("Arial", 30)
        )

        self.update()
        
    def update(self):
        # 将玩家的行为映射到游戏
        for player in self.players:
            #if type(player) == Player:
                #enemy = Enemy(game, 150, 150)
                #enemy.player = player
                #self.players.append(enemy)
            for key in player.key_pressed:
                if key in self.operations[player]:
                    self.operations[player][key]()

            # 更新玩家行为
            player.update(self.terrain)

            # 修改显示文字
            self.canvas.itemconfig(
                self.bullet_text, text=f"子弹数: {player.bullet_num}")
        enemy_deaths = player_deaths = 0
        for player in self.players:
            if type(player) == Enemy:
                enemy_deaths += player.death
            else:
                player_deaths += player.death
        self.canvas.itemconfig(
            self.death_text,
            text=f"{enemy_deaths}:{player_deaths}")
        
        # 更新子弹行为
        for bullet in self.bullets:
            bullet.update(self.terrain)

        # 递归
        self.master.after(self.update_instance, self.update)
        
    def speed(self, update_instance):
        """设置游戏运行速度"""
        self.update_instance = update_instance

        
class Player:
    """创建玩家对象"""
    def __init__(self, game, x, y):
        # 基本变量
        self.game = game
        game.players.append(self)
        self.canvas = game.canvas
        self.master = self.canvas.master
        self.x = x
        self.y = y
        self.x_velocity = 0
        self.y_velocity = 0

        self.death = 0
        self.fall_timer = 0
        self.dash_cd = 0
        self.jump_charge = 0
        self.fall = False
        self.is_filling = False
        self.dizzed = False
        
        # 玩家操作变量，一般可做修改
        self.bullet_num = 25
        self.kb = 2.50
        self.max_speed = 45
        self.gravity_acceleration = 1

        # kb词条
        self.kb_text = self.canvas.create_text(
            self.x, self.y - 25, text=f"KB: {self.kb:.1f}",
            fill="black", font=("Arial", 10))

        # 开始按键事件
        self.key_pressed = set()
        self.master.bind('<Key>', self.press)
        self.master.bind('<KeyRelease>', self.release)
        self.master.bind('<Button-1>', self.shoot)

        # 绘制玩家身体
        self.body = self.canvas.create_rectangle(
            x-15, y-15, x+15, y+15, fill='indigo')

    def update(self, terrain):
        """更新玩家行为"""
        # 红子弹效果
        if self.fall:
            self.fall_timer += 1
            if self.fall_timer % 10 == 0:
                self.kb += 0.2
        if self.fall_timer % 40 == 0:
            self.fall = False

        # 限制速度
        self.x_velocity = max(self.x_velocity, -self.max_speed)
        self.x_velocity = min(self.x_velocity, self.max_speed)
        self.y_velocity = max(self.y_velocity, -self.max_speed)
        self.y_velocity = min(self.y_velocity, self.max_speed)

        # 判定子弹与击中行为
        for bullet in self.game.bullets:
            if type(bullet.player) != type(self):
                if any(bullet.determine_collide(((
                    (self.x-15, self.y+15),
                    (self.x+15, self.y-15),
                    (self.x-15, self.y-15),
                    (self.x+15, self.y+15)
                    ),))):
                    if bullet.special == 'fall': # 红子弹
                        self.fall = True
                    else: # 普通子弹
                        self.x_velocity += self.kb * bullet.x_velocity
                        self.y_velocity += -0.5 * self.kb * abs(self.y - bullet.y)
                    self.kb += 0.2
                    # 删除子弹
                    self.canvas.delete(bullet.body)
                    self.game.bullets.remove(bullet)
                    del bullet

        # 判定与墙的碰撞
        collision = self.determine_collide(terrain)
        rejection = self.determine_collide(terrain, 14, 14) # rejection 用于调整玩家的位置而不抖动
        #if self.fall_timer % 10000 == 0:
        #print(self.y_velocity)
        
        if collision[1] and self.y_velocity > 0:
            self.y_velocity = 0
            if rejection[1]:
                self.y -= 1
        if collision[0] and self.y_velocity < 0:
            self.y_velocity = 0
            if self.y_velocity > 5:
                self.dizzed = True
        if collision[2] and self.x_velocity < 0:
            self.x_velocity = 0
            if rejection[1]:
                self.x += 1
        if collision[3] and self.x_velocity > 0:
            self.x_velocity = 0
            if rejection[1]:
                self.x -= 1
            
        if collision[0]: # 防止卡墙
            self.y += 2
            
        # 更新速度，重力和阻力。常数可修改
        self.x += self.x_velocity
        self.y += self.y_velocity

        self.x_velocity *= 0.75
        self.y_velocity *= 0.75

        self.jump_charge *= 0.80

        self.y_velocity += self.gravity_acceleration

        # 判定死亡和重生
        if not (-100 <= self.y <= 615 and -115 <= self.x <= 1115):
            self.y = random.randint(100, 400)
            self.x = random.randint(100, 900)
            
            self.death += 1

            self.kb = 2.50

            # 防止玩家重生后迅速死亡（是的，我遇到过）
            self.x_velocity = self.y_velocity = 0

        # 冲刺冷却
        if self.dash_cd > 0:
            self.dash_cd -= 0.2

        # 更新kb条和位置
        self.canvas.coords(self.kb_text, self.x, self.y - 25)
        self.canvas.itemconfig(self.kb_text, text=f"KB: {self.kb:.1f}")

        mouse_x, mouse_y = self.master.winfo_pointerxy()

        mouse_x -= int(self.master.geometry().split('+')[1])
        mouse_y -= int(self.master.geometry().split('+')[2])
        
        self.canvas.coords(
            self.body, self.x-15, self.y-15,
            self.x+15, self.y+15)
        
    def press(self, event):
        """判定按键按下事件"""
        self.key_pressed.add(event.keysym)
        
    def release(self, event):
        """判定按键松开事件"""
        self.key_pressed.discard(event.keysym)

    def shoot(self, event):
        """发射子弹"""
        # 判定子弹不足
        if self.bullet_num < 1:
            self.refill()
            return
        
        self.bullet_num -= 1
        x_distance = event.x-self.x
        y_distance = event.y-self.y
        if x_distance == 0 or y_distance == 0:
            return
        whole_distance = math.sqrt(x_distance ** 2 + y_distance ** 2)
        # 随机子弹类型，仅测试
        #special = random.choice([(None, 'yellow'), ('fall', 'red')])
        # 常数可修改
        Bullet(
            self.canvas, self.x, self.y,
            7*x_distance/whole_distance, 7*y_distance/whole_distance,
            self, None, 'yellow')

    def refill(self):
        def fill():
            self.bullet_num = 25
            self.is_filling = False
        # 阻止多次装填
        if not self.is_filling:
            # 防止装填后继续射击
            self.bullet_num = 0
            self.is_filling = True
            self.master.after(self.game.update_instance*80, fill)

    def determine_collide(self, terrain, sizex=15, sizey=15):
        """判定两个矩形是否碰撞"""
        # 计算玩家的四个边界点
        bottom = (self.x, self.y + sizey)   # 底部中心点
        top = (self.x, self.y - sizey)      # 顶部中心点
        left = (self.x - sizex, self.y)     # 左侧中心点
        right = (self.x + sizex, self.y)    # 右侧中心点

        collisions = {
            'bottom': False,
            'top': False,
            'left': False,
            'right': False
        }

        # 遍历 terrain 中的每个 block（每个 block 是一个包含四个点的元组）
        for block in terrain:
            # 计算 block 的边界
            min_x = min(point[0] for point in block)
            max_x = max(point[0] for point in block)
            min_y = min(point[1] for point in block)
            max_y = max(point[1] for point in block)

            # 检测底部碰撞
            if min_x <= bottom[0] <= max_x and min_y <= bottom[1] <= max_y:
                collisions['bottom'] = True
            # 检测顶部碰撞
            if min_x <= top[0] <= max_x and min_y <= top[1] <= max_y:
                collisions['top'] = True
            # 检测左侧碰撞
            if min_x <= left[0] <= max_x and min_y <= left[1] <= max_y:
                collisions['left'] = True
            # 检测右侧碰撞
            if min_x <= right[0] <= max_x and min_y <= right[1] <= max_y:
                collisions['right'] = True

        # 返回四个方向的碰撞状态
        return (collisions['top'], collisions['bottom'], collisions['left'], collisions['right'])

    # 快捷函数
    def move(self, x, y):
        """移动一段距离"""
        self.move_to(self.x+x, self.y+y)
        
    def move_to(self, x, y):
        """移动到某个位置"""
        self.x = x
        self.y = y
        
    def speed_up(self, x_velocity, y_velocity):
        """加速"""
        self.set_speed(self.x_velocity+x_velocity, self.y_velocity+y_velocity)
        
    def set_speed(self, x_velocity, y_velocity):
        """直接设置速度"""
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity

    def jump(self, x_velocity, y_velocity, terrain):
        """跳跃"""
        collide = self.determine_collide(terrain, 15+self.x_velocity, 15+self.y_velocity)
        if collide[1] and not collide[0] and not self.dizzed: # 如果踩在地面上且头顶为空气且没有被击晕
            self.speed_up(x_velocity, y_velocity-self.jump_charge)
            self.jump_charge = 0
            return
        
    def jump_charging(self, x_velocity, y_velocity, charge, terrain):
        """下坠和跳跃充能"""
        self.speed_up(x_velocity, y_velocity)
        self.x_velocity *= 0.5
        if self.determine_collide(terrain, 15+self.x_velocity, 15+self.y_velocity)[1]:
            self.jump_charge += charge

    def dash(self, times, terrain):
        """冲刺和蹬墙"""
        if self.dash_cd > 0:
            return
        if self.determine_collide(terrain, 15+self.x_velocity, 15+self.y_velocity)[1]:
            self.x_velocity *= times
            self.dash_cd = 10
        if self.determine_collide(terrain, 15+self.x_velocity, 15+self.y_velocity)[2]:
            self.x_velocity = abs(self.x_velocity*times) + 20
        if self.determine_collide(terrain, 15+self.x_velocity, 15+self.y_velocity)[3]:
            self.x_velocity = -abs(self.x_velocity*times) - 20


class Enemy(Player):
    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.direction = random.choice([-1, 1])  # 随机选择左或右方向
        self.auto_move_counter = 0  # 控制自动移动的计数器
        self.bullet_num = 3
        self.canvas.itemconfig(self.body, fill='yellow')

    def update(self, terrain):
        if not (
            300 <= self.player.x <= 400 or (
                self.player.x > 800
                and self.y > 300 and self.player.y < 300
                and self.y > 300 and self.x > 500 and self.x < 500
                ) or self.player.x > 900):
            # 自动水平移动，模拟简单的敌人行为
            if self.player.x - self.x < 0:  # 每隔一定的帧数改变方向
                self.direction = -1
            else:
                self.direction = 1
        else:
            if self.player.x - self.x < 0:  # 每隔一定的帧数改变方向
                self.direction = 1
            else:
                self.direction = -1

        self.auto_move_counter += 1

        self.direction += (random.random()-0.5)

        # 自动跳跃，如果位于地面上
        if self.determine_collide(terrain)[1]:
            self.jump(self.x_velocity*15, -60, terrain)

        event = SimpleNamespace(x=self.player.x, y=self.player.y)

        if self.auto_move_counter % 20 == 0:
            #self.direction = random.choice([-1, 1])
            self.shoot(event)
            #barrage(self.x, self.y)

        self.bullet_num = 25
        
        # 继续调用父类的 update 方法来处理重力、速度、位移等
        super().update(terrain)

        #if self.bullet_num > 25:
            #self.bullet_num = 25
        
        # 额外的自动移动
        self.speed_up(self.direction * 0.5, 0)  # 控制敌人自动水平移动的速度

    def press(self, event):
        pass  # 禁用按键控制


class Bullet:
    def __init__(self, canvas, x, y, x_velocity, y_velocity, player, special, color):
        # 基本变量，加入游戏和绘制子弹
        self.x = x
        self.y = y
        self.canvas = canvas
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.player = player
        self.game = player.game
        self.special = special
        self.color = color

        self.game.bullets.append(self)

        self.body = canvas.create_rectangle(self.x-5, self.y-5, self.x+5, self.y+5, fill=color)

    def update(self, terrain):
        self.x += self.x_velocity
        self.y += self.y_velocity

        # 是否飞出屏幕外或撞墙
        if any(self.determine_collide(terrain)) or not (
            0 < self.x < self.canvas.winfo_width() and 0 < self.y < self.canvas.winfo_height()):
            self.canvas.delete(self.body)
            self.game.bullets.remove(self)
            del self
            return

        self.canvas.coords(self.body, self.x-5, self.y-5, self.x+5, self.y+5)
        
    def determine_collide(self, terrain):
        # 计算子弹的四个边界点
        bottom = (self.x, self.y + 5)   # 底部中心点
        top = (self.x, self.y - 5)      # 顶部中心点
        left = (self.x - 5, self.y)     # 左侧中心点
        right = (self.x + 5, self.y)    # 右侧中心点

        collisions = {
            'bottom': False,
            'top': False,
            'left': False,
            'right': False
        }
    
        # 遍历 terrain 中的每个 block（每个 block 是一个包含四个点的元组）
        for block in terrain:
            # 计算 block 的边界
            min_x = min(point[0] for point in block)
            max_x = max(point[0] for point in block)
            min_y = min(point[1] for point in block)
            max_y = max(point[1] for point in block)

            # 检测底部碰撞
            if min_x <= bottom[0] <= max_x and min_y <= bottom[1] <= max_y:
                collisions['bottom'] = True
            # 检测顶部碰撞
            if min_x <= top[0] <= max_x and min_y <= top[1] <= max_y:
                collisions['top'] = True
            # 检测左侧碰撞
            if min_x <= left[0] <= max_x and min_y <= left[1] <= max_y:
                collisions['left'] = True
            # 检测右侧碰撞
            if min_x <= right[0] <= max_x and min_y <= right[1] <= max_y:
                collisions['right'] = True

        # 返回四个方向的碰撞状态
        return (collisions['top'], collisions['bottom'], collisions['left'], collisions['right'])

    
class test:
    def __init__(self, game):
        self.game = game

def barrage(x, y):
    bullet = Bullet(canvas, x, y, -5, 0, test, None, 'yellow')
    #root.after(500, lambda: Bullet(canvas, x, y, 5, 0, test, None, 'yellow'))
    root.after(250, lambda: barrage(x, y))

def start_game():
    root = tk.Tk()
    root.title('️☁️PvP game')
    #root.attributes('-fullscreen', True)
    canvas = tk.Canvas(root, height=600, width=1000, bg="#87ceeb")
    canvas.pack(expand=True, fill="both")
    
    game = Game(canvas)

    test1 = test(game)

    enemy = []
    
    for i in range(10):
        enemy.append(Enemy(game, 150, 150))

    player1 = Player(game, 150, 150)
        
    #player2 = Player(game, 400, 150)

    #barrage(999, 500)

    game.setup()

    bullet = Bullet(canvas, 0, 0, 5, 5, test1, None, 'yellow')
    
    root.mainloop()

    return root, canvas, enemy, player1, game
if __name__ == '__main__':
    root, canvas, enemy, player, game = start_game()

