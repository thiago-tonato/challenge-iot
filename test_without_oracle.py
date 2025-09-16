#!/usr/bin/env python3
"""
Script de demonstração que simula o funcionamento sem Oracle Database
"""

import cv2
import numpy as np
import string
from datetime import datetime
import threading
import pandas as pd
import plotly.express as px
from flask import Flask, jsonify

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
GRID_ROWS, GRID_COLS = 5, 5
QUAD_WIDTH = WIDTH // GRID_COLS
QUAD_HEIGHT = HEIGHT // GRID_ROWS
NUM_MOTOS = 4

# ---------------- SIMULAÇÃO DE DADOS ----------------
# Em vez de Oracle, vamos usar uma lista em memória para demonstração
detections_data = []
db_lock = threading.Lock()

def save_detection(moto_id, x, y, quadrant):
    """Simula o salvamento no banco de dados"""
    ts = datetime.utcnow()
    with db_lock:
        detection = {
            'id': len(detections_data) + 1,
            'moto_id': moto_id,
            'x': x,
            'y': y,
            'quadrant': quadrant,
            'timestamp': ts
        }
        detections_data.append(detection)
        print(f"Salvo: Moto {moto_id} em ({x:.1f}, {y:.1f}) - Quadrante {quadrant}")

def detections_dataframe(limit=200):
    """Simula a consulta ao banco de dados"""
    with db_lock:
        df = pd.DataFrame(detections_data[-limit:])
        return df

# ---------------- QUADRANTES ----------------
def get_quadrant(x, y):
    col = min(int(x) // QUAD_WIDTH, GRID_COLS - 1)
    row = min(int(y) // QUAD_HEIGHT, GRID_ROWS - 1)
    label = f"{string.ascii_uppercase[row]}{col+1}"
    return label

# ---------------- SIMULAÇÃO ----------------
cores = [(0,0,255), (0,255,0), (255,0,0), (0,255,255)]
xs = [100, 700, 400, 200]
ys = [100, 500, 300, 400]
vxs = [3, -2, 4, -3]
vys = [2, -3, -2, 3]

def run_simulation():
    frame_count = 0
    while True:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        # desenha grid
        for r in range(1, GRID_ROWS):
            cv2.line(frame, (0, r*QUAD_HEIGHT), (WIDTH, r*QUAD_HEIGHT), (100,100,100), 1)
        for c in range(1, GRID_COLS):
            cv2.line(frame, (c*QUAD_WIDTH, 0), (c*QUAD_WIDTH, HEIGHT), (100,100,100), 1)

        for i in range(NUM_MOTOS):
            xs[i] += vxs[i]
            ys[i] += vys[i]

            # Reflete nas bordas
            if xs[i] <= 10 or xs[i] >= WIDTH - 10: vxs[i] = -vxs[i]
            if ys[i] <= 10 or ys[i] >= HEIGHT - 10: vys[i] = -vys[i]

            # Desenha moto
            cv2.circle(frame, (int(xs[i]), int(ys[i])), 10, cores[i], -1)

            # Quadrante
            quad = get_quadrant(xs[i], ys[i])
            cv2.putText(frame, f"Moto {i+1}: Quadrante {quad}", (10, 30 + i*30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, cores[i], 2)

            # Salva no banco (simulado)
            save_detection(i+1, xs[i], ys[i], quad)

        # Mostra estatísticas
        cv2.putText(frame, f"Registros: {len(detections_data)}", (10, HEIGHT - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {frame_count}", (10, HEIGHT - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Rastreamento das Motos - Demo (Sem Oracle)", frame)
        key = cv2.waitKey(30)
        if key == 27: break  # ESC para sair
        
        frame_count += 1
        
        # Para demonstração, limitar a 100 frames
        if frame_count >= 100:
            print("Demonstração concluída (100 frames)")
            break

    cv2.destroyAllWindows()

# ---------------- DASHBOARD ----------------
def plot_dashboard():
    df = detections_dataframe(500)
    if df.empty:
        print("Nenhum dado coletado ainda.")
        return
    
    print(f"\nTotal de registros coletados: {len(detections_data)}")
    print("Últimos 5 registros:")
    for i, record in enumerate(detections_data[-5:]):
        print(f"  {i+1}. Moto {record['moto_id']} - Pos: ({record['x']:.1f}, {record['y']:.1f}) - Quadrante: {record['quadrant']}")
    
    # Criar gráfico se houver dados suficientes
    if len(df) > 10:
        fig = px.scatter(df, x="x", y="y", color="moto_id",
                         symbol="quadrant", title="Posições das motos - Demo")
        fig.show()
    else:
        print("Dados insuficientes para gerar gráfico")

# ---------------- API BACKEND ----------------
app = Flask("motos_api_demo")

@app.route("/latest")
def latest():
    df = detections_dataframe(50)
    return jsonify(df.to_dict(orient="records"))

@app.route("/stats")
def stats():
    return jsonify({
        "total_detections": len(detections_data),
        "unique_motos": len(set(d['moto_id'] for d in detections_data)),
        "quadrants_used": len(set(d['quadrant'] for d in detections_data))
    })

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("=== DEMONSTRAÇÃO DO SISTEMA DE RASTREAMENTO ===")
    print("Este script demonstra o funcionamento sem Oracle Database")
    print("Os dados são armazenados em memória para demonstração")
    print("Pressione ESC para sair ou aguarde 100 frames")
    print("-" * 50)
    
    run_simulation()
    
    # Depois de fechar a janela, exibir dashboard:
    plot_dashboard()
    
    print("\n=== ESTATÍSTICAS FINAIS ===")
    print(f"Total de detecções: {len(detections_data)}")
    
    # Análise por moto
    for moto_id in range(1, NUM_MOTOS + 1):
        moto_data = [d for d in detections_data if d['moto_id'] == moto_id]
        print(f"Moto {moto_id}: {len(moto_data)} detecções")
    
    # Análise por quadrante
    quadrants = {}
    for d in detections_data:
        quad = d['quadrant']
        quadrants[quad] = quadrants.get(quad, 0) + 1
    
    print("\nOcupação por quadrante:")
    for quad in sorted(quadrants.keys()):
        print(f"  {quad}: {quadrants[quad]} detecções")
