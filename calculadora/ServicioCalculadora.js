import { Generations, calculate, Pokemon, Move, Field } from '@smogon/calc';

export class CalculatorService {
  constructor(genNumber = 9) {
    this.gen = Generations.get(genNumber);
  }

  calculateDamage(attackerData, defenderData, moveData, fieldData) {
    const attacker = new Pokemon(this.gen, attackerData.name, attackerData.options || {});
    const defender = new Pokemon(this.gen, defenderData.name, defenderData.options || {});
    const move = new Move(this.gen, moveData.name, moveData.options || {});
    const field = new Field(fieldData || {});

    const result = calculate(this.gen, attacker, defender, move, field);
    const description = result.desc().replace(/O/g, '0');

    const hkoMatch = description.match(/(\d+)HK0/);
    return hkoMatch ? Math.max(parseInt(hkoMatch[1], 10), 1) : -1;
  }
}
