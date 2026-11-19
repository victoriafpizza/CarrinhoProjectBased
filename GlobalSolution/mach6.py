#codigo que intrega a identificação de movimento com a IA, utilizando a webcam do notebook com FPS em tempo real.
#o sexto teste não ocorreu como o esperado, a IA não consegue identificar a bolinha em movimento
#mas não posso negar que isso ajudou na queda de FPS, então estou pensando no que posso fazer 
# SETIMO teste demonstrou melhora, quando a bolinha esta no topo onde a velocidade é 0 a IA consegue identificar a bolinha.
import time
import cv2
import numpy as np
from ultralytics import YOLO

def main():
    # 1. Carregar o modelo YOLOv8
    # Se treinou um modelo próprio para bolinhas de papel, substitua 'yolov8n.pt' pelo caminho (ex: 'runs/detect/train/weights/best.pt')
    print("Carregando o modelo YOLOv8...")
    model = YOLO("best.pt")

    # 2. Abrir a Webcam do notebook
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    # Ajustar resolução para melhor desempenho
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Webcam aberta com sucesso! Pressione 'q' para sair.")

    ret, frame1 = cap.read()
    ret, frame2 = cap.read()
    prev_frame_time = 0

    while cap.isOpened():
        if not ret:
            print("Erro ao capturar o frame da webcam.")
            break

        # --- Cálculo do FPS ---
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time) if prev_frame_time > 0 else 0
        prev_frame_time = new_frame_time
        # ----------------------

        # --- Detecção de Movimento (OpenCV) ---
        diff = cv2.absdiff(frame1, frame2)
        gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        valid_contours = []
        for contour in contours:
            if cv2.contourArea(contour) < 500:
                continue
            valid_contours.append(contour)

        # Copiar o frame atual para exibição
        annotated_frame = frame2.copy()

        # Se houver movimento válido, unimos em uma caixa e rodamos a IA apenas nela
        if len(valid_contours) > 0:
            all_contours = np.concatenate(valid_contours)
            (x, y, w, h) = cv2.boundingRect(all_contours)

            # Garantir que a caixa fique dentro dos limites da tela
            h_img, w_img, _ = frame2.shape
            x = max(0, x)
            y = max(0, y)
            w = min(w_img - x, w)
            h = min(h_img - y, h)

            if w > 10 and h > 10:
                # Recorta apenas a região onde houve movimento (ROI)
                roi = frame2[y:y+h, x:x+w]

                # --- 3. Rodar inferência do YOLOv8 APENAS na caixa de movimento ---
                results = model(roi, conf=0.5, verbose=False)

                # Verificar se a IA encontrou objetos dentro do recorte
                for r in results:
                    boxes = r.boxes
                    if len(boxes) > 0:
                        print("Bolinha identificada!") # Print solicitado no sistema

                        # Desenhar as caixas do YOLO ajustando para as coordenadas da tela principal
                        for box in boxes:
                            bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            class_name = model.names[cls]

                            # Converter coordenadas locais do ROI para o frame global
                            gx1 = bx1 + x
                            gy1 = by1 + y
                            gx2 = bx2 + x
                            gy2 = by2 + y

                            # Desenhar o retângulo e o rótulo da IA na tela
                            cv2.rectangle(annotated_frame, (gx1, gy1), (gx2, gy2), (0, 255, 0), 2)
                            label = f"{class_name} ({conf:.2f})"
                            cv2.putText(annotated_frame, label, (gx1, max(20, gy1 - 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Escrever o FPS no canto superior esquerdo (em amarelo)
        cv2.putText(annotated_frame, f'FPS: {int(fps)}', (10, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        # 4. Exibir o vídeo processado
        cv2.imshow("Deteccao Inteligente - YOLOv8 + Movimento", annotated_frame)

        # Atualizar quadros para o próximo ciclo
        frame1 = frame2
        ret, frame2 = cap.read()

        # Sair ao pressionar 'q'
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Aplicação encerrada.")

if __name__ == "__main__":
    main()