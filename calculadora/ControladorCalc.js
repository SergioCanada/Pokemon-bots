import { CalculatorService } from './ServicioCalculadora.js';

export class CalculatorController {
  constructor() {
    this.service = new CalculatorService();
  }

  handleCalcRequest(req, res) {
    try {
      const { attacker, defender, move, field } = req.body;
      const turnsToKO = this.service.calculateDamage(attacker, defender, move, field);
      res.json({ turnsToKO });
    } catch (error) {
      console.error('Error al calcular el daño:', error);
      res.status(500).json({ error: 'Error interno al calcular el daño' });
    }
  }
}
