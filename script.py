import cv2
import numpy as np
import string
import sqlite3
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
DB_PATH = "motos.sqlite"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        moto_id INTEGER,
        x REAL,
        y REAL,
        quadrant TEXT,
        timestamp TEXT
    )
    ''')
    conn.commit()
    return conn

db_conn = init_db()
db_lock = threading.Lock()

def save_detection(moto_id, x, y, quadrant):
    ts = datetime.utcnow().isoformat()
    with db_lock:
        cur = db_conn.cursor()
        cur.execute("INSERT INTO detections (moto_id, x, y, quadrant, timestamp) VALUES (?,?,?,?,?)",
                    (moto_id, x, y, quadrant, ts))
        db_conn.commit()

def detections_dataframe(limit=200):
    with db_lock:
        return pd.read_sql_query("SELECT * FROM detections ORDER BY timestamp DESC LIMIT ?",
                                 db_conn, params=(limit,))

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

            # Salva no banco
            save_detection(i+1, xs[i], ys[i], quad)

        cv2.imshow("Rastreamento das Motos", frame)
        key = cv2.waitKey(30)
        if key == 27: break  # ESC para sair

    cv2.destroyAllWindows()

# ---------------- DASHBOARD ----------------
def plot_dashboard():
    df = detections_dataframe(500)
    if df.empty:
        print("Nenhum dado coletado ainda.")
        return
    fig = px.scatter(df, x="x", y="y", color="moto_id",
                     symbol="quadrant", title="Posições recentes das motos")
    fig.show()

# ---------------- API BACKEND ----------------
app = Flask("motos_api")

@app.route("/latest")
def latest():
    df = detections_dataframe(50)
    return jsonify(df.to_dict(orient="records"))

# Para rodar API em paralelo:
# threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False)).start()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    run_simulation()
    # Depois de fechar a janela, exibir dashboard:
    plot_dashboard()
