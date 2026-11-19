#calculo sem IA de onde a bolinha vai cair e tentar calcular onde ela vai e retornar o a porcentagem de acerto que ele realizou.
#o oitavo teste foi bem sucedito ele consegue calcular com certa presisão pelo visto.
#o que estou pesando ele pegar o intante em que o objeto estara na menor velocidade e tirar fotos e mandar para a IA rotular a imagem.
import math
import time
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

ret, frame1 = cap.read()
ret, frame2 = cap.read()

prev_frame_time = 0

# Variáveis para rastreamento e previsão
prev_center = None
current_velocity = (0, 0)
predicted_center = None

# Métricas de acerto
history_errors = []
accuracy_percentage = 100.0

while cap.isOpened():
  if not ret:
    break

  # --- Cálculo do FPS ---
  new_frame_time = time.time()
  fps = (
      1 / (new_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
  )
  prev_frame_time = new_frame_time
  # ----------------------

  # Detecção de movimento
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

  if len(valid_contours) > 0:
    all_contours = np.concatenate(valid_contours)
    (x, y, w, h) = cv2.boundingRect(all_contours)

    # Centro atual do objeto detectado
    cx = x + w // 2
    cy = y + h // 2
    detected_center = (cx, cy)

    # 1. COMPARAÇÃO (Avaliar a previsão anterior)
    if predicted_center is not None and detected_center is not None:
      # Calcula a distância euclidiana entre o que foi previsto e o que realmente aconteceu
      error_distance = math.sqrt(
          (predicted_center[0] - detected_center[0]) ** 2
          + (predicted_center[1] - detected_center[1]) ** 2
      )

      # Converte o erro em porcentagem de acerto (considerando um limiar máximo de 100 pixels de erro para 0%)
      max_tolerated_error = 100.0
      frame_accuracy = max(
          0.0,
          min(100.0, (1.0 - (error_distance / max_tolerated_error)) * 100.0),
      )

      # Guarda no histórico para tirar uma média móvel suave
      history_errors.append(frame_accuracy)
      if len(history_errors) > 20:  # Mantém os últimos 20 quadros
        history_errors.pop(0)

      accuracy_percentage = sum(history_errors) / len(history_errors)

    # 2. PREVISÃO (Estimar o próximo movimento com base na velocidade atual)
    if prev_center is not None:
      # Velocidade = Posição Atual - Posição Anterior
      current_velocity = (
          detected_center[0] - prev_center[0],
          detected_center[1] - prev_center[1],
      )
      # Previsão linear simples: Posição Futura = Posição Atual + Velocidade
      predicted_center = (
          detected_center[0] + current_velocity[0],
          detected_center[1] + current_velocity[1],
      )
    else:
      predicted_center = detected_center

    prev_center = detected_center

    # Desenha a caixa unificada na cor verde (Real)
    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.circle(frame1, detected_center, 5, (0, 255, 0), -1)

    cv2.putText(
        frame1,
        'Bolinha Detectada',
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )

  else:
    # Se perdeu a bolinha temporariamente, limpa as referências de movimento
    prev_center = None
    predicted_center = None

  # Desenha a previsão futura (se houver) na cor azul
  if predicted_center is not None:
    cv2.circle(
        frame1,
        (int(predicted_center[0]), int(predicted_center[1])),
        6,
        (255, 0, 0),
        -1,
    )
    cv2.putText(
        frame1,
        'Previsao',
        (int(predicted_center[0]) + 10, int(predicted_center[1])),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 0, 0),
        2,
    )

  # Exibe o FPS e a Porcentagem de Acerto na tela
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

  cv2.imshow('Deteccao e Previsao de Movimento', frame1)

  frame1 = frame2
  ret, frame2 = cap.read()

  if cv2.waitKey(10) & 0xFF == ord('q'):
    break

cap.release()
cv2.destroyAllWindows()