from poke_env.player import RandomPlayer  # Jugadores que eligen movimientos aleatorios
from poke_env.player import Player

import asyncio

class MaxDamagePlayer(Player):
    def choose_move(self, battle):
        # Chooses a move with the highest base power when possible
        if battle.available_moves:
            # Iterating over available moves to find the one with the highest base power
            best_move = max(battle.available_moves, key=lambda move: move.base_power)
            # Creating an order for the selected move
            try:
                return self.create_order(best_move)
            except:
                return self.choose_random_move(battle)

        else:
            # If no attacking move is available, perform a random switch
            # This involves choosing a random move, which could be a switch or another available action
            return self.choose_random_move(battle)
