#codigo repaginado,depois de aguns teste percebi que o sistema trava com velocidade constante e não companha a curva feita pela 
#graviade vou execultar o teste 11 agora 
import math
import time
import cv2
import numpy as np

cap = cv2.VideoCapture(1)

ret, frame1 = cap.read()
ret, frame2 = cap.read()

prev_frame_time = 0

# --- CONFIGURAÇÃO DO FILTRO DE KALMAN (6 ESTADOS: Posição, Velocidade e Aceleração) ---
# 6 estados: [x, y, dx, dy, ddx, ddy] -> (posição, velocidade e aceleração horizontal/vertical)
# 2 medições: [x, y] (posição real detectada pela câmera)
kf = cv2.KalmanFilter(6, 2)

# O que o OpenCV mede: apenas x e y
kf.measurementMatrix = np.array(
    [[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0]], np.float32
)

# Matriz de Transição Física (Equações do movimento com aceleração)
# x = x + dx + 0.5*ddx
# y = y + dy + 0.5*ddy
kf.transitionMatrix = np.array(
    [
        [1, 0, 1, 0, 0.5, 0],
        [0, 1, 0, 1, 0, 0.5],
        [0, 0, 1, 0, 1, 0],
        [0, 0, 0, 1, 0, 1],
        [0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 0, 1],
    ],
    np.float32,
)

# Covariância do ruído do processo (ajustada para permitir que o filtro reaja rápido a mudanças como gravidade)
kf.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03

predicted_center = None
history_errors = []
accuracy_percentage = 100.0
is_initialized = False

while cap.isOpened():
  # --- Cálculo do FPS ---
  new_frame_time = time.time()
  fps = (
      1 / (new_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
  )
  prev_frame_time = new_frame_time
  # ----------------------

  # Detecção de movimento padrão
  diff = cv2.absdiff(frame1, frame2)
  gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
  blur = cv2.GaussianBlur(gray, (5, 5), 0)
  _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
  dilated = cv2.dilate(thresh, None, iterations=3)
  contours, _ = cv2.findContours(
      dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
  )

  valid_contours = []
  for contour in contours:
    if cv2.contourArea(contour) < 500:
      continue
    valid_contours.append(contour)

  detected_center = None
  cx, cy = 0, 0

  if len(valid_contours) > 0:
    all_contours = np.concatenate(valid_contours)
    (x, y, w, h) = cv2.boundingRect(all_contours)

    cx = x + w // 2
    cy = y + h // 2
    detected_center = np.array([[np.float32(cx)], [np.float32(cy)]])

    # Inicializa o estado do Kalman na primeira detecção (6 estados: pos, vel, aceleração zerada)
    if not is_initialized:
      kf.statePre = np.array(
          [[np.float32(cx)], [np.float32(cy)], [0], [0], [0], [0]], np.float32
      )
      kf.statePost = np.array(
          [[np.float32(cx)], [np.float32(cy)], [0], [0], [0], [0]], np.float32
      )
      is_initialized = True

    # 1. COMPARAÇÃO
    if predicted_center is not None:
      error_distance = math.sqrt(
          (predicted_center[0] - cx) ** 2 + (predicted_center[1] - cy) ** 2
      )
      max_tolerated_error = 100.0
      frame_accuracy = max(
          0.0,
          min(100.0, (1.0 - (error_distance / max_tolerated_error)) * 100.0),
      )

      history_errors.append(frame_accuracy)
      if len(history_errors) > 20:
        history_errors.pop(0)

      accuracy_percentage = sum(history_errors) / len(history_errors)

    # 2. CORREÇÃO
    kf.correct(detected_center)

    # Desenha a caixa real (verde)
    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.circle(frame1, (cx, cy), 5, (0, 255, 0), -1)
    cv2.putText(
        frame1,
        'Bolinha Detectada',
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )

  # 3. PREVISÃO E CURVA DOS PONTINHOS COM ACELERAÇÃO
  if is_initialized:
    prediction = kf.predict()
    predicted_center = (int(prediction[0].item()), int(prediction[1].item()))

    # --- SIMULAÇÃO DA CURVA PARABÓLICA (PONTINHOS) ---
    future_state = kf.statePost.copy()
    num_dots = 10  # Quantidade de pontinhos no ar para frente

    for i in range(num_dots):
      # Projeta o estado considerando a aceleração dinâmica (ponto de inflexão / gravidade)
      future_state = np.dot(kf.transitionMatrix, future_state)
      fx = int(future_state[0].item())
      fy = int(future_state[1].item())

      # Desenha os pontinhos formando a curva preditiva
      cv2.circle(frame1, (fx, fy), 4, (0, 255, 255), -1)

    # Desenha o círculo principal de previsão final (azul)
    cv2.circle(frame1, predicted_center, 6, (255, 0, 0), -1)
    cv2.putText(
        frame1,
        'Previsao Kalman',
        (predicted_center[0] + 10, predicted_center[1]),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 0, 0),
        2,
    )

  # Exibe FPS e Porcentagem de Acerto na tela
  cv2.putText(
      frame1,
      f'FPS: {int(fps)}',
      (10, 35),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.8,
      (0, 255, 255),
      2,
  )
  cv2.putText(
      frame1,
      f'Acerto: {accuracy_percentage:.1f}%',
      (10, 70),
      cv2.FONT_HERSHEY_SIMPLEX,
      0.8,
      (255, 0, 255),
      2,
  )

  cv2.imshow('Deteccao com Filtro de Kalman', frame1)

  frame1 = frame2
  ret, frame2 = cap.read()
  if not ret:
    break

  if cv2.waitKey(10) & 0xFF == ord('q'):
    break

cap.release()
cv2.destroyAllWindows()