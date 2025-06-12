from poke_env.player import Player
import asyncio
import subprocess
import signal
import time
import psutil
import os

class JugarOnline:
    def __init__(self, jugador: Player, tipo_online: str = "ladder"):
        self.jugador = jugador
        self.tipo_online = tipo_online
        self.elo_inicial = None
        self.elo_final = None
        self.calculadora_proc = None

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

    def detener_calculadora(self):
        if self.calculadora_proc:
            print("Deteniendo servidor de la calculadora...")
            self.calculadora_proc.send_signal(signal.CTRL_BREAK_EVENT)
            self.calculadora_proc.wait(timeout=5)

    def _esta_proceso_activo(self, nombre_script):
        for proc in psutil.process_iter(attrs=["cmdline"]):
            try:
                cmdline = proc.info.get("cmdline")
                if cmdline and any(nombre_script in str(arg) for arg in cmdline):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        return False

    async def jugar(self, num_batallas):
        self.iniciar_calculadora_server()
        await asyncio.sleep(1)  # espera que calculadora arranque

        print(f"Iniciando juego online en {self.tipo_online} con {self.jugador.__class__.__name__}...")

        # Esperar y jugar según tipo
        if self.tipo_online == "ladder":
            await self.jugador.ladder(num_batallas)
        elif self.tipo_online == "desafio":
            print("Esperando desafíos...")
            await self.jugador.accept_challenges(None, n_challenges=num_batallas)
        else:
            raise ValueError(f"Tipo desconocido: {self.tipo_online}")

        # Sacar ELO inicial y final de la primera y última batalla respectivamente
        if self.jugador.battles:
            first_battle = list(self.jugador.battles.values())[0]
            self.elo_inicial = first_battle.rating
        else:
            self.elo_inicial = None
        self.elo_final = self.jugador.rating if hasattr(self.jugador, 'rating') else None

        # Mostrar resumen
        print("\nResultados de las batallas:")
        for battle_id, battle in self.jugador.battles.items():
            opponent = battle.opponent_username
            resultado = battle.won
            if resultado is True:
                estado = "Ganaste"
            elif resultado is False:
                estado = "Perdiste"
            else:
                estado = "Empate o sin resultado claro"
            print(f"- {battle_id}: {estado} contra {opponent}")


        self.detener_calculadora()
