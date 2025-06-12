# Pokémon Bots - Simulador de batallas con bots básicos

Este proyecto permite simular batallas de Pokémon usando bots programados, tanto en modo local como en línea contra el servidor oficial Pokémon Showdown. Ideal para experimentos, entrenamientos y torneos automáticos.

## Requisitos previos

- Python 3.10 o superior  
- Node.js instalado y accesible desde la terminal  
- Dependencias Python instaladas (ver sección Instalación)  

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/SergioCanada/Pokemon-bots.git
   cd pokemon-bots
   git clone https://github.com/smogon/pokemon-showdown.git

2. Entorno virtual (opcional)
   ```bash
   python -m venv venv
   venv\Scripts\activate
   
3. Dependencias
   ```bash
   pip install -r requirements.txt
   npm install
   
## Uso
Modo Local
Ejecuta batallas entre bots en servidores locales:

      python main.py --modo local --batallas 10 --bot1 ataca --bot2 defiende

Modo Online
Compite en el servidor oficial Pokémon Showdown:

      python main.py --modo online --tipo_online ladder --batallas 5 --bot1 defiende

Nota: Para el modo online es posible configurar las credenciales de usuario en config.py.

Los bots disponibles son: random, maxdmg, ataca y defiende.
En online, el tipo puede ser ladder (bot vs alguien jugando competitivo) o desafio (puedes desafiarlo tù)




