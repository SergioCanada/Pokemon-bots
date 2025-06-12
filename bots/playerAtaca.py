from poke_env.player.player import Player
from poke_env.player.battle_order import BattleOrder
from calculadora.converterCalculadora import calcular_dmg_con_poke_env
import asyncio

class playerAtaca(Player):
    
    async def choose_move(self, battle):
        try:
            print(" ")
            await asyncio.sleep(0.2)
            if not battle.available_moves and not battle.force_switch:
                print(f"Esperamos a que cargue todo.")
                await asyncio.sleep(0.2)

            if battle.force_switch:
                print("Cambio requerido. Seleccionando un Pokémon que más daño vaya a hacer.")
                try:
                    best_switch = await self.mejor_cambio(battle)
                    if best_switch:
                        print(f"Se elige a {best_switch.species} para el cambio forzado.")
                        return self.create_order(best_switch)
                except Exception as e:
                    print(f"[FALLO1] create_order falló para cambio estratégico: {e}")

                print("No se pudo seleccionar el mejor cambio. Selección aleatoria.")
                return self.choose_random_move(battle)


            best_action = None
            best_turns_to_ko = float('inf')

            for poke in battle.team.values():
                if poke.fainted:
                    continue

                move, turns_to_ko = await self.mejor_move_poke(battle, poke)

                if move and turns_to_ko < best_turns_to_ko:
                    best_turns_to_ko = turns_to_ko
                    best_action = (poke, move)

            if best_action:
                chosen_poke, chosen_move = best_action
                print(f"Mejor acción: {chosen_poke.species} usa {chosen_move.id} en {best_turns_to_ko} turnos (tiene {chosen_poke.item})")

                if chosen_poke.active:
                    print(f"[acción] {chosen_poke.species} usa {chosen_move.id}")
                    try:
                        return self.create_order(chosen_move)
                    except Exception as e:
                        print(f"[FALLO] create_order falló para usar {chosen_move.id}: {e}")
                        return self.choose_random_move(battle)
                else:
                    if chosen_poke in battle.available_switches:
                        print(f"[acción] Se cambia a {chosen_poke.species}")
                        try:
                            return self.create_order(chosen_poke)
                        except Exception as e:
                            print(f"[FALLO] create_order falló para cambio a {chosen_poke.species}: {e}")
                            return self.choose_random_move(battle)
                    else:
                        print("No se puede cambiar")
                        return self.choose_random_move(battle)

            print("Error (o no tiene moves que hagan daño)")
            return self.choose_random_move(battle)

        except AssertionError as ae:
            print(f"[ASSERTION FALLO] Error crítico durante choose_move: {ae}")
            return self.choose_random_move(battle)

        except Exception as e:
            print(f"[FALLO] choose_move general falló: {e}")
            return self.choose_random_move(battle)

    async def mejor_move_poke(self, battle, poke):
        best_move = None
        best_turns = float('inf')

        if poke.active: 
            moves_to_check = battle.available_moves
        else: 
            moves_to_check = [move for move in poke.moves.values() if move and move.current_pp > 0]

        if not moves_to_check:
            print(f"[WARN] {poke.species} has no usable moves.")
            return None, float('inf')

        for move in moves_to_check:
            data = await calcular_dmg_con_poke_env(
                battle=battle,
                attacker=poke,
                defender=battle.opponent_active_pokemon,
                move=move
            )
            turnos = data.get("turnsToKO", -1)

            print(f"Si {poke.species} usa {move.id}: {turnos} turnos")

            if turnos != -1:
                if not poke.active:
                    turnos += 1

                score = self.puntuacion_extra(move)
                if turnos < best_turns:
                    best_turns = turnos
                    best_move = move
                    best_move_score = score
                elif turnos == best_turns and (not best_move or score > best_move_score):
                    best_move = move
                    best_move_score = score

        return best_move, best_turns
    
    def puntuacion_extra(self, move):

        score = 0

        if move.priority > 0:
            score += 5

        # buffos o debufos
        if move.self_boost:
            total_boosts = sum(move.self_boost.values())
            score += total_boosts

        # +2: Estado (burn, para, etc.)
        if move.status:
            score += 2

        # +2: Cambio de clima o terreno
        if move.weather or move.terrain:
            score += 2

        # +2: Movimiento de curación decente
        if move.heal and move.heal.get("fraction", 0) >= 0.25:
            score += 2

        # +1 o +2: Recoil, puede implicar mucha potencia
        if move.recoil:
            if move.recoil > 0.3:
                score -=1
            else:
                score += 1

        # +2: Hazards (Stealth Rock, Spikes, etc.)
        if move.side_condition:
            score += 2

        # +1: Movimientos que protegen o bloquean (Protect, etc.)
        if move.volatile_status in ["protect", "endure", "substitute"]:
            score += 1

        # +1: Trampas o bloqueo (Wrap, Infestation, etc.)
        if move.volatile_status in ["partiallytrapped", "meanlook", "infestation"]:
            score += 1

        return score
    
    async def mejor_cambio(self, battle):
        move = None
        turns_to_ko = float('inf')
        best_turns_to_ko = float('inf')
        best_action = None, None
        for poke in battle.team.values():
            if poke.fainted:
                continue

            move, turns_to_ko = await self.mejor_move_poke(battle, poke)

            if move and turns_to_ko < best_turns_to_ko:
                best_turns_to_ko = turns_to_ko
                best_action = (poke, move)


        chosen_poke, chosen_move = best_action
        return chosen_poke if best_action else None
