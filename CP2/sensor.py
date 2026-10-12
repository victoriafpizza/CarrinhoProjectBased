
import serial
import csv
import time
from pathlib import Path

# ==========================================
# CP2 - TINYML + ESP32
# SENSOR ULTRASSÔNICO HC-SR04
# ==========================================

# CONFIGURAÇÕES
PORTA = "COM5"  # Altere para a porta do ESP32
BAUD_RATE = 115200

ARQUIVO_CSV = "dados_sensor.csv"

# ==========================================
# CLASSIFICAÇÃO DAS DISTÂNCIAS
# ==========================================

def classificar_distancia(distancia):

    if distancia < 25:
        return "PERIGO"

    elif distancia <= 60:
        return "ATENCAO"

    else:
        return "LIVRE"


# ==========================================
# CONEXÃO COM O ESP32
# ==========================================

def conectar_sensor():

    try:
        esp32 = serial.Serial(
            PORTA,
            BAUD_RATE,
            timeout=2
        )

        time.sleep(2)

        print("ESP32 conectado!")
        return esp32

    except serial.SerialException as erro:
        print("Erro ao conectar:", erro)
        return None


# ==========================================
# COLETA DOS DADOS
# ==========================================

def coletar_dados():

    esp32 = conectar_sensor()

    if esp32 is None:
        return

    caminho = Path(ARQUIVO_CSV)

    novo_arquivo = (
        not caminho.exists()
        or caminho.stat().st_size == 0
    )

    try:
        with open(
            ARQUIVO_CSV,
            "a",
            newline="",
            encoding="utf-8"
        ) as arquivo:

            writer = csv.writer(arquivo)

            if novo_arquivo:
                writer.writerow([
                    "tempo_ms",
                    "distancia_cm",
                    "classe"
                ])

            print("Iniciando coleta...")
            print("Pressione CTRL+C para parar.")

            # Inicia a coleta no código .ino
            esp32.write(b"s")

            while True:

                linha = esp32.readline().decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                if not linha or linha.startswith("#"):
                    continue

                partes = linha.split(",")

                if len(partes) != 3:
                    continue

                try:
                    tempo_ms = int(partes[0])
                    distancia = float(partes[1])

                except ValueError:
                    continue

                # Ignora leituras inválidas
                if not 2 <= distancia <= 400:
                    continue

                # Classificação inicial por distância
                classe = classificar_distancia(distancia)

                writer.writerow([
                    tempo_ms,
                    round(distancia, 2),
                    classe
                ])

                arquivo.flush()

                print(
                    f"Tempo: {tempo_ms} ms | "
                    f"Distância: {distancia:.2f} cm | "
                    f"Classe: {classe}"
                )

    except KeyboardInterrupt:
        print("\nColeta finalizada.")

    finally:
        if esp32.is_open:
            esp32.write(b"p")
            esp32.close()

        print("Dados salvos em:", ARQUIVO_CSV)


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    coletar_dados()
