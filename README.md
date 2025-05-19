# Simulador de Rastreamento de Motos

Este projeto implementa uma simulação simples de rastreamento de múltiplas motos em um ambiente 2D usando OpenCV e NumPy.

## Descrição

O simulador cria uma representação visual de várias motos (cada uma representada por um círculo colorido) que se movem em um "pátio" virtual. As motos se movem com velocidades constantes e refletem nas bordas do ambiente, simulando um movimento de ricochete. O pátio é dividido em um grid 5x5, e o quadrante de cada moto é exibido em tempo real.

## Características

- Visualização em tempo real do movimento de múltiplas motos
- Cada moto possui uma cor diferente
- Exibição do quadrante (5x5) atual de cada moto (ex: A1, C4)
- Movimento automático com reflexão nas bordas
- Interface gráfica usando OpenCV

## Requisitos

- Python 3.x
- OpenCV (cv2)
- NumPy

## Instalação

1. Clone este repositório
2. Instale as dependências necessárias:

```bash
pip install opencv-python numpy
```

## Como Executar

Execute o arquivo `script.py`:

```bash
python script.py
```

## Controles

- Pressione `ESC` para sair da simulação

## Parâmetros Configuráveis

- `WIDTH, HEIGHT`: Dimensões da janela de visualização (800x600 pixels)
- `GRID_ROWS, GRID_COLS`: Número de linhas e colunas do grid (5x5)
- `NUM_MOTOS`: Número de motos simuladas (padrão: 4)
- `cores`: Lista de cores das motos
- `xs, ys`: Posições iniciais das motos
- `vxs, vys`: Velocidades iniciais das motos

## Estrutura do Código

O código principal (`script.py`) contém:

- Inicialização do ambiente de visualização
- Parâmetros de múltiplas motos
- Loop principal de simulação
- Lógica de movimento e reflexão
- Renderização gráfica das motos e exibição dos quadrantes
