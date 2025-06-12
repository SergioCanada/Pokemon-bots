
from math import floor
import requests
from utilidades.normalizarItems import normalize_item_name

def poke_env_to_dmg_input(pokemon):
    #print("Tiene: ", pokemon.item)
    return {
        "name": pokemon.base_species,
        "options": {
            "level": pokemon.level,
            "item": normalize_item_name(pokemon.item) if pokemon.item else None,
            "ability": pokemon.ability,
            "status": str(pokemon.status) if pokemon.status else None,
            "stats": pokemon.base_stats,
            "boosts": pokemon.boosts,
            "curHP": pokemon.current_hp,
        }
    }

def calcular_max_hp(base_hp, level, iv=31, ev=0):
    return floor(((2 * base_hp + iv + floor(ev / 4)) * level) / 100) + level + 10

def poke_defensor(pokemon):
    # Asume que pokemon.current_hp es un porcentaje (ej. 70 para 70%)
    porcentaje = pokemon.current_hp
    base_hp = pokemon.base_stats['hp']
    nivel = pokemon.level

    max_hp = calcular_max_hp(base_hp, nivel)
    cur_hp = floor((porcentaje / 100) * max_hp)

    options = {
            "level": nivel,
            "item": normalize_item_name(pokemon.item) if pokemon.item else None,
            "status": str(pokemon.status) if pokemon.status else None,
            "boosts": pokemon.boosts,
            "curHP": cur_hp
        }
    
    if pokemon.is_terastallized:
        options["teraType"] = pokemon.tera_type.name.capitalize()

    return {
        "name": pokemon.base_species,
        "options": options
    }

def move_to_dmg_input(move):
    return {
        "name": move.id,  
        "options": {
            # Puedes añadir laterales como "useZ", "isCrit", etc. si quieres
        }
    }

def campo_general(battle):
    # Clima
    if battle.weather:
        weather_obj = next(iter(battle.weather), None)
        weather = str(weather_obj) if weather_obj else None
        if weather == "snowscape": weather = None #not implemented
    else:
        weather = None

    # Campos como Electric Terrain, Grassy Terrain, etc.
    field_conditions = {}
    if battle.fields:
        for field_effect in battle.fields:
            name = str(field_effect).lower().replace(" ", "")
            # Traducir a claves compatibles con @smogon/calc si es necesario
            if "trickroom" in name:
                field_conditions["isTrickRoom"] = True
            elif "gravity" in name:
                field_conditions["isGravity"] = True
            elif "wonderroom" in name:
                field_conditions["isWonderRoom"] = True
            elif "magicroom" in name:
                field_conditions["isMagicRoom"] = True
            elif "electricterrain" in name:
                field_conditions["terrain"] = "Electric"
            elif "grassyterrain" in name:
                field_conditions["terrain"] = "Grassy"
            elif "mistyterrain" in name:
                field_conditions["terrain"] = "Misty"
            elif "psychicterrain" in name:
                field_conditions["terrain"] = "Psychic"

    return {
        "weather": weather,
        **field_conditions
    }

def campo_oponente(battle):
    side = {}

    if "spikes" in battle.opponent_side_conditions:
        side["spikes"] = battle.opponent_side_conditions["spikes"]
    
    if "stealthrock" in battle.opponent_side_conditions:
        side["stealthRock"] = True
    
    if "toxicspikes" in battle.opponent_side_conditions:
        side["toxicSpikes"] = battle.opponent_side_conditions["toxicspikes"]
    
    if "reflect" in battle.opponent_side_conditions:
        side["isReflect"] = True
    if "lightscreen" in battle.opponent_side_conditions:
        side["isLightScreen"] = True

    return {"defenderSide": side}

def crear_campo(battle):
    field = campo_general(battle)
    defender_side = campo_oponente(battle)
    
    return {
        **field,
        **defender_side,
        "gameType": "singles",
    }

session = requests.Session()

async def calcular_dmg_con_poke_env(battle, attacker, defender, move):
    payload = {
        "attacker": poke_env_to_dmg_input(attacker),
        "defender": poke_defensor(defender),
        "move": move_to_dmg_input(move),
        "field": crear_campo(battle),
    }
    try:
        response = session.post("http://localhost:3000/calc", json=payload, timeout=2)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] calculo de daño fallo para {attacker.species} usando {move.id} contra {defender.species}: {e}")
        return {"turnsToKO": float("inf")}
    
