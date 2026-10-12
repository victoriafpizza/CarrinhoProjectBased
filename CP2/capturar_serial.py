
import argparse
import csv
from pathlib import Path
import re
import threading
import serial

# ==========================================
# CONFIGURAÇÕES DA COLETA
# ==========================================

parser = argparse.ArgumentParser()

parser.add_argument('--porta', required=True)
parser.add_argument('--baud', type=int, default=115200)
parser.add_argument(
    '--saida',
    default='../dataset/dados_brutos.csv'
)

args = parser.parse_args()

saida = Path(args.saida)
saida.parent.mkdir(parents=True, exist_ok=True)

existe = saida.exists() and saida.stat().st_size > 0

# ==========================================
# CONEXÃO COM ESP32
# ==========================================

with serial.Serial(
    args.porta,
    args.baud,
    timeout=1
) as ser, saida.open(
    'a',
    newline='',
    encoding='utf-8'
) as f:

    writer = csv.writer(f)

    if not existe:
        writer.writerow([
            'tempo_ms',
            'distancia_cm',
            'classe'
        ])

    print("ESP32 conectado!")
    print("1 = LIVRE")
    print("2 = ATENCAO")
    print("3 = PERIGO")
    print("s = iniciar coleta")
    print("p = pausar coleta")
    print("q = finalizar")

    ativo = threading.Event()
    ativo.set()

    # ==========================================
    # CONTROLE DA COLETA
    # ==========================================

    def comandos():
        while ativo.is_set():

            try:
                cmd = input().strip().lower()
            except EOFError:
                cmd = 'q'

            if cmd == 'q':
                ativo.clear()
                break

            if cmd in {'1', '2', '3', 's', 'p'}:
                ser.write(cmd.encode('ascii'))

    threading.Thread(
        target=comandos,
        daemon=True
    ).start()

    # ==========================================
    # CAPTURA DOS DADOS REAIS
    # ==========================================

    total = 0

    while ativo.is_set():

        linha = ser.readline().decode(
            'utf-8',
            errors='replace'
        ).strip()

        if linha.startswith('#'):
            print(linha)
            continue

        colunas = linha.split(',')

        if len(colunas) != 3:
            continue

        if not re.fullmatch(r'\d+', colunas[0]):
            continue

        try:
            distancia = float(colunas[1])
        except ValueError:
            continue

        if not (2 <= distancia <= 400):
            continue

        if colunas[2] not in {
            'LIVRE',
            'ATENCAO',
            'PERIGO'
        }:
            continue

        writer.writerow(colunas)
        f.flush()

        total += 1

        print(f'{total:04d} | {linha}')

print("Coleta encerrada!")
print("Arquivo CSV:", saida)
