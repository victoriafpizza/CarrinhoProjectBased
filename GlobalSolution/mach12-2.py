#o codigo esta bom mas  percebo uma certa impresisão da camera quanto a velocidade da bolinha,pela minha pesquisa percebi que ela é mais 
#presisa quando o FPS é maior então busquei forma de almetar o FPS, eu iluminei a sala e deixe a camera mais distante.
import math
import os
import time
from collections import deque

import cv2

CAMERA = 1            # índice da webcam
AREA_MIN = 300        # REDUZIDO: Detecta a bolinha mais cedo (mesmo menor/mais longe)
PARADA_S = 0.5        # segundos gravando após o movimento cessar
PRE_ROLL_S = 1.0      # segundos gravados antes da detecção
BOLA_M = 0.06         # diâmetro real da bolinha (6 cm)
SUAVIZA = 0.4         # suavização da velocidade
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
bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=25, detectShadows=False) # Ajustado para maior sensibilidade
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
pre_buffer = deque(maxlen=int(fps * PRE_ROLL_S))
out = None
ultimo_mov = 0

# Usamos um deque para guardar as últimas posições e calcular uma velocidade imediata
historico_posicoes = deque(maxlen=5) 
vel = 0.0
altura_m = CAMERA_ALTURA_M

print("Pressione 'q' na janela do vídeo para sair.")

while True:
  ok, frame = cap.read()
  if not ok:
    break
  t = time.perf_counter()
  limpo = frame.copy()

  mask = bg.apply(frame)
  mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
  mask = cv2.dilate(mask, None, iterations=2)
  contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  candidatos = [c for c in contornos if cv2.contourArea(c) >= AREA_MIN]

  movimento = bool(candidatos)
  if movimento:
    x, y, bw, bh = cv2.boundingRect(max(candidatos, key=cv2.contourArea))
    cx, cy = x + bw / 2, y + bh / 2

    # Escala baseada na menor dimensão
    m_por_px = BOLA_M / max(min(bw, bh), 1)

    # --- CÁLCULO DA ALTURA ---
    y_centro = h / 2
    vertical_offset_pixels = y_centro - cy
    altura_m = CAMERA_ALTURA_M + (vertical_offset_pixels * m_por_px)

    # --- CÁLCULO DA VELOCIDADE MAIS ROBUSTO ---
    historico_posicoes.append((cx, cy, t))
    
    if len(historico_posicoes) >= 2:
      # Pega o ponto mais antigo do histórico curto para calcular o delta de movimento imediato
      p_antigo = historico_posicoes[0]
      dt_total = t - p_antigo[2]
      
      if dt_total > 0:
        dist_px = math.hypot(cx - p_antigo[0], cy - p_antigo[1])
        v_inst = (dist_px * m_por_px) / dt_total
        vel = SUAVIZA * v_inst + (1 - SUAVIZA) * vel
    else:
      vel = 0.0

    # Caixa de identificação + textos
    cv2.rectangle(frame, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
    cv2.putText(frame, f'Vel: {vel:.2f} m/s', (min(x + bw + 8, w - 220), y + 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, f'Alt: {altura_m:.2f} m', (min(x + bw + 8, w - 220), y + 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
  else:
    historico_posicoes.clear()
    vel = 0.0

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
    out.write(frame)
    cv2.circle(frame, (30, 80), 10, (0, 0, 255), -1)
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