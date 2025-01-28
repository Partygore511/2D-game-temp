import socket
import threading
import random
import json
import tkinter as tk

from game_code import *

def receive_messages(client_socket, dictionary, canvas):
    """接收来自服务器的消息"""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                completed = message.split(':')
                
                # 判断是否有玩家退出，假设服务器发送了"quit:{player_id}"这样的消息
                if completed[0] == "quit":
                    player_id = completed[1]
                    if player_id in dictionary:
                        canvas.delete(dictionary[player_id].body)
                        del dictionary[player_id]
                        print(f"玩家 {player_id} 退出，已移除其映射。")
                else:
                    dictionary[completed[0]] = completed[1]
        except (ConnectionRefusedError,
                ConnectionResetError,
                BrokenPipeError,
                TimeoutError,
                OSError,
                socket.error,
                EOFError) as e:
            print("与服务器的连接断开。")
            break
        

def send_messages(client_socket, message):
    try:
        client_socket.send(json.dumps(message).encode('utf-8'))
    except Exception as e:
        print(f"无法发送消息，与服务器断开：{e}")

class PlayerImage:
    def __init__(self, game):
        self.game = game
        self.canvas = game.canvas
        self.master = self.canvas.master
        self.x = 0
        self.y = 0
        self.x_velocity = 0
        self.y_velocity = 0
        self.kb = 2.50

        # 身体
        self.kb_text = self.canvas.create_text(
            self.x, self.y - 25, text=f"KB: {self.kb:.1f}",
            fill="black", font=("Arial", 10))
        self.body = self.canvas.create_rectangle(
            self.x-15, self.y-15, self.x+15, self.y+15, fill='blue')
        self.canvas.tag_lower(self.body)

    def update(self, x, y, x_velocity, y_velocity):
        self.x = x
        self.y = y
        self.x_velocity = x_velocity
        self.y_velocity = y_velocity
        self.x += self.x_velocity
        self.y += self.y_velocity

        self.canvas.coords(self.body, self.x-15, self.y-15, self.x+15, self.y+15)

    def __del__(self):
        self.canvas.delete(self.body, self.kb_text)
        del self


class BulletImage(Bullet):
    def update(self, terrain, x=0, y=0, xv=0, yv=0):
        self.x = x
        self.y = y
        self.x_velocity = xv
        self.y_velocity = yv
        
        super().update(terrain)


class BulletSender:
    def __init__(self, game):
        self.game = game


class PlayerOnConnection(Player):
    def __init__(self, game, x, y):
        self.bullet_id = 0
        print(self.bullet_id)
        super().__init__(game, x, y)
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
        # 常数可修改
        bullet = BulletOnConnection(
            self.canvas, self.x, self.y,
            7*x_distance/whole_distance, 7*y_distance/whole_distance,
            self, None, 'yellow', self.bullet_id, self.client)

        message = [[float(f'{decimal:.2f}') for decimal in (
                    bullet.x, bullet.y,
                    bullet.x_velocity, bullet.y_velocity)]+[True]+[self.bullet_id]]

        self.bullet_id += 1

        send_messages(self.client, message)

class BulletOnConnection(Bullet):
    def __init__(self, canvas, x, y, x_velocity, y_velocity, player, special, color, ID, client):
        super().__init__(canvas, x, y, x_velocity, y_velocity, player, special, color)
        self.client = client


class MultiPlayerGame(Game):
    def __init__(self, canvas):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = "0.0.0.0"  # input("请输入服务器地址（默认localhost）: ") or "localhost"
        port = 9999  # input("请输入服务器端口（默认9999）: ")
        self.server_port = 9999  # (int(port if port.isdecimal() else 9999))
        self.players_image = {}
        self.images = {}
        self.bullet_images = {}
        self.bullet_sender = BulletSender(self)

        try:
            self.client.connect((self.server_address, self.server_port))
            print("成功连接到服务器！")
        except Exception as e:
            print(e, "无法连接到服务器。")
            raise SystemExit(0)
        # 输入或生成客户端 ID
        self.client_id = str(random.randint(100000, 999999))
        # (input("请输入你的客户端ID（留空将随机生成）: ") or str(random.randint(100000, 999999)))
        print(f"你的客户端ID是: {self.client_id}")
        self.client.send(json.dumps(self.client_id).encode('utf-8'))  # 将 ID 发送给服务器
        super().__init__(canvas)
        
        # 启动接收消息的线程
        self.receive_thread = threading.Thread(target=receive_messages, args=(self.client, self.players_image, self.canvas))
        self.receive_thread.daemon = True  # 设置为守护线程，确保主线程退出时该线程也会退出
        self.receive_thread.start()

    def update(self):
        player = self.players[0]
        player.client = self.client
        self.player_info = [float(f'{decimal:.2f}') for decimal in (
            player.x, player.y,
            player.x_velocity, player.y_velocity)]+[False]+[-1]
        send_messages(self.client, self.player_info)
        #if self.players_image:
        print(self.players_image)
            
        for image in list(self.players_image):  # 使用list()来避免在遍历时修改字典
            if type(self.players_image[image]) == str:
                self.players_image[image] = (
                    self.players_image[image].replace("[", "").replace("]", "")
                    ).split(',')
            x, y, xv, yv = tuple(self.players_image[image][:4])
            b_id = self.players_image[image][5]
            
            if self.players_image[image][4].strip() == 'true':
                if image in self.bullet_images:
                    self.bullet_images[b_id].update(self.terrain, float(x), float(y), float(xv), float(yv))
                else:
                    self.bullet_images[b_id] = BulletImage(
                        self.canvas, float(x), float(y), float(xv), float(yv), 
                        self.bullet_sender, None, 'yellow')
            else:
                if image in self.images:
                    #print(x, y, xv, yv)
                    self.images[image].update(float(x), float(y), float(xv), float(yv))
                else:
                    self.images[image] = PlayerImage(self)
        
        # 移除已退出的玩家
        for image in list(self.players_image):  # 使用list()来避免在遍历时修改字典
            if image not in self.players_image:  # 确保只删除断开连接的玩家
                del self.players_image[image]
                del self.images[image]
                
        super().update()
        

def main():
    root = tk.Tk()
    root.title('️☁️PvP game')
    canvas = tk.Canvas(root, height=600, width=1000, bg="#87ceeb")
    canvas.pack(expand=True, fill="both")
    game = MultiPlayerGame(canvas)
    
    #game = Game(canvas)
    player1 = PlayerOnConnection(game, 150, 150)

    game.setup()
    root.mainloop()

    return root, canvas, game, player1


if __name__ == "__main__":
    root, canvas, game, player1 = main()

