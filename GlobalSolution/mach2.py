#V2
#agora com contagem de FPS usando a Webcam e contagem de FPS do YOLO 
#o terceiro teste demonstrou que o modelo ainda possui dificuldade em identificar a bolinha isso me gerou uma ideia:
#eu posso usar a IA para tentar identificar a bolinha e então usar o HSV para a trajetoria e o acompanhamento dela
import time
import cv2
from ultralytics import YOLO

def main():
    # 1. Carregar o modelo (substitua pelo seu modelo customizado se tiver)
    print("Carregando o modelo...")
    model = YOLO("best.pt")

    # 2. Abrir a Webcam do notebook
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    # Ajustar resolução padrão
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Webcam aberta com sucesso! Pressione 'q' para sair.")

    # Variáveis para o cálculo de FPS
    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar o frame da webcam.")
            break

        # 3. Rodar a inferência sem poluir o terminal (verbose=False)
        results = model(frame, conf=0.5, verbose=False)

        # 4. Renderizar as caixas delimitadoras
        annotated_frame = results[0].plot()

        # 5. Cálculo do FPS em tempo real
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if prev_time > 0 else 0
        prev_time = current_time

        # Escrever o valor do FPS na tela (canto superior esquerdo)
        cv2.putText(
            annotated_frame, 
            f"FPS: {int(fps)}", 
            (20, 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            1, 
            (0, 255, 0),  # Cor verde
            2, 
            cv2.LINE_AA
        )

        # 6. Exibir o vídeo limpo
        cv2.imshow("Identificador de Bolinhas de Papel", annotated_frame)

        # Sair do loop se a tecla 'q' for pressionada
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Aplicação encerrada.")

if __name__ == "__main__":
    main()