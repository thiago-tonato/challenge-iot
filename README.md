# Simulador de Rastreamento de Moto

Este projeto implementa uma simulação simples de rastreamento de uma moto em um ambiente 2D usando OpenCV e NumPy.

## Descrição

O simulador cria uma representação visual de uma moto (representada por um círculo vermelho) que se move em um "pátio" virtual. A moto se move com velocidade constante e reflete nas bordas do ambiente, simulando um movimento de ricochete.

## Características

- Visualização em tempo real do movimento da moto
- Exibição das coordenadas atuais da moto
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
- `x, y`: Posição inicial da moto (100, 100)
- `vx, vy`: Velocidade da moto (3, 2 pixels por frame)

## Estrutura do Código

O código principal (`script.py`) contém:

- Inicialização do ambiente de visualização
- Loop principal de simulação
- Lógica de movimento e reflexão
- Renderização gráfica
