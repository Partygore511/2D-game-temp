import socket
import threading

clients = {}  # 存储已连接的客户端及其 ID

def handle_client(client_socket, client_address):
    """处理单个客户端的通信"""
    # 接收客户端的 ID
    client_id = client_socket.recv(1024).decode('utf-8')
    #print(f"客户端 {client_address} 连接成功，ID: {client_id}")
    clients[client_socket] = client_id
    
    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            print(f"来自 {client_id} 的消息: {message}")
            broadcast(f"{client_id}: {message}", client_socket)
    except (ConnectionRefusedError,
            ConnectionResetError,
            BrokenPipeError,
            TimeoutError,
            OSError,
            socket.error,
            EOFError) as e:
        print(f"客户端 {client_id} ({client_address}) 断开连接:{e}")
    except Exception as e:
        print(e)
        raise SystemExit(0)
    
    # 客户端断开时，广播退出信息
    broadcast(f"quit:{client_id}", client_socket)
    
    # 从客户端列表中删除该客户端
    del clients[client_socket]
    client_socket.close()

def broadcast(message, sender_socket):
    """将消息转发给其他客户端"""
    for client in list(clients):
        if client != sender_socket:
            try:
                client.send(message.encode('utf-8'))
                print(f"广播的消息: {message}")
            except:
                del clients[client]  # 删除无法发送的客户端
                client.close()  # 关闭断开的连接

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 9999))
    server.listen(5)
    print("服务器启动，等待连接...")
    
    while True:
        client_socket, client_address = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    main()
