from poke_env.player.player import Player
from poke_env.player.battle_order import BattleOrder
from calculadora.converterCalculadora import calcular_dmg_con_poke_env

from poke_env.data import GenData
import asyncio

import random

class playerDefiende(Player):
    async def choose_move(self, battle):
        try:
            print(" ")
            await asyncio.sleep(0.2)
            if not battle.available_moves and not battle.force_switch:
                print(f" Principio de batalla.")
                await asyncio.sleep(0.2)

            if battle.force_switch:
                print("Cambio requerido. Seleccionando un Pokémon con mejor ventaja de tipo.")
                try:
                    best_switch = self.choose_best_switch(battle)
                    if best_switch:
                        print(f"Se elige a {best_switch.species} para el cambio forzado (mejor ventaja de tipo).")
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

                move, turns_to_ko = await self.get_best_move_for_pokemon(battle, poke)

                if move and turns_to_ko < best_turns_to_ko:
                    best_turns_to_ko = turns_to_ko
                    best_action = (poke, move)

            # Determina la acción a tomar
            if best_action:
                chosen_poke, chosen_move = best_action
                print(f"Mejor accion: {chosen_poke.species} usa {chosen_move.id} en {best_turns_to_ko} turnos (tiene {chosen_poke.item}) contra {battle.opponent_active_pokemon.species}")

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
                        print("[FALLO] No se puede cambiar")
                        return self.choose_random_move(battle)

            print("Error (o no tiene moves que hagan daño)")
            return self.choose_random_move(battle)

        except AssertionError as ae:
            print(f"[ASSERTION FALLO] Error crítico durante choose_move: {ae}")
            return self.choose_random_move(battle)

        except Exception as e:
            print(f"[FALLO] choose_move general falló: {e}")
            return self.choose_random_move(battle)

    async def get_best_move_for_pokemon(self, battle, poke):

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
            # Calcular el daño y turnos necesarios para KO con el movimiento actual
            data = await calcular_dmg_con_poke_env(
                battle=battle,
                attacker=poke,
                defender=battle.opponent_active_pokemon,
                move=move
            )
            turnos = data.get("turnsToKO", -1)

            print(f"Si {poke.species} usa {move.id}: {turnos} turnos")

            #seleccionamos un move que haga daño
            if turnos != -1:# and not (move.force_switch or move.self_switch):
                if not poke.active:
                    turnos += 1

                # Calcular utilidad estratégica adicional
                is_faster = self.is_faster(poke, battle.opponent_active_pokemon)
                add_effect_score = self.evaluate_additional_effects(move, is_faster)
                typing_adv = self.get_typing_advantage_score(poke, battle.opponent_active_pokemon)

                bono_vel = 3 if is_faster else 0
                total_score = typing_adv * 10 + bono_vel + add_effect_score  # Peso mayor a la ventaja de tipo

                # Decisión priorizando ventaja de tipo
                if best_move is None:
                    best_move = move
                    best_turns = turnos
                    best_typing_score = typing_adv
                    best_move_score = total_score
                elif typing_adv > best_typing_score:
                    best_move = move
                    best_turns = turnos
                    best_typing_score = typing_adv
                    best_move_score = total_score
                elif typing_adv == best_typing_score:
                    if turnos < best_turns:
                        best_move = move
                        best_turns = turnos
                        best_move_score = total_score
                    elif turnos == best_turns and total_score > best_move_score:
                        best_move = move
                        best_move_score = total_score


        return best_move, best_turns


    def is_faster(self, attacker, defender):
        return attacker.base_stats["spe"] > defender.base_stats["spe"]






    def evaluate_additional_effects(self, move, vel):

        score = 0

        if move.priority > 0 and not vel:
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
        
    def get_typing_advantage_score(self, defender, attacker, gen=9):
        type_chart = GenData.from_gen(gen).type_chart

        def get_multiplier(attack_type, defender_types):
            mult = 1.0
            for def_type in defender_types:
                mult *= type_chart.get(def_type, {}).get(attack_type, 1.0)
            return mult

        def score_from_multiplier(mult):
            if mult == 0.0:
                return +4   # immune
            elif mult >= 4.0:
                return -4   # 4x weak
            elif mult >= 2.0:
                return -2   # 2x weak
            elif mult < 1.0:
                return +2   # resist
            else:
                return 0    # neutral

        attacker_types = [t.name.upper() for t in (attacker.types or [])]
        defender_types = [t.name.upper() for t in (defender.types or [])]

        if not attacker_types:
            attacker_types = ["NORMAL"]
        if not defender_types:
            defender_types = ["NORMAL"]

        # Evaluate each attacking type's impact separately
        scores = []
        for atk_type in attacker_types:
            mult = get_multiplier(atk_type, defender_types)
            #print(f"Atacante {atk_type} tiene mul total de {mult} contra {defender_types}")
            scores.append(score_from_multiplier(mult))

        # Use the worst (lowest) score to reflect most dangerous type
        final_score = min(scores)
        #print("Puntuacion final: ", final_score)
        return final_score


    def choose_pokemon_switch(self, battle):
        return self.choose_best_switch(battle)
    

    def choose_best_switch(self, battle):
        if not battle.opponent_active_pokemon:
            print("[INFO] Oponente no visible. Se elige cambio aleatorio.")
            return random.choice(battle.available_switches)

        best_poke = None
        best_score = float('-inf')

        for poke in battle.available_switches:
            if poke.fainted:
                continue

            score = self.get_typing_advantage_score(poke, battle.opponent_active_pokemon)

            print(f"[SWITCH SCORE] {poke.species}: score {score}")
            if score > best_score:
                best_score = score
                best_poke = poke

        return best_poke if best_poke else None
