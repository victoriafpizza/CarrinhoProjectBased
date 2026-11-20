"""Treina em dados sintéticos e testa quadros de um ESP32 simulado."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "inteligencia-artificial"))
from luminosidade import assess, parse_serial, predict, read_samples, train


def events(model):
    for line in ("LDR,200,3200,OK", "LDR,400,1900,OK", "LDR,600,700,OK",
                 "LDR,800,4095,LIMITE_OU_INVALIDO", ""):
        try:
            timestamp, raw = parse_serial(line)
            yield {"fonte": "sintetica", "tempo_ms": timestamp, **predict(model, raw)}
        except ValueError as error:
            reason = str(error) if line else "SEM_DADOS_SERIAIS"
            yield {"fonte": "sintetica", "classe": None, "resposta": "FALHA", "motivo": reason}


def main():
    model = train(read_samples([ROOT / "dados/treino_sintetico.csv"], "sintetica"), "sintetica")
    report = assess(model, read_samples([ROOT / "dados/teste_sintetico.csv"], "sintetica"))
    print(json.dumps({"modelo": model, "avaliacao": report, "registros": list(events(model))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
