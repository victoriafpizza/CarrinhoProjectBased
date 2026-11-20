"""Treino supervisionado, coleta serial, avaliação e monitoramento de luminosidade."""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

CLASSES = ("ADEQUADA", "REDUZIDA", "CRITICA")
ACTIONS = {"ADEQUADA": "REGISTRO_NORMAL", "REDUZIDA": "ATENCAO", "CRITICA": "ALERTA"}
ADC_MAX = 4095
CSV_FIELDS = ("fonte", "sessao", "tempo_ms", "adc", "classe")
MIN_SAMPLES = 5


def normalize(raw):
    if type(raw) is not int or not 0 < raw < ADC_MAX:
        raise ValueError("ADC inválido ou saturado")
    return raw / ADC_MAX


def parse_serial(line):
    marker, timestamp, raw, status = line.strip().split(",")
    if marker != "LDR" or status != "OK":
        raise ValueError("Registro serial inválido ou saturado")
    timestamp, raw = int(timestamp), int(raw)
    if not 0 <= timestamp <= 0xFFFFFFFF:
        raise ValueError("Timestamp serial inválido")
    normalize(raw)
    return timestamp, raw


def read_samples(files, source):
    readings = []
    sessions = {}
    for path in files:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != list(CSV_FIELDS):
                raise ValueError(f"Cabeçalho incompatível em {path}")
            for row in reader:
                session, label = row["sessao"], row["classe"]
                if row["fonte"] != source or not session or label not in CLASSES:
                    raise ValueError(f"Origem, sessão ou classe incompatível em {path}")
                timestamp, raw = int(row["tempo_ms"]), int(row["adc"])
                previous = sessions.get(session)
                if timestamp < 0 or (previous and (label != previous[0] or timestamp <= previous[1])):
                    raise ValueError(f"Reset, duplicação ou troca de classe: {session}")
                sessions[session] = (label, timestamp)
                readings.append((session, timestamp, raw, label))
                normalize(raw)
    if not readings:
        raise ValueError("Nenhuma leitura válida no conjunto")
    return readings


def train(readings, source):
    groups = {label: [] for label in CLASSES}
    for _, _, raw, label in readings:
        groups[label].append(normalize(raw))
    if any(len(values) < MIN_SAMPLES for values in groups.values()):
        raise ValueError(f"São necessárias pelo menos {MIN_SAMPLES} leituras por classe")
    centroids = {label: statistics.mean(values) for label, values in groups.items()}
    model = {
        "schema": 1,
        "algoritmo": "centroide_mais_proximo",
        "fonte": source,
        "adc_max": ADC_MAX,
        "centroides": centroids,
        "amostras_por_classe": {label: len(values) for label, values in groups.items()},
        "sessoes_treino": sorted({row[0] for row in readings}),
    }
    return validate_model(model)


def validate_model(model):
    if (
        model["schema"] != 1 or model["algoritmo"] != "centroide_mais_proximo"
        or model["adc_max"] != ADC_MAX or model["fonte"] not in ("real", "sintetica")
    ):
        raise ValueError("Modelo incompatível")
    centroids = model["centroides"]
    if set(centroids) != set(CLASSES) or any(
        type(value) not in (int, float) or not 0 < value < 1
        for value in centroids.values()
    ):
        raise ValueError("Centroides inválidos")
    critical, reduced, adequate = (centroids[label] for label in ("CRITICA", "REDUZIDA", "ADEQUADA"))
    if not (critical < reduced < adequate or adequate < reduced < critical):
        raise ValueError("Classes sem ordenação física. Revise a montagem e a rotulagem.")
    sessions = model["sessoes_treino"]
    if not isinstance(sessions, list) or not sessions or any(
        not isinstance(session, str) or not session for session in sessions
    ):
        raise ValueError("Sessões de treinamento inválidas")
    return model


def predict(model, raw):
    value = normalize(raw)
    ranked = sorted((abs(value - center), label) for label, center in model["centroides"].items())
    distance, label = ranked[0]
    if abs(ranked[1][0] - distance) <= 1e-12:
        raise ValueError("Leitura ambígua entre classes")
    return {"adc": raw, "normalizado": value, "classe": label,
            "resposta": ACTIONS[label], "distancia_centroide": distance}


