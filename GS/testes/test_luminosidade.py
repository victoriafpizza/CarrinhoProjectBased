import io
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "inteligencia-artificial"))
from luminosidade import (assess, capture, parse_serial, predict, read_samples,
                          serial_event, train, validate_model)


class SerialFixture(io.BytesIO):
    def read_until(self, expected, size):
        if expected != b"\n":
            raise AssertionError("O protocolo usa fim de linha")
        return self.readline(size)


class LuminosidadeTests(unittest.TestCase):
    def setUp(self):
        self.readings = read_samples([ROOT / "dados/treino_sintetico.csv"], "sintetica")
        self.model = train(self.readings, "sintetica")

    def test_normal_and_alert_responses(self):
        for adc, expected in [(3200, "REGISTRO_NORMAL"), (1900, "ATENCAO"), (700, "ALERTA")]:
            with self.subTest(adc=adc):
                self.assertEqual(predict(self.model, adc)["resposta"], expected)

    def test_test_split(self):
        readings = read_samples([ROOT / "dados/teste_sintetico.csv"], "sintetica")
        result = assess(self.model, readings)
        self.assertEqual((result["acertos"], result["total"]), (6, 6))
        with self.assertRaises(ValueError):
            assess(self.model, self.readings)

    def test_reverse_polarity(self):
        model = train([(s, t, 4095 - adc, label) for s, t, adc, label in self.readings], "sintetica")
        self.assertEqual(predict(model, 895)["classe"], "ADEQUADA")
        self.assertEqual(predict(model, 3395)["classe"], "CRITICA")

    def test_serial_valid(self):
        self.assertEqual(serial_event(SerialFixture(b"LDR,200,3200,OK\n")), (200, 3200))

    def test_serial_failures(self):
        for frame in (b"", b"LDR,1,22,OK", b"LDR,1,-1,OK\n", b"LDR,1,4095,OK\n",
                      b"LDR,1,900,LIMITE_OU_INVALIDO\n", b"LDR,1,0,OK\n", b"inv\xff\n"):
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                serial_event(SerialFixture(frame))

    def test_invalid_model_and_ambiguity(self):
        for value in (float("nan"), 0, self.model["centroides"]["ADEQUADA"]):
            invalid = dict(self.model, centroides=dict(self.model["centroides"], REDUZIDA=value))
            with self.assertRaises(ValueError):
                validate_model(invalid)
        # Midpoint at 2550 between synthetic centroids 1900 and 3200.
        with self.assertRaisesRegex(ValueError, "ambígua"):
            predict(self.model, 2550)

    def test_class_balance_and_provenance(self):
        with self.assertRaises(ValueError):
            train(self.readings[:5], "sintetica")
        with self.assertRaises(ValueError):
            read_samples([ROOT / "dados/treino_sintetico.csv"], "real")

    def test_capture_transaction(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "capture.csv"
            args = Namespace(amostras=5, saida=output, sessao="ensaio-1", classe="ADEQUADA")
            stream = b"LDR,200,3200,OK\n"
            with self.assertRaisesRegex(ValueError, "reiniciado"):
                capture(SerialFixture(stream * 2), args)
            self.assertFalse(output.exists())
            frames = b"".join(f"LDR,{i * 200},3200,OK\n".encode() for i in range(5))
            capture(SerialFixture(frames), args)
            self.assertEqual(len(read_samples([output], "real")), 5)

    def test_model_gate_and_absence(self):
        cli = [sys.executable, str(ROOT / "inteligencia-artificial/luminosidade.py"), "monitorar",
               "--porta", "COM99", "--modelo"]
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.json"
            missing = subprocess.run([*cli, str(model)], capture_output=True)
            self.assertEqual(missing.returncode, 1)
            model.write_text(json.dumps(self.model), encoding="utf-8")
            simulation = subprocess.run([*cli, str(model)], capture_output=True)
            self.assertEqual(simulation.returncode, 1)
            self.assertIn(b"dados reais", simulation.stderr)

    def test_simulator_cli(self):
        demo = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "simulacao/demo.py")],
                              check=True, capture_output=True)
        results = json.loads(demo.stdout)
        self.assertEqual(results["avaliacao"]["total"], 6)
        self.assertEqual([r["resposta"] for r in results["registros"]],
                         ["REGISTRO_NORMAL", "ATENCAO", "ALERTA", "FALHA", "FALHA"])


if __name__ == "__main__":
    unittest.main()
