import subprocess
import time
import psutil
import signal
from poke_env.player import Player
import asyncio

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
        time.sleep(10)  # Espera fija más larga para mayor fiabilidad
        print("Servidor Showdown debería estar listo en http://localhost:8000")

    def iniciar_calculadora_server(self):
        if not self._esta_proceso_activo("servidor.js"):
            print("Iniciando servidor de la calculadora en puerto 3000...")
            self.calculadora_proc = subprocess.Popen(
                ["node", "servidor.js"],
                cwd="calculadora",
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True
            )
            time.sleep(2)
        else:
            print("Servidor de la calculadora ya está activo.")

    def _esta_proceso_activo(self, nombre_script):
        for proc in psutil.process_iter(attrs=["cmdline"]):
            try:
                cmdline = proc.info.get("cmdline")
                if cmdline and any(nombre_script in str(arg) for arg in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        return False

    def detener_procesos(self):
        if self.showdown_proc:
            print("Deteniendo servidor de Pokémon Showdown...")
            try:
                self.showdown_proc.send_signal(signal.CTRL_BREAK_EVENT)
                self.showdown_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("El proceso Showdown no respondió, matándolo...")
                self.showdown_proc.kill()
        if self.calculadora_proc:
            print("Deteniendo servidor de la calculadora...")
            try:
                self.calculadora_proc.send_signal(signal.CTRL_BREAK_EVENT)
                self.calculadora_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("La calculadora no respondió, matándola...")
                self.calculadora_proc.kill()

    def print_local_showdown_link(self):
        url = "http://localhost:8000/"
        texto = "Click aquí para abrir el servidor local de Showdown"
        print(f"\033]8;;{url}\033\\{texto}\033]8;;\033\\")
        

    async def jugar(self, num_batallas=5):
        try:
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
        finally:
            await asyncio.sleep(1)
