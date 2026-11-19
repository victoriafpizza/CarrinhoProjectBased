#esse codigo devine a primeira etapa que é a velocidade da bolinha.
import time
import cv2
import numpy as np

cap = cv2.VideoCapture(1)

ret, frame1 = cap.read()
ret, frame2 = cap.read()

# Variável para guardar o tempo do quadro anterior
prev_frame_time = time.time()

# Variáveis para rastreamento da posição anterior da bolinha
prev_cx, prev_cy = None, None
ball_diameter_meters = 0.06  # 6 cm convertidos para metros

while cap.isOpened():
  if not ret:
    break

  # --- Cálculo do Tempo (dt) e FPS ---
  new_frame_time = time.time()
  dt = new_frame_time - prev_frame_time  # Tempo exato entre os quadros em segundos
  fps = 1 / dt if dt > 0 else 0
  prev_frame_time = new_frame_time
  # -----------------------------------

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

  speed_ms = 0.0

  if len(valid_contours) > 0:
    all_contours = np.concatenate(valid_contours)
    (x, y, w, h) = cv2.boundingRect(all_contours)

    # Coordenadas do centro atual da bolinha
    cx = x + w / 2
    cy = y + h / 2

    # Diâmetro médio em pixels (média entre largura e altura do retângulo)
    pixel_diameter = (w + h) / 2

    if pixel_diameter > 0:
      # Escala dinâmica: quantos metros vale cada pixel neste frame
      meters_per_pixel = ball_diameter_meters / pixel_diameter

      # Se já temos uma posição anterior registrada e o tempo é válido
      if prev_cx is not None and prev_cy is not None and dt > 0:
        # Distância em pixels entre a posição anterior e a atual
        pixel_distance = np.sqrt((cx - prev_cx) ** 2 + (cy - prev_cy) ** 2)

        # Converte a distância de pixels para metros reais
        real_distance = pixel_distance * meters_per_pixel

        # Velocidade = Distância (metros) / Tempo (segundos) -> m/s
        speed_ms = real_distance / dt

      # Atualiza a posição anterior para o próximo ciclo
      prev_cx, prev_cy = cx, cy

    # Desenha a caixa unificada na cor verde
    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Exibe a velocidade calculada em m/s na tela
    cv2.putText(
        frame1,
        f"Velocidade: {speed_ms:.2f} m/s",
        (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),
        2,
    )
    print(f"Velocidade calculada: {speed_ms:.2f} m/s")  # Imprime no console para depuração
  else:
    # Se a bolinha sumir da tela, limpa a referência anterior
    prev_cx, prev_cy = None, None

  # Escreve o FPS no canto superior esquerdo da janela (em amarelo)
  cv2.putText(
      frame1,
      f"FPS: {int(fps)}",
      (10, 35),
      cv2.FONT_HERSHEY_SIMPLEX,
      1,
      (0, 255, 255),
      2,
  )

  cv2.imshow("Deteccao de Movimento e Velocidade", frame1)

  frame1 = frame2
  ret, frame2 = cap.read()

  if cv2.waitKey(10) & 0xFF == ord("q"):
    break

cap.release()
cv2.destroyAllWindows()