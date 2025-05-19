import cv2
import numpy as np
import string

#Tamanho do pátio
WIDTH, HEIGHT = 800, 600

# Parâmetros do grid
GRID_ROWS, GRID_COLS = 5, 5
QUAD_WIDTH = WIDTH // GRID_COLS
QUAD_HEIGHT = HEIGHT // GRID_ROWS

# Função para obter o quadrante
def get_quadrant(x, y):
    col = min(int(x) // QUAD_WIDTH, GRID_COLS - 1)
    row = min(int(y) // QUAD_HEIGHT, GRID_ROWS - 1)
    label = f"{string.ascii_uppercase[row]}{col+1}"
    return label

# Parâmetros das motos
NUM_MOTOS = 4
cores = [
    (0, 0, 255),    # Vermelho
    (0, 255, 0),    # Verde
    (255, 0, 0),    # Azul
    (0, 255, 255),  # Amarelo
]
# Posições e velocidades iniciais diferentes
xs = [100, 700, 400, 200]
ys = [100, 500, 300, 400]
vxs = [3, -2, 4, -3]
vys = [2, -3, -2, 3]

while True:
    # Cria uma imagem preta (o pátio)
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

    for i in range(NUM_MOTOS):
        # Atualiza posição
        xs[i] += vxs[i]
        ys[i] += vys[i]

        # Reflete nos limites do pátio
        if xs[i] <= 10 or xs[i] >= WIDTH - 10:
            vxs[i] = -vxs[i]
        if ys[i] <= 10 or ys[i] >= HEIGHT - 10:
            vys[i] = -vys[i]

        # Desenha a moto
        cv2.circle(frame, (int(xs[i]), int(ys[i])), 10, cores[i], -1)

        # Mostra quadrante
        quad = get_quadrant(xs[i], ys[i])
        cv2.putText(frame, f"Moto {i+1}: Quadrante {quad}", (10, 30 + i*30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, cores[i], 2)

    # Exibe a imagem
    cv2.imshow("Rastreamento das Motos", frame)

    # Sai com ESC
    key = cv2.waitKey(30)
    if key == 27:
        break
