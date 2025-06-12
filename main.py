import argparse
import asyncio
from poke_env import AccountConfiguration, ShowdownServerConfiguration

from entorno.JugarOnline import JugarOnline
from entorno.JugarLocal import JugarLocal
from bots.playerAtaca import playerAtaca
from bots.playerDefiende import playerDefiende
from poke_env.player.random_player import RandomPlayer
from bots.maxDmgPlayer import MaxDamagePlayer

# Diccionario para instanciar los bots por nombre
BOT_OPCIONES = {
    "random": RandomPlayer,
    "maxdmg": MaxDamagePlayer,
    "ataca": playerAtaca,
    "defiende": playerDefiende,
}
def parse_args():
    parser = argparse.ArgumentParser(description="Bot Pokémon Showdown - TFG")
    parser.add_argument("--modo", choices=["local", "online"], default="local", help="Modo de juego")
    parser.add_argument("--tipo_online", choices=["ladder", "desafio"], default="ladder", help="Tipo de juego online")
    parser.add_argument("--batallas", type=int, default=1, help="Número de batallas a jugar")
    parser.add_argument("--bot1", choices=BOT_OPCIONES.keys(), default="random", help="Bot jugador 1")
    parser.add_argument("--bot2", choices=BOT_OPCIONES.keys(), default="random", help="Bot jugador 2 (solo local)")
    return parser.parse_args()

async def main():
    args = parse_args()

    if args.modo == "online":
        from config import USERNAME, PASSWORD

        player_config = AccountConfiguration(USERNAME, PASSWORD)
        server_config = ShowdownServerConfiguration # Servidor oficial

        bot1 = BOT_OPCIONES[args.bot1](
            account_configuration=player_config,
            server_configuration=server_config,
            start_timer_on_battle_start=True
        )

        juego = JugarOnline(bot1, tipo_online=args.tipo_online)
        await juego.jugar(num_batallas=args.batallas)

    else:  # modo local
        bot1 = BOT_OPCIONES[args.bot1](battle_format="gen9randombattle")
        bot2 = BOT_OPCIONES[args.bot2](battle_format="gen9randombattle")
        juego = JugarLocal(bot1, bot2)
        await juego.jugar(num_batallas=args.batallas)

if __name__ == "__main__":
    asyncio.run(main())
