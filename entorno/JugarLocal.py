import subprocess
import time
import psutil
import socket
import signal
from poke_env.player import Player


class JugarLocal:
    def __init__(self, jugador1: Player, jugador2: Player):
        self.jugador1 = jugador1
        self.jugador2 = jugador2
        self.showdown_proc = None
        self.calculadora_proc = None

    def liberar_puerto(self, port):
        for proc in psutil.process_iter(attrs=["pid", "name", "net_connections"]):
            try:
                for conn in proc.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        print(f"Matando proceso en puerto {port}: PID {proc.pid} ({proc.name()})")
                        proc.kill()
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def esperar_puerto(self, host, port, timeout=30):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (ConnectionRefusedError, OSError):
                time.sleep(0.5)
        return False

    def iniciar_showdown_server(self):
        self.liberar_puerto(8000)

        print("Iniciando servidor de Pokémon Showdown en local...")
        self.showdown_proc = subprocess.Popen(
            ["node", "pokemon-showdown", "start", "--no-security"],
            cwd="pokemon-showdown",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
        print("Esperando que Showdown arranque...")
        if self.esperar_puerto('127.0.0.1', 8000, timeout=60):
            print("Servidor Showdown listo y puerto 8000 activo.")
            time.sleep(3)
        else:
            raise RuntimeError("No se pudo conectar al puerto 8000 de Showdown")

    def iniciar_calculadora_server(self):
        self.liberar_puerto(3000)

        print("Iniciando servidor de la calculadora...")
        self.calculadora_proc = subprocess.Popen(
            ["node", "servidor.js"],
            cwd="calculadora",
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=True
        )
        print("Esperando que la calculadora arranque...")
        if self.esperar_puerto('127.0.0.1', 3000, timeout=30):
            print("Servidor de la calculadora listo y puerto 3000 activo.")
            time.sleep(1)
        else:
            raise RuntimeError("No se pudo conectar al puerto 3000 de la calculadora")

    def detener_procesos(self):
        try:
            if self.showdown_proc:
                print("Deteniendo servidor de Pokémon Showdown...")
                self.showdown_proc.send_signal(signal.CTRL_BREAK_EVENT)
                try:
                    self.showdown_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("El proceso Showdown no respondió a la señal, matándolo forzadamente...")
                    self.showdown_proc.kill()
        except Exception as e:
            print(f"[WARN] Error al detener Showdown: {e}")

        try:
            if self.calculadora_proc:
                print("Deteniendo servidor de la calculadora...")
                self.calculadora_proc.send_signal(signal.CTRL_BREAK_EVENT)
                try:
                    self.calculadora_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print("El proceso calculadora no respondió a la señal, matándolo forzadamente...")
                    self.calculadora_proc.kill()
        except Exception as e:
            print(f"[WARN] Error al detener calculadora: {e}")

    def print_local_showdown_link(self):
        url = "http://localhost:8000/"
        texto = "Click aquí para abrir el servidor local de Showdown (http://localhost:8000)"
        print(f"\033]8;;{url}\033\\{texto}\033]8;;\033\\")


    async def jugar(self, num_batallas=5):
        self.iniciar_showdown_server()
        self.iniciar_calculadora_server()
        self.print_local_showdown_link()

        print(f"Iniciando {num_batallas} batallas locales entre {self.jugador1.__class__.__name__} y {self.jugador2.__class__.__name__}...")
        for i in range(num_batallas):
            print(f"\nBatalla {i + 1}...")
            await self.jugador1.battle_against(self.jugador2, n_battles=1)

        victorias1 = self.jugador1.n_won_battles
        victorias2 = self.jugador2.n_won_battles
        empates = num_batallas - victorias1 - victorias2

        print("\n--- RESUMEN DE BATALLAS ---")
        print(f"{self.jugador1.__class__.__name__}: {victorias1} victoria(s)")
        print(f"{self.jugador2.__class__.__name__}: {victorias2} victoria(s)")
        print(f"Empates o sin decidir: {empates}")
        print("----------------------------")


