# wallpaper_updater.py
import os
import requests
import ctypes
import winreg
import time
import threading
import sys
import hashlib 
from PIL import Image
from pystray import Icon, MenuItem as item

# --- Configurações ---
SERVER_IP = "192.168.1.24"
SERVER_PORT = 8000
IMAGE_NAME = "/wallpaper.jpg" 
WALLPAPER_STYLE_STRETCH = "2"
CHECK_INTERVAL_MINUTES = 15

# Variável global para armazenar o último hash MD5 conhecido
LAST_KNOWN_MD5_HASH = None

def create_image():
    width = 64
    height = 64
    color = (100, 100, 100)
    image = Image.new('RGB', (width, height), color)
    return image

def set_wallpaper(image_path, style):
    SPI_SETDESKWALLPAPER = 0x0014
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style)
        winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Erro ao definir estilo no registro: {e}")

    image_path_w = str(image_path)
    success = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        image_path_w,
        SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
    )
    return success

def update_wallpaper_if_changed():
    """
    Verifica se a imagem no servidor mudou (usando hash MD5) e atualiza o papel de parede.
    """
    global LAST_KNOWN_MD5_HASH
    status_url = f"http://{SERVER_IP}:{SERVER_PORT}/status"
    image_url = f"http://{SERVER_IP}:{SERVER_PORT}{IMAGE_NAME}"

    download_dir = os.environ.get('TEMP')
    if not download_dir:
        download_dir = os.getcwd()
    download_path = os.path.join(download_dir, "current_wallpaper.jpg")

    try:
        # 1. Obter o status (incluindo hash) do servidor
        response_status = requests.get(status_url, timeout=5)
        response_status.raise_for_status()
        server_status = response_status.json()
        server_md5_hash = server_status.get("md5_hash")

        if server_md5_hash is None:
            print("Não foi possível obter o hash MD5 do servidor ou imagem não encontrada no servidor.")
            return

        # Se esta é a primeira execução, ou se o hash mudou
        if LAST_KNOWN_MD5_HASH is None or server_md5_hash != LAST_KNOWN_MD5_HASH:
            print(f"Alteração detectada! Baixando nova imagem. (Server MD5: {server_md5_hash}, Local MD5: {LAST_KNOWN_MD5_HASH})")

            # 2. Baixar a nova imagem
            response_image = requests.get(image_url, stream=True, timeout=10)
            response_image.raise_for_status()

            with open(download_path, 'wb') as f:
                for chunk in response_image.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 3. Definir o novo papel de parede
            if set_wallpaper(download_path, WALLPAPER_STYLE_STRETCH):
                print("Papel de parede atualizado com sucesso!")
                LAST_KNOWN_MD5_HASH = server_md5_hash # Atualiza o hash local
            else:
                print("Falha ao definir o papel de parede.")
        else:
            print(f"Papel de parede já atualizado. (MD5: {server_md5_hash})")

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ou download: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

def run_update_loop():
    update_wallpaper_if_changed() # Primeira verificação ao iniciar
    while True:
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
        update_wallpaper_if_changed()

def exit_program(icon):
    icon.stop()
    sys.exit(0)

def on_right_click(icon, item):
    if str(item) == "Sair":
        exit_program(icon)
    elif str(item) == "Verificar Agora":
        update_wallpaper_if_changed()

if __name__ == "__main__":
    update_thread = threading.Thread(target=run_update_loop, daemon=True)
    update_thread.start()

    icon_image = create_image()
    menu = (item('Verificar Agora', on_right_click), item('Sair', on_right_click))
    icon = Icon("WallpaperUpdater", icon_image, "Atualizador de Papel de Parede", menu)
    icon.run()