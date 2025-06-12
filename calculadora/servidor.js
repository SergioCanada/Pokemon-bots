import express from 'express';
import cors from 'cors';
import { CalculatorController } from './ControladorCalc.js';

const app = express();
const PORT = 3000;
const controller = new CalculatorController();

app.use(cors());
app.use(express.json());

app.post('/calc', (req, res) => controller.handleCalcRequest(req, res));

app.listen(PORT, () => {
  console.log(` Servidor de calculadora escuchando en http://localhost:${PORT}`);
});