def assess(model, readings):
    overlap = set(model["sessoes_treino"]) & {row[0] for row in readings}
    if overlap:
        raise ValueError(f"Sessões coincidentes entre treino e teste: {sorted(overlap)}")
    matrix = {label: dict.fromkeys((*CLASSES, "INDETERMINADA"), 0) for label in CLASSES}
    for _, _, raw, expected in readings:
        try:
            predicted = predict(model, raw)["classe"]
        except ValueError:
            predicted = "INDETERMINADA"
        matrix[expected][predicted] += 1
    if any(not sum(row.values()) for row in matrix.values()):
        raise ValueError("O teste precisa incluir as três classes")
    return {"fonte": model["fonte"], "total": len(readings),
            "acertos": sum(matrix[label][label] for label in CLASSES), "matriz": matrix}


def serial_event(stream):
    line = stream.read_until(b"\n", 128)
    if not line:
        raise ValueError("SEM_DADOS_SERIAIS")
    if not line.endswith(b"\n"):
        raise ValueError("QUADRO_SERIAL_INCOMPLETO")
    return parse_serial(line.decode("ascii"))


def capture(stream, args):
    if args.amostras < MIN_SAMPLES or not args.sessao.strip():
        raise ValueError("Informe sessão e quantidade suficiente de amostras")
    last_timestamp = -1
    readings = []
    for _ in range(args.amostras):
        timestamp, raw = serial_event(stream)
        if timestamp <= last_timestamp:
            raise ValueError("Timestamp reiniciado durante a coleta. Repita a sessão.")
        readings.append((args.sessao, timestamp, raw, args.classe))
        last_timestamp = timestamp
    with args.saida.open("x", encoding="utf-8", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(CSV_FIELDS)
        writer.writerows(("real", *reading) for reading in readings)


def monitor(stream, model):
    while True:
        try:
            timestamp, raw = serial_event(stream)
            event = {"fonte": "real", "tempo_ms": timestamp, **predict(model, raw)}
        except ValueError as error:
            event = {"fonte": "real", "classe": None, "resposta": "FALHA", "motivo": str(error)}
        print(json.dumps(event, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    train_parser = commands.add_parser("treinar")
    train_parser.add_argument("--dados", nargs="+", type=Path, required=True)
    train_parser.add_argument("--fonte", choices=("real", "sintetica"), required=True)
    train_parser.add_argument("--saida", type=Path, required=True)
    test_parser = commands.add_parser("avaliar")
    test_parser.add_argument("--dados", nargs="+", type=Path, required=True)
    test_parser.add_argument("--modelo", type=Path, required=True)
    for command in ("coletar", "monitorar"):
        sub = commands.add_parser(command)
        sub.add_argument("--porta", required=True)
        if command == "coletar":
            sub.add_argument("--classe", choices=CLASSES, required=True)
            sub.add_argument("--sessao", required=True)
            sub.add_argument("--amostras", type=int, default=30)
            sub.add_argument("--saida", type=Path, required=True)
        else:
            sub.add_argument("--modelo", type=Path, required=True)
    args = parser.parse_args()

    try:
        if args.command == "treinar":
            model = train(read_samples(args.dados, args.fonte), args.fonte)
            with args.saida.open("x", encoding="utf-8") as output:
                json.dump(model, output, indent=2)
                output.write("\n")
            return 0
        if args.command in ("avaliar", "monitorar"):
            model = validate_model(json.loads(args.modelo.read_text(encoding="utf-8")))
        if args.command == "avaliar":
            print(json.dumps(assess(model, read_samples(args.dados, model["fonte"])), indent=2))
            return 0
        if args.command == "monitorar" and model["fonte"] != "real":
            raise ValueError("O monitor serial requer um modelo treinado com dados reais")
        import serial
        import time

        with serial.Serial(args.porta, 115200, timeout=1.5) as stream:
            time.sleep(2)
            stream.reset_input_buffer()
            if args.command == "coletar":
                capture(stream, args)
            else:
                monitor(stream, model)
    except KeyboardInterrupt:
        return 130
    except (OSError, ValueError, TypeError, KeyError, ImportError) as error:
        print(f"FALHA: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
