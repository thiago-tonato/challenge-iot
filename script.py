import cv2
import numpy as np

#Tamanho do pátio
WIDTH, HEIGHT = 800, 600

#Posição inicial da moto
x, y = 100, 100

#Velocidade da moto
vx, vy = 3, 2

while True:
  # Cria uma imagem preta (o pátio)
  frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

  # Atualiza posição
  x += vx
  y += vy

  # Reflete nos limites do pátio
  if x <= 10 or x >= WIDTH - 10: vx = -vx
  if y <= 10 or y >= HEIGHT - 10: vy = -vy

  # Desenha a "moto" como um círculo vermelho
  cv2.circle(frame, (int(x), int(y)), 10, (0, 0, 255), -1)

  # Mostra coordenadas
  cv2.putText(frame, f"Posicao: ({int(x)}, {int(y)})", (10, 30),
              cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

  # Exibe a imagem
  cv2.imshow("Rastreamento da Moto", frame)

  # Sai com ESC
  key = cv2.waitKey(30)
  if key == 27:
      break
