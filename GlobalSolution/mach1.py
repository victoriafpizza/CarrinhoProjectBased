#Reinicio do projeto V1
#17/11/2026- o primeiro teste não foi satisfartorio pois o modelos não identifiou corretemente a bolinha de papel.
#o segundo teste demonstrou que o modelo identifica mais facilmente se a bolinha estiver em um fundo escuro.E curiosamente ela identifica 
#qualquer coisa que contraste com o fundo, como uma folha de papel branca, por exemplo.
import cv2
from ultralytics import YOLO

def main():
    # 1. Carregar o modelo
    # Se você já treinou um modelo para bolinhas de papel, substitua 'yolov8n.pt' pelo caminho do seu arquivo (ex: 'runs/detect/train/weights/best.pt')
    # O 'yolov8n.pt' é o modelo nano padrão (rápido para webcam). Ele baixará automaticamente na primeira execução.
    print("Carregando o modelo...")
    model = YOLO("best.pt")

    # 2. Abrir a Webcam do notebook (geralmente o índice 0 é a câmera principal)
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Erro: Não foi possível acessar a webcam.")
        return

    # Ajustar resolução opcional (ex: 640x480 para melhor desempenho)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("Webcam aberta com sucesso! Pressione 'q' para sair.")

    while True:
        # Capturar frame por frame
        ret, frame = cap.read()
        if not ret:
            print("Erro ao capturar o frame da webcam.")
            break

        # 3. Rodar a inferência do modelo no frame atual
        # conf=0.5 define o limiar de confiança mínimo (50%)
        results = model(frame, conf=0.6)

        # 4. Renderizar os resultados desenhando as caixas delimitadoras no frame
        annotated_frame = results[0].plot()

        # 5. Exibir o vídeo em uma janela
        cv2.imshow("Identificador de Bolinhas de Papel - Teste Webcam", annotated_frame)

        # Sair do loop se a tecla 'q' for pressionada
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Liberar a câmera e fechar todas as janelas do OpenCV
    cap.release()
    cv2.destroyAllWindows()
    print("Aplicação encerrada.")

if __name__ == "__main__":
    main()