import cv2
import numpy as np
import string
import oracledb
from datetime import datetime
import threading
import pandas as pd
import plotly.express as px
from flask import Flask, jsonify
from oracle_config import ORACLE_CONFIG, get_dsn, TABLE_NAME, SEQUENCE_NAME

# Configurar modo thick do Oracle (fallback para thin se não disponível)
try:
    oracledb.init_oracle_client()
    print("Usando modo thick do Oracle")
except oracledb.DatabaseError as e:
    if "DPI-1047" in str(e):
        print("Cliente Oracle não encontrado, usando modo thin")
        # Modo thin não precisa de inicialização
    else:
        raise

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 800, 600
GRID_ROWS, GRID_COLS = 5, 5
QUAD_WIDTH = WIDTH // GRID_COLS
QUAD_HEIGHT = HEIGHT // GRID_ROWS
NUM_MOTOS = 4

# ---------------- DATABASE ----------------
def init_db():
    try:
        # Conecta ao Oracle
        conn = oracledb.connect(
            user=ORACLE_CONFIG['user'],
            password=ORACLE_CONFIG['password'],
            dsn=get_dsn()
        )
        cur = conn.cursor()
        
        # Cria a sequência para ID auto-incremento
        cur.execute(f'''
        CREATE SEQUENCE {SEQUENCE_NAME}
        START WITH 1
        INCREMENT BY 1
        NOCACHE
        NOCYCLE
        ''')
        
        # Cria a tabela de detecções
        cur.execute(f'''
        CREATE TABLE {TABLE_NAME} (
            id NUMBER PRIMARY KEY,
            moto_id NUMBER,
            x NUMBER,
            y NUMBER,
            quadrant VARCHAR2(10),
            timestamp TIMESTAMP
        )
        ''')
        
        # Cria trigger para auto-incremento do ID
        cur.execute(f'''
        CREATE OR REPLACE TRIGGER {TABLE_NAME}_trg
        BEFORE INSERT ON {TABLE_NAME}
        FOR EACH ROW
        BEGIN
            IF :NEW.id IS NULL THEN
                :NEW.id := {SEQUENCE_NAME}.NEXTVAL;
            END IF;
        END;
        ''')
        
        conn.commit()
        print("Banco de dados Oracle inicializado com sucesso!")
        return conn
        
    except oracledb.Error as e:
        error, = e.args
        if error.code == 955:  # Tabela já existe
            print("Tabela já existe, conectando...")
            return conn
        elif error.code == 2289:  # Sequência já existe
            print("Sequência já existe, conectando...")
            return conn
        else:
            print(f"Erro ao conectar com Oracle: {e}")
            raise

db_conn = init_db()
db_lock = threading.Lock()

def save_detection(moto_id, x, y, quadrant):
    ts = datetime.utcnow()
    with db_lock:
        cur = db_conn.cursor()
        cur.execute(f"INSERT INTO {TABLE_NAME} (moto_id, x, y, quadrant, timestamp) VALUES (:1, :2, :3, :4, :5)",
                    (moto_id, x, y, quadrant, ts))
        db_conn.commit()

def detections_dataframe(limit=200):
    with db_lock:
        return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME} ORDER BY timestamp DESC FETCH FIRST {limit} ROWS ONLY",
                                 db_conn)

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

        cv2.imshow("Rastreamento das Motos - Oracle", frame)
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
                     symbol="quadrant", title="Posições recentes das motos - Oracle")
    fig.show()

# ---------------- API BACKEND ----------------
app = Flask("motos_api_oracle")

@app.route("/latest")
def latest():
    df = detections_dataframe(50)
    return jsonify(df.to_dict(orient="records"))

# Para rodar API em paralelo:
# threading.Thread(target=lambda: app.run(port=5000, debug=False, use_reloader=False)).start()

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("Iniciando simulação com Oracle Database...")
    print("Pressione ESC para sair")
    run_simulation()
    # Depois de fechar a janela, exibir dashboard:
    plot_dashboard()
