#esse codigo promete o aumento de FPS, mas percebi que não fuincionou bem então vou optar pelas opções anteriores.
import math
import os
import time
from collections import deque

import cv2

CAMERA = 1            # índice da webcam
FPS_ALVO = 60         # FPS desejado (a câmera precisa suportar)
LARGURA, ALTURA = 1280, 720   # resolução pedida (se não der 60 FPS, tente 640x480)
ESCALA_DET = 0.5      # detecta em imagem reduzida p/ ganhar velocidade (1.0 = tamanho original)
AREA_MIN = 300        # área mínima do contorno (em pixels da imagem original)
PARADA_S = 0.5        # segundos gravando após o movimento cessar
PRE_ROLL_S = 1.0      # segundos gravados antes da detecção
BOLA_M = 0.06         # diâmetro real da bolinha (6 cm)
SUAVIZA = 0.4         # suavização da velocidade
CAMERA_ALTURA_M = 1.34  # altura da câmera em relação ao chão (134 cm)

# --- Abre a câmera forçando MJPG + resolução + FPS (a ordem importa) ---
backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
cap = cv2.VideoCapture(CAMERA, backend)
if not cap.isOpened():
  raise SystemExit('Erro ao abrir a webcam.')

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # YUY2 não passa de ~30 FPS em HD
cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA)
cap.set(cv2.CAP_PROP_FPS, FPS_ALVO)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # menos atraso (ignorado em alguns drivers)

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Mede o FPS real da câmera (o valor reportado pelo driver nem sempre é verdadeiro)
for _ in range(10):
  cap.read()
t0 = time.perf_counter()
for _ in range(60):
  cap.read()
fps = 60 / (time.perf_counter() - t0)
print(f'Câmera: {w}x{h} @ {fps:.1f} FPS (pedido: {FPS_ALVO})')
if fps < FPS_ALVO * 0.9:
  print('AVISO: a câmera não está entregando o FPS pedido. Tente outra resolução, '
        'mais luz no ambiente, ou outro backend (CAP_MSMF).')

os.makedirs('videos_gravados', exist_ok=True)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=25, detectShadows=False)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
dil_it = max(1, round(2 * ESCALA_DET))
area_min_det = AREA_MIN * ESCALA_DET ** 2
pre_buffer = deque(maxlen=int(fps * PRE_ROLL_S))
out = None
ultimo_mov = 0

historico_posicoes = deque(maxlen=5)
vel = 0.0
altura_m = CAMERA_ALTURA_M
fps_tela = fps
t_ant = time.perf_counter()

print("Pressione 'q' na janela do vídeo para sair.")

while True:
  ok, frame = cap.read()
  if not ok:
    break
  t = time.perf_counter()
  limpo = frame.copy()

  # FPS em tempo real (média suavizada)
  if t > t_ant:
    fps_tela = 0.9 * fps_tela + 0.1 / (t - t_ant)
  t_ant = t

  # Detecção em imagem reduzida
  det = cv2.resize(frame, None, fx=ESCALA_DET, fy=ESCALA_DET,
                   interpolation=cv2.INTER_AREA) if ESCALA_DET != 1 else frame
  mask = bg.apply(det)
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
  mask = cv2.dilate(mask, None, iterations=dil_it)
  contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  candidatos = [c for c in contornos if cv2.contourArea(c) >= area_min_det]

  movimento = bool(candidatos)
  if movimento:
    bx, by, bbw, bbh = cv2.boundingRect(max(candidatos, key=cv2.contourArea))
    x, y = int(bx / ESCALA_DET), int(by / ESCALA_DET)
    bw, bh = int(bbw / ESCALA_DET), int(bbh / ESCALA_DET)
    cx, cy = x + bw / 2, y + bh / 2

    # Escala baseada na menor dimensão
    m_por_px = BOLA_M / max(min(bw, bh), 1)

    # Altura
    altura_m = CAMERA_ALTURA_M + (h / 2 - cy) * m_por_px

    # Velocidade (janela curta de 5 posições)
    historico_posicoes.append((cx, cy, t))
    if len(historico_posicoes) >= 2:
      p_antigo = historico_posicoes[0]
      dt_total = t - p_antigo[2]
      if dt_total > 0:
        dist_px = math.hypot(cx - p_antigo[0], cy - p_antigo[1])
        v_inst = (dist_px * m_por_px) / dt_total
        vel = SUAVIZA * v_inst + (1 - SUAVIZA) * vel
    else:
      vel = 0.0

    cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    cv2.putText(frame, f'Vel: {vel:.2f} m/s', (min(x + bw + 8, w - 220), y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f'Alt: {altura_m:.2f} m', (min(x + bw + 8, w - 220), y + 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
  else:
    historico_posicoes.clear()
    vel = 0.0

  cv2.putText(frame, f'FPS: {fps_tela:.0f}', (10, 35),
              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

  agora = time.time()
  if movimento:
    ultimo_mov = agora
    if out is None:
      nome = f"videos_gravados/bolinha_{time.strftime('%Y%m%d_%H%M%S')}.avi"
      out = cv2.VideoWriter(nome, fourcc, fps, (w, h))
      for f in pre_buffer:
        out.write(f)
      print(f'Gravando: {nome}')

  if out is not None:
    out.write(frame)  # grava com caixa, velocidade, altura e FPS
    cv2.circle(frame, (30, 80), 10, (0, 0, 255), -1)  # REC só na tela
    cv2.putText(frame, 'REC', (50, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    if not movimento and agora - ultimo_mov > PARADA_S:
      out.release()
      out = None
      print('Movimento cessou. Vídeo salvo!')
  else:
    pre_buffer.append(limpo)

  cv2.imshow('Deteccao de Movimento - Bolinha', frame)
  if cv2.waitKey(1) & 0xFF == ord('q'):
    break

if out is not None:
  out.release()
cap.release()
cv2.destroyAllWindows()