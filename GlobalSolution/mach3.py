#codigo para a identificação de movimento, utilizando a webcam do notebook.
#o Teste 4 foi muito satisfatorio e estou pensando em usalo mas tem uma questão, como aplicar a IA nisso 
#mas tendo o problema resolvido em parte já é gratificante 
import cv2

# Inicializa a webcam (0 é a câmera padrão do notebook)
cap = cv2.VideoCapture(0)

# Lê o primeiro quadro
ret, frame1 = cap.read()
ret, frame2 = cap.read()

while cap.isOpened():
  # Calcula a diferença entre dois quadros seguidos
  diff = cv2.absdiff(frame1, frame2)

  # Converte a diferença para escala de cinza
  gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

  # Aplica um desfoque para suavizar o ruído
  blur = cv2.GaussianBlur(gray, (5, 5), 0)

  # Aplica limiarização (threshold) para destacar as áreas com mudança
  _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)

  # Dilata a imagem para preencher buracos no objeto em movimento
  dilated = cv2.dilate(thresh, None, iterations=3)

  # Encontra os contornos da área que se moveu
  contours, _ = cv2.findContours(
      dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
  )

  for contour in contours:
    if cv2.contourArea(contour) < 500:  # Ignora movimentos muito pequenos (ruído)
      continue
    (x, y, w, h) = cv2.boundingRect(contour)
    # Desenha um retângulo verde em volta do objeto em movimento
    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 2)

  # Mostra o vídeo na tela
  cv2.imshow('Detecção de Movimento', frame1)

  frame1 = frame2
  ret, frame2 = cap.read()

  # Pressione 'q' para sair do loop
  if cv2.waitKey(10) & 0xFF == ord('q'):
    break

cap.release()
cv2.destroyAllWindows()

