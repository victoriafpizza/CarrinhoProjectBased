import math
import os
import time
from collections import deque

import cv2

CAMERA = 1            # índice da webcam
AREA_MIN = 600        # área mínima do contorno (filtra ruído)
PARADA_S = 0.5        # segundos gravando após o movimento cessar
PRE_ROLL_S = 1.0      # segundos gravados antes da detecção
BOLA_M = 0.06         # diâmetro real da bolinha (6 cm) -> calibra pixels em metros
SUAVIZA = 0.5         # 0 a 1: quanto maior, mais reage à velocidade nova
CAMERA_ALTURA_M = 1.34 # Altura da câmera em relação ao chão (134 cm)

cap = cv2.VideoCapture(CAMERA)
if not cap.isOpened():
  raise SystemExit('Erro ao abrir a webcam.')

w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if not 0 < fps <= 60:
  fps = 20.0

os.makedirs('videos_gravados', exist_ok=True)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
bg = cv2.createBackgroundSubtractorMOG2(history=200, varThreshold=40, detectShadows=False)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
pre_buffer = deque(maxlen=int(fps * PRE_ROLL_S))
out = None
ultimo_mov = 0
prev = None   # (cx, cy, t) da detecção anterior
vel = 0.0     # velocidade suavizada em m/s
altura_m = CAMERA_ALTURA_M  # Altura padrão inicial

print("Pressione 'q' na janela do vídeo para sair.")

while True:
  ok, frame = cap.read()
  if not ok:
    break
  t = time.perf_counter()
  limpo = frame.copy()  # usado no pré-buffer (ainda sem detecção)

  mask = bg.apply(frame)
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
  mask = cv2.dilate(mask, None, iterations=2)
  contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  candidatos = [c for c in contornos if cv2.contourArea(c) >= AREA_MIN]

  movimento = bool(candidatos)
  if movimento:
    # Maior contorno = bolinha
    x, y, bw, bh = cv2.boundingRect(max(candidatos, key=cv2.contourArea))
    cx, cy = x + bw / 2, y + bh / 2

    # Escala: a menor dimensão da caixa (o borrão alonga a outra) equivale a 6 cm
    m_por_px = BOLA_M / max(min(bw, bh), 1)

    # --- CÁLCULO DA ALTURA EM RELAÇÃO AO CHÃO ---
    y_centro = h / 2  # Centro vertical da imagem
    vertical_offset_pixels = y_centro - cy  # Eixo Y cresce para baixo no OpenCV
    altura_m = CAMERA_ALTURA_M + (vertical_offset_pixels * m_por_px)
    # --------------------------------------------

    if prev and t - prev[2] < 0.2:
      v = math.hypot(cx - prev[0], cy - prev[1]) * m_por_px / (t - prev[2])
      vel = SUAVIZA * v + (1 - SUAVIZA) * vel
    else:
      vel = 0.0
    prev = (cx, cy, t)

    # Caixa de identificação + velocidade e altura ao lado
    cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    
    # Texto de Velocidade
    cv2.putText(frame, f'Vel: {vel:.2f} m/s', (min(x + bw + 8, w - 220), y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Texto de Altura
    cv2.putText(frame, f'Alt: {altura_m:.2f} m', (min(x + bw + 8, w - 220), y + 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
  else:
    prev, vel = None, 0.0

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
    out.write(frame)  # grava com caixa, velocidade e altura na imagem
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