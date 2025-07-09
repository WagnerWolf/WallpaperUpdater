# server.py
import http.server
import socketserver
import os
import json
import time
import threading
import sys
import hashlib
from PIL import Image
from pystray import Icon, MenuItem as item

PORT = 8000
DIRECTORY = "wallpapers"
IMAGE_NAME = "wallpaper.jpg"

def calculate_file_md5(filepath):
    """Calcula o hash MD5 de um arquivo."""
    hash_md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Erro ao calcular MD5 para {filepath}: {e}")
        return None

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            image_path = os.path.join(DIRECTORY, IMAGE_NAME)
            response_data = {
                "modified_time": None,
                "timestamp": None,
                "md5_hash": None # Novo campo para o hash MD5
            }

            if os.path.exists(image_path):
                modified_timestamp = os.path.getmtime(image_path)
                response_data["modified_time"] = time.ctime(modified_timestamp)
                response_data["timestamp"] = modified_timestamp
                response_data["md5_hash"] = calculate_file_md5(image_path) # Calcula e adiciona o hash

            self.wfile.write(json.dumps(response_data).encode('utf-8'))
        else:
            super().do_GET()

def run_server():
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"Servidor Python servindo em http://0.0.0.0:{PORT}")
        print(f"Basta colocar sua imagem de papel de parede '{IMAGE_NAME}' na pasta '{DIRECTORY}'")
        print(f"Verificar status da imagem em http://0.0.0.0:{PORT}/status")
        httpd.serve_forever()

def create_image_for_icon():
    width = 64
    height = 64
    color = (0, 150, 0)
    image = Image.new('RGB', (width, height), color)
    return image

def exit_program(icon):
    icon.stop()
    sys.exit(0)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    icon_image = create_image_for_icon()
    menu = (item('Sair', exit_program),)
    icon = Icon("WallpaperServer", icon_image, "Servidor de Papel de Parede", menu)
    icon.run()