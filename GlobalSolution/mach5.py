#novo codigo para juntar as areas onde o movimento foi identificado, e assim identificar a bolinha de papel, e não apenas o movimento.
#o 5 teste foi muito bem, ainda não esta perfeito mas ja esta melhor do que antes e com isso podemos tentar aplicar a IA
import time
import cv2
import numpy as np

cap = cv2.VideoCapture(0)

ret, frame1 = cap.read()
ret, frame2 = cap.read()

# Variável para guardar o tempo do quadro anterior
prev_frame_time = 0

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

    # Lista para juntar todos os pontos dos contornos válidos
    valid_contours = []

    for contour in contours:
        if cv2.contourArea(contour) < 500:
            continue
        valid_contours.append(contour)

    # Se encontramos algum contorno válido, unimos todos em uma única caixa
    if len(valid_contours) > 0:
        # Junta todos os arrays de contornos em um só
        all_contours = np.concatenate(valid_contours)

        # Cria um retângulo único que engloba todos os pontos combinados
        (x, y, w, h) = cv2.boundingRect(all_contours)

        # Desenha a caixa unificada na cor verde
        cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Opcional: Escrever um texto indicando a detecção
        cv2.putText(
            frame1,
            'Bolinha Detectada',
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    # Escreve o FPS no canto superior esquerdo da janela (em amarelo)
    cv2.putText(
        frame1,
        f'FPS: {int(fps)}',
        (10, 35),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 255),
        2,
    )

    cv2.imshow('Deteccao de Movimento', frame1)

    frame1 = frame2
    ret, frame2 = cap.read()

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()