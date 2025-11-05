import cv2
import numpy as np
import string
import os
import oracledb
from datetime import datetime, timedelta
import threading
import pandas as pd
import warnings
import plotly.express as px
from flask import Flask, jsonify, request
from flask_cors import CORS
from oracle_config import ORACLE_CONFIG, get_dsn, TABLE_NAME, SEQUENCE_NAME

# Suprime warnings do pandas sobre DBAPI2 connections
warnings.filterwarnings("ignore", category=UserWarning, module="pandas")

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
    # Conecta ao Oracle (sempre tenta conectar primeiro)
    try:
        conn = oracledb.connect(
            user=ORACLE_CONFIG["user"],
            password=ORACLE_CONFIG["password"],
            dsn=get_dsn(),
        )
        cur = conn.cursor()

        # Verifica se a tabela existe
        cur.execute(
            f"""
            SELECT COUNT(*) 
            FROM user_tables 
            WHERE table_name = UPPER('{TABLE_NAME}')
        """
        )
        table_exists = cur.fetchone()[0] > 0

        # Verifica se a sequência existe
        cur.execute(
            f"""
            SELECT COUNT(*) 
            FROM user_sequences 
            WHERE sequence_name = UPPER('{SEQUENCE_NAME}')
        """
        )
        sequence_exists = cur.fetchone()[0] > 0

        # Cria a sequência se não existir
        if not sequence_exists:
            try:
                cur.execute(
                    f"""
                CREATE SEQUENCE {SEQUENCE_NAME}
                START WITH 1
                INCREMENT BY 1
                NOCACHE
                NOCYCLE
                """
                )
                print("✅ Sequência criada com sucesso")
            except oracledb.Error as e:
                (error,) = e.args
                if error.code != 2289:  # Ignora se já existe
                    raise
                print("ℹ️  Sequência já existe")
        else:
            print("ℹ️  Sequência já existe")

        # Cria a tabela se não existir
        if not table_exists:
            try:
                cur.execute(
                    f"""
                CREATE TABLE {TABLE_NAME} (
                    id NUMBER PRIMARY KEY,
                    moto_id NUMBER,
                    x NUMBER,
                    y NUMBER,
                    quadrant VARCHAR2(10),
                    status VARCHAR2(20),
                    timestamp TIMESTAMP
                )
                """
                )
                print("✅ Tabela criada com sucesso")
            except oracledb.Error as e:
                (error,) = e.args
                if error.code != 955:  # Ignora se já existe
                    raise
                print("ℹ️  Tabela já existe")
        else:
            print("ℹ️  Tabela já existe")
            # Verifica se a coluna status existe, se não, adiciona
            try:
                cur.execute(
                    f"""
                    SELECT COUNT(*) 
                    FROM user_tab_columns 
                    WHERE table_name = UPPER('{TABLE_NAME}') 
                    AND column_name = 'STATUS'
                    """
                )
                status_column_exists = cur.fetchone()[0] > 0

                if not status_column_exists:
                    cur.execute(f"ALTER TABLE {TABLE_NAME} ADD status VARCHAR2(20)")
                    print("✅ Coluna 'status' adicionada à tabela")
                else:
                    print("ℹ️  Coluna 'status' já existe")
            except oracledb.Error as e:
                (error,) = e.args
                print(f"⚠️  Aviso ao verificar coluna status: {error.message}")

        # Cria ou atualiza o trigger (sempre executa)
        try:
            cur.execute(
                f"""
            CREATE OR REPLACE TRIGGER {TABLE_NAME}_trg
            BEFORE INSERT ON {TABLE_NAME}
            FOR EACH ROW
            BEGIN
                IF :NEW.id IS NULL THEN
                    :NEW.id := {SEQUENCE_NAME}.NEXTVAL;
                END IF;
            END;
            """
            )
        except oracledb.Error as e:
            (error,) = e.args
            print(f"⚠️  Aviso ao criar trigger: {error.message}")

        conn.commit()
        print("✅ Banco de dados Oracle inicializado com sucesso!")
        return conn

    except oracledb.Error as e:
        (error,) = e.args
        print(f"❌ Erro ao conectar com Oracle:")
        print(f"   Código: {error.code}")
        print(f"   Mensagem: {error.message}")
        raise
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        raise


db_conn = init_db()
db_lock = threading.Lock()


def save_detection(moto_id, x, y, quadrant):
    """Salva detecção no banco com status baseado no quadrante"""
    ts = datetime.utcnow()
    status = get_status_from_quadrant(quadrant)
    with db_lock:
        cur = db_conn.cursor()
        cur.execute(
            f"INSERT INTO {TABLE_NAME} (moto_id, x, y, quadrant, status, timestamp) VALUES (:1, :2, :3, :4, :5, :6)",
            (moto_id, x, y, quadrant, status, ts),
        )
        db_conn.commit()


def detections_dataframe(limit=200):
    """Retorna DataFrame com últimas detecções"""
    try:
        with db_lock:
            query = f"SELECT * FROM {TABLE_NAME} ORDER BY timestamp DESC FETCH FIRST {limit} ROWS ONLY"
            df = pd.read_sql_query(query, db_conn)
            return (
                df
                if not df.empty
                else pd.DataFrame(
                    columns=[
                        "id",
                        "moto_id",
                        "x",
                        "y",
                        "quadrant",
                        "status",
                        "timestamp",
                    ]
                )
            )
    except Exception as e:
        print(f"⚠️  Erro ao buscar detecções: {e}")
        return pd.DataFrame(
            columns=["id", "moto_id", "x", "y", "quadrant", "status", "timestamp"]
        )


def get_moto_data(moto_id, limit=100):
    """Obtém dados de uma moto específica"""
    try:
        with db_lock:
            query = f"""
            SELECT * FROM {TABLE_NAME} 
            WHERE moto_id = :1 
            ORDER BY timestamp DESC 
            FETCH FIRST {limit} ROWS ONLY
            """
            df = pd.read_sql_query(query, db_conn, params=[moto_id])
            return (
                df
                if not df.empty
                else pd.DataFrame(
                    columns=[
                        "id",
                        "moto_id",
                        "x",
                        "y",
                        "quadrant",
                        "status",
                        "timestamp",
                    ]
                )
            )
    except Exception as e:
        print(f"⚠️  Erro ao buscar dados da moto {moto_id}: {e}")
        return pd.DataFrame(
            columns=["id", "moto_id", "x", "y", "quadrant", "status", "timestamp"]
        )


def get_stats():
    """Calcula estatísticas gerais do sistema"""
    try:
        with db_lock:
            cur = db_conn.cursor()

            # Total de detecções
            cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
            total_detections = cur.fetchone()[0] or 0

            # Total de motos únicas
            cur.execute(f"SELECT COUNT(DISTINCT moto_id) FROM {TABLE_NAME}")
            unique_motos = cur.fetchone()[0] or 0

            # Detecções por moto
            detections_per_moto = {}
            if total_detections > 0:
                cur.execute(
                    f"""
                    SELECT moto_id, COUNT(*) as count 
                    FROM {TABLE_NAME} 
                    GROUP BY moto_id 
                    ORDER BY moto_id
                """
                )
                detections_per_moto = {
                    int(row[0]): int(row[1]) for row in cur.fetchall()
                }

            # Quadrantes mais visitados
            top_quadrants = []
            if total_detections > 0:
                cur.execute(
                    f"""
                    SELECT quadrant, COUNT(*) as count 
                    FROM {TABLE_NAME} 
                    GROUP BY quadrant 
                    ORDER BY count DESC 
                    FETCH FIRST 5 ROWS ONLY
                """
                )
                top_quadrants = [
                    {"quadrant": row[0], "count": int(row[1])} for row in cur.fetchall()
                ]

            # Última detecção
            last_detection = None
            if total_detections > 0:
                cur.execute(f"SELECT MAX(timestamp) FROM {TABLE_NAME}")
                result = cur.fetchone()[0]
                last_detection = str(result) if result else None

            # Primeira detecção
            first_detection = None
            if total_detections > 0:
                cur.execute(f"SELECT MIN(timestamp) FROM {TABLE_NAME}")
                result = cur.fetchone()[0]
                first_detection = str(result) if result else None

            # Estatísticas por status
            status_stats = {}
            try:
                cur.execute(
                    f"""
                    SELECT status, COUNT(*) as count 
                    FROM {TABLE_NAME} 
                    WHERE status IS NOT NULL
                    GROUP BY status 
                    ORDER BY count DESC
                    """
                )
                status_stats = {row[0]: int(row[1]) for row in cur.fetchall()}
            except Exception:
                # Se coluna status não existe, retorna vazio
                pass

            # Status atual das motos (última detecção de cada moto)
            current_statuses = {}
            for moto_id in range(1, NUM_MOTOS + 1):
                cur.execute(
                    f"""
                    SELECT status FROM (
                        SELECT status 
                        FROM {TABLE_NAME} 
                        WHERE moto_id = :1 
                        ORDER BY timestamp DESC
                    ) WHERE ROWNUM <= 1
                    """,
                    [moto_id],
                )
                result = cur.fetchone()
                if result and result[0]:
                    current_statuses[moto_id] = result[0]
                else:
                    current_statuses[moto_id] = "sem_dados"

            return {
                "total_detections": int(total_detections),
                "unique_motos": int(unique_motos),
                "detections_per_moto": detections_per_moto,
                "top_quadrants": top_quadrants,
                "status_stats": status_stats,
                "current_statuses": current_statuses,
                "last_detection": last_detection,
                "first_detection": first_detection,
            }
    except Exception as e:
        print(f"⚠️  Erro ao calcular estatísticas: {e}")
        return {
            "total_detections": 0,
            "unique_motos": 0,
            "detections_per_moto": {},
            "top_quadrants": [],
            "status_stats": {},
            "current_statuses": {},
            "last_detection": None,
            "first_detection": None,
            "error": str(e),
        }


def get_moto_status(moto_id):
    """Obtém status atual de uma moto específica (baseado no quadrante onde está)"""
    with db_lock:
        cur = db_conn.cursor()

        # Última posição da moto com status
        cur.execute(
            f"""
            SELECT * FROM (
                SELECT x, y, quadrant, status, timestamp 
                FROM {TABLE_NAME} 
                WHERE moto_id = :1 
                ORDER BY timestamp DESC
            ) WHERE ROWNUM <= 1
        """,
            [moto_id],
        )

        last_pos = cur.fetchone()
        if not last_pos:
            return {
                "moto_id": moto_id,
                "status": "not_found",
                "message": "Moto não encontrada",
            }

        x, y, quadrant, status, timestamp = last_pos

        # Se status está NULL, calcula baseado no quadrante
        if status is None:
            status = get_status_from_quadrant(quadrant)
            # Atualiza o registro com o status correto
            cur.execute(
                f"UPDATE {TABLE_NAME} SET status = :1 WHERE moto_id = :2 AND timestamp = :3",
                (status, moto_id, timestamp),
            )
            db_conn.commit()

        # Calcula tempo desde última detecção
        time_diff = datetime.utcnow() - timestamp
        seconds_since_last = time_diff.total_seconds()

        return {
            "moto_id": moto_id,
            "status": status or get_status_from_quadrant(quadrant),
            "position": {"x": float(x), "y": float(y), "quadrant": quadrant},
            "last_update": str(timestamp),
            "seconds_since_last_update": int(seconds_since_last),
        }


def get_all_motos_status():
    """Obtém status de todas as motos"""
    statuses = []
    for moto_id in range(1, NUM_MOTOS + 1):
        statuses.append(get_moto_status(moto_id))
    return statuses


def get_alerts():
    """Gera alertas baseados em condições específicas"""
    alerts = []

    # Verifica status de todas as motos
    statuses = get_all_motos_status()

    for status in statuses:
        moto_id = status["moto_id"]
        moto_status = status.get("status", "desconhecido")
        seconds_since = status.get("seconds_since_last_update", 999)

        # Alerta: Moto em manutenção por muito tempo (pode indicar problema)
        if moto_status == "manutencao" and seconds_since > 60:
            alerts.append(
                {
                    "type": "long_maintenance",
                    "severity": "warning",
                    "moto_id": moto_id,
                    "message": f"Moto {moto_id} em manutenção há {seconds_since} segundos",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Alerta: Moto não atualizada há muito tempo (sistema offline?)
        if seconds_since > 30:
            alerts.append(
                {
                    "type": "stale_data",
                    "severity": "warning",
                    "moto_id": moto_id,
                    "message": f"Moto {moto_id} sem atualização há {seconds_since} segundos",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Alerta: Moto reservada (informação)
        if moto_status == "reservada":
            alerts.append(
                {
                    "type": "reserved",
                    "severity": "info",
                    "moto_id": moto_id,
                    "message": f"Moto {moto_id} está reservada (quadrante {status.get('position', {}).get('quadrant', 'N/A')})",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    return alerts


# ---------------- QUADRANTES ----------------
# Mapeamento de quadrantes para status
QUADRANT_STATUS_MAP = {
    # Colunas 1-2: Em uso
    **{f"{letter}{col}": "em_uso" for letter in "ABCDE" for col in [1, 2]},
    # Coluna 3: No pátio
    **{f"{letter}3": "no_patio" for letter in "ABCDE"},
    # Coluna 4: Em manutenção
    **{f"{letter}4": "manutencao" for letter in "ABCDE"},
    # Coluna 5: Reservada/Indisponível
    **{f"{letter}5": "reservada" for letter in "ABCDE"},
}


def get_quadrant(x, y):
    col = min(int(x) // QUAD_WIDTH, GRID_COLS - 1)
    row = min(int(y) // QUAD_HEIGHT, GRID_ROWS - 1)
    label = f"{string.ascii_uppercase[row]}{col+1}"
    return label


def get_status_from_quadrant(quadrant):
    """Retorna o status baseado no quadrante"""
    return QUADRANT_STATUS_MAP.get(quadrant, "desconhecido")


# ---------------- SIMULAÇÃO ----------------
cores = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
xs = [100, 700, 400, 200]
ys = [100, 500, 300, 400]
vxs = [3, -2, 4, -3]
vys = [2, -3, -2, 3]


def run_simulation():
    """Executa simulação de rastreamento (modo headless para containers)"""
    import time

    # Detecta se há display disponível (para modo gráfico vs headless)
    # Em containers Azure, geralmente não há display disponível
    has_display = False
    if os.environ.get("DISPLAY"):
        try:
            # Tenta detectar se cv2.imshow() funcionaria
            test_frame = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.namedWindow("test", cv2.WINDOW_NORMAL)
            cv2.imshow("test", test_frame)
            cv2.waitKey(1)
            cv2.destroyWindow("test")
            has_display = True
        except Exception:
            has_display = False

    if not has_display:
        print("Modo headless detectado - simulação rodando sem interface gráfica")

    frame_count = 0
    while True:
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)

        # desenha grid
        for r in range(1, GRID_ROWS):
            cv2.line(
                frame,
                (0, r * QUAD_HEIGHT),
                (WIDTH, r * QUAD_HEIGHT),
                (100, 100, 100),
                1,
            )
        for c in range(1, GRID_COLS):
            cv2.line(
                frame, (c * QUAD_WIDTH, 0), (c * QUAD_WIDTH, HEIGHT), (100, 100, 100), 1
            )

        for i in range(NUM_MOTOS):
            xs[i] += vxs[i]
            ys[i] += vys[i]

            # Reflete nas bordas
            if xs[i] <= 10 or xs[i] >= WIDTH - 10:
                vxs[i] = -vxs[i]
            if ys[i] <= 10 or ys[i] >= HEIGHT - 10:
                vys[i] = -vys[i]

            # Desenha moto
            cv2.circle(frame, (int(xs[i]), int(ys[i])), 10, cores[i], -1)

            # Quadrante e status
            quad = get_quadrant(xs[i], ys[i])
            status = get_status_from_quadrant(quad)

            # Mapeia status para cores de texto
            status_colors = {
                "em_uso": (0, 255, 0),  # Verde
                "no_patio": (255, 255, 0),  # Amarelo
                "manutencao": (0, 165, 255),  # Laranja
                "reservada": (128, 0, 128),  # Roxo
                "desconhecido": (255, 255, 255),  # Branco
            }
            status_color = status_colors.get(status, (255, 255, 255))

            # Exibe informação na tela (se houver display)
            if has_display:
                cv2.putText(
                    frame,
                    f"Moto {i+1}: {quad} - {status.upper()}",
                    (10, 30 + i * 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    status_color,
                    2,
                )

            # Salva no banco com status
            save_detection(i + 1, xs[i], ys[i], quad)

        # Apenas mostra janela se houver display disponível
        if has_display:
            cv2.imshow("Rastreamento das Motos - Oracle", frame)
            key = cv2.waitKey(30) & 0xFF
            if key == 27:  # ESC para sair
                break
        else:
            # Modo headless: apenas espera um pouco e continua
            time.sleep(0.03)  # ~30ms equivalente ao waitKey(30)
            frame_count += 1
            # Log a cada 100 frames para não poluir logs
            if frame_count % 100 == 0:
                print(f"Simulação rodando... {frame_count} frames processados")

    if has_display:
        cv2.destroyAllWindows()


# ---------------- DASHBOARD ----------------
def plot_dashboard():
    df = detections_dataframe(500)
    if df.empty:
        print("Nenhum dado coletado ainda.")
        return

    # Normaliza nomes das colunas para minúsculas (Oracle retorna em maiúsculas)
    df.columns = df.columns.str.lower()

    # Usa status para colorir se disponível, senão usa moto_id
    if "status" in df.columns:
        fig = px.scatter(
            df,
            x="x",
            y="y",
            color="status",
            symbol="moto_id",
            title="Posições recentes das motos por Status - Oracle",
            labels={"status": "Status", "moto_id": "Moto ID"},
        )
    else:
        fig = px.scatter(
            df,
            x="x",
            y="y",
            color="moto_id",
            symbol="quadrant",
            title="Posições recentes das motos - Oracle",
        )
    fig.show()


# ---------------- API BACKEND ----------------
app = Flask("motos_api_oracle")
CORS(app)  # Habilita CORS para integrações


@app.route("/")
def index():
    """Endpoint raiz com informações da API"""
    return jsonify(
        {
            "name": "Motos IoT Tracking API",
            "version": "1.0",
            "endpoints": {
                "/latest": "GET - Últimas detecções",
                "/stats": "GET - Estatísticas gerais",
                "/moto/<id>": "GET - Dados de uma moto específica",
                "/status": "GET - Status de todas as motos",
                "/status/<id>": "GET - Status de uma moto específica",
                "/alerts": "GET - Alertas em tempo real",
                "/health": "GET - Health check",
            },
        }
    )


@app.route("/health")
def health():
    """Health check do sistema"""
    try:
        with db_lock:
            cur = db_conn.cursor()
            cur.execute("SELECT 1 FROM DUAL")
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify(
        {
            "status": "healthy" if db_status == "connected" else "degraded",
            "database": db_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@app.route("/latest")
def latest():
    """Últimas detecções"""
    limit = request.args.get("limit", default=50, type=int)
    if limit > 500:
        limit = 500  # Limite máximo
    df = detections_dataframe(limit)
    return jsonify(df.to_dict(orient="records"))


@app.route("/stats")
def stats():
    """Estatísticas gerais do sistema"""
    try:
        stats_data = get_stats()
        return jsonify(stats_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/moto/<int:moto_id>")
def moto(moto_id):
    """Dados de uma moto específica"""
    if moto_id < 1 or moto_id > NUM_MOTOS:
        return jsonify({"error": f"Moto ID deve estar entre 1 e {NUM_MOTOS}"}), 400

    limit = request.args.get("limit", default=100, type=int)
    if limit > 1000:
        limit = 1000  # Limite máximo

    try:
        df = get_moto_data(moto_id, limit)
        if df.empty:
            return jsonify(
                {"moto_id": moto_id, "message": "Nenhum dado encontrado", "data": []}
            )
        return jsonify(
            {
                "moto_id": moto_id,
                "total_records": len(df),
                "data": df.to_dict(orient="records"),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def status_all():
    """Status de todas as motos"""
    try:
        statuses = get_all_motos_status()
        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_motos": len(statuses),
                "motos": statuses,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/status/<int:moto_id>")
def status_moto(moto_id):
    """Status de uma moto específica"""
    if moto_id < 1 or moto_id > NUM_MOTOS:
        return jsonify({"error": f"Moto ID deve estar entre 1 e {NUM_MOTOS}"}), 400

    try:
        status = get_moto_status(moto_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/alerts")
def alerts():
    """Alertas em tempo real"""
    try:
        alerts_data = get_alerts()
        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_alerts": len(alerts_data),
                "alerts": alerts_data,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/dashboard")
def dashboard():
    """Dashboard web desenhado no navegador (funciona no App Service)."""
    return (
        """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Motos IoT - Dashboard</title>
  <style>
    :root { --w: 800px; --h: 600px; }
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 0; background: #0b1020; color: #e6e9f0; }
    header { padding: 12px 16px; border-bottom: 1px solid #2a3350; display: flex; align-items: center; gap: 12px; }
    header h1 { font-size: 16px; font-weight: 600; margin: 0; }
    .container { display: grid; grid-template-columns: var(--w) 1fr; gap: 20px; padding: 16px; }
    .card { background: #0f162b; border: 1px solid #2a3350; border-radius: 10px; padding: 12px; }
    .canvas-wrap { position: relative; width: var(--w); height: var(--h); }
    canvas { width: var(--w); height: var(--h); background: #0a0f1f; border-radius: 8px; display: block; }
    .legend { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; font-size: 12px; }
    .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; vertical-align: middle; }
    .kpi { display: grid; grid-template-columns: repeat(2, minmax(120px, 1fr)); gap: 10px; }
    .kpi-item { background: #0b1326; border: 1px solid #223055; border-radius: 8px; padding: 10px; }
    .kpi-item .label { color: #9fb0d6; font-size: 11px; }
    .kpi-item .value { font-size: 18px; font-weight: 600; margin-top: 4px; }
    a { color: #8ab4ff; text-decoration: none; }
  </style>
</head>
<body>
  <header>
    <h1>🏍️ Motos IoT - Dashboard</h1>
    <div style="opacity:.8">API: <a href="/" target="_blank">/</a> · Health: <a href="/health" target="_blank">/health</a></div>
  </header>

  <div class="container">
    <div class="card">
      <div class="canvas-wrap">
        <canvas id="board" width="800" height="600"></canvas>
      </div>
      <div class="legend">
        <span><span class="dot" style="background:#ff5555"></span>Moto 1</span>
        <span><span class="dot" style="background:#22cc88"></span>Moto 2</span>
        <span><span class="dot" style="background:#4aa3ff"></span>Moto 3</span>
        <span><span class="dot" style="background:#00e5e5"></span>Moto 4</span>
        <span>·</span>
        <span><span class="dot" style="background:#22cc88"></span>em_uso</span>
        <span><span class="dot" style="background:#ffd166"></span>no_patio</span>
        <span><span class="dot" style="background:#ff8c42"></span>manutencao</span>
        <span><span class="dot" style="background:#a78bfa"></span>reservada</span>
      </div>
    </div>

    <div class="card">
      <div class="kpi">
        <div class="kpi-item">
          <div class="label">Total de detecções</div>
          <div class="value" id="kpi-total">-</div>
        </div>
        <div class="kpi-item">
          <div class="label">Motos únicas</div>
          <div class="value" id="kpi-uniq">-</div>
        </div>
        <div class="kpi-item">
          <div class="label">Última atualização</div>
          <div class="value" id="kpi-last">-</div>
        </div>
        <div class="kpi-item">
          <div class="label">Status (1→4)</div>
          <div class="value" id="kpi-status">-</div>
        </div>
      </div>
      <div style="margin-top:10px;color:#9fb0d6;font-size:12px">Atualiza a cada ~500 ms. Dados via <code>/status</code> e <code>/stats</code>.</div>
    </div>
  </div>

  <script>
    const WIDTH = 800, HEIGHT = 600, ROWS = 5, COLS = 5;
    const QUAD_W = Math.floor(WIDTH / COLS), QUAD_H = Math.floor(HEIGHT / ROWS);
    const motoColors = ["#ff5555", "#22cc88", "#4aa3ff", "#00e5e5"]; // 1..4
    const statusColors = { em_uso: "#22cc88", no_patio: "#ffd166", manutencao: "#ff8c42", reservada: "#a78bfa", desconhecido: "#e6e9f0" };

    const canvas = document.getElementById('board');
    const ctx = canvas.getContext('2d');

    function drawGrid() {
      ctx.clearRect(0,0,WIDTH,HEIGHT);
      ctx.fillStyle = "#0a0f1f"; ctx.fillRect(0,0,WIDTH,HEIGHT);
      ctx.strokeStyle = "#2a3350"; ctx.lineWidth = 1;
      for (let r=1; r<ROWS; r++) { ctx.beginPath(); ctx.moveTo(0, r*QUAD_H); ctx.lineTo(WIDTH, r*QUAD_H); ctx.stroke(); }
      for (let c=1; c<COLS; c++) { ctx.beginPath(); ctx.moveTo(c*QUAD_W, 0); ctx.lineTo(c*QUAD_W, HEIGHT); ctx.stroke(); }
      // labels A1..E5
      ctx.fillStyle = "#7085b6"; ctx.font = "12px system-ui";
      for (let r=0; r<ROWS; r++) {
        for (let c=0; c<COLS; c++) {
          const label = String.fromCharCode(65 + r) + (c+1);
          ctx.fillText(label, c*QUAD_W + 6, r*QUAD_H + 16);
        }
      }
    }

    function drawMotos(motos) {
      motos.forEach((m, idx) => {
        const x = (m.position && m.position.x != null) ? m.position.x : 0;
        const y = (m.position && m.position.y != null) ? m.position.y : 0;
        const status = m.status || 'desconhecido';
        // trail shadow
        ctx.beginPath(); ctx.arc(x, y, 16, 0, Math.PI*2); ctx.fillStyle = "rgba(255,255,255,0.05)"; ctx.fill();
        // main dot
        ctx.beginPath(); ctx.arc(x, y, 10, 0, Math.PI*2); ctx.fillStyle = motoColors[(m.moto_id-1)%motoColors.length]; ctx.fill();
        // status ring
        ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI*2); ctx.strokeStyle = statusColors[status] || "#e6e9f0"; ctx.lineWidth = 3; ctx.stroke();
        // label
        ctx.fillStyle = "#e6e9f0"; ctx.font = "12px system-ui";
        ctx.fillText(`Moto ${m.moto_id} · ${status}`, x + 14, y - 12);
      });
    }

    async function refresh() {
      try {
        const [statusRes, statsRes] = await Promise.all([
          fetch('/status', { cache: 'no-store' }),
          fetch('/stats', { cache: 'no-store' })
        ]);
        const statusJson = await statusRes.json();
        const statsJson = await statsRes.json();

        drawGrid();
        if (statusJson && Array.isArray(statusJson.motos)) {
          drawMotos(statusJson.motos);
          const ordered = statusJson.motos.sort((a,b)=>a.moto_id-b.moto_id).map(m=>m.status || '—');
          document.getElementById('kpi-status').textContent = ordered.join(' | ');
        }

        document.getElementById('kpi-total').textContent = (statsJson.total_detections ?? 0).toString();
        document.getElementById('kpi-uniq').textContent = (statsJson.unique_motos ?? 0).toString();
        document.getElementById('kpi-last').textContent = statsJson.last_detection ? new Date(statsJson.last_detection).toLocaleTimeString() : '—';
      } catch (e) {
        // simple error indicator
        ctx.fillStyle = "#ff5555"; ctx.font = "14px system-ui";
        ctx.fillText("Erro ao carregar dados", 10, HEIGHT - 10);
      }
    }

    drawGrid();
    refresh();
    setInterval(refresh, 600); // ~600ms
  </script>
</body>
</html>
        """,
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


def run_api():
    """Executa a API Flask em thread separada"""
    # Porta do Azure ou padrão 5000
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Iniciando API Flask na porta {port}...")
    print("📡 Endpoints disponíveis:")
    print(f"   GET http://localhost:{port}/")
    print(f"   GET http://localhost:{port}/health")
    print(f"   GET http://localhost:{port}/latest")
    print(f"   GET http://localhost:{port}/stats")
    print(f"   GET http://localhost:{port}/moto/<id>")
    print(f"   GET http://localhost:{port}/status")
    print(f"   GET http://localhost:{port}/status/<id>")
    print(f"   GET http://localhost:{port}/alerts")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ---------------- INICIALIZAÇÃO AUTOMÁTICA ----------------
# Inicia a simulação em thread daemon quando o módulo é importado
# Isso permite que funcione tanto com Gunicorn quanto com execução direta
_simulation_thread = None
_simulation_started = False


def _start_simulation_background():
    """Inicia a simulação em uma thread daemon (para Gunicorn/App Service)"""
    global _simulation_thread, _simulation_started
    if _simulation_started:
        return

    _simulation_started = True
    print("🚀 Iniciando simulação de rastreamento em background...")
    _simulation_thread = threading.Thread(target=run_simulation, daemon=True)
    _simulation_thread.start()
    print("✅ Simulação iniciada em thread daemon")


# Inicia automaticamente quando o módulo é importado
_start_simulation_background()


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("=" * 60)
    print("🏍️  SISTEMA DE RASTREAMENTO DE MOTOS - MOTTU")
    print("=" * 60)

    # Simulação já está rodando em thread daemon (iniciada automaticamente)
    # Aqui apenas iniciamos a API Flask para execução direta
    print("✅ Simulação já está rodando em background")
    print()

    print("Iniciando API Flask...")
    print("Pressione Ctrl+C para sair")
    print("-" * 60)

    try:
        # Executa API Flask diretamente (não em thread quando executado diretamente)
        port = int(os.environ.get("PORT", 5000))
        print(f"🌐 Iniciando API Flask na porta {port}...")
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n⏹️  Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro na API: {e}")
        import traceback

        traceback.print_exc()
    finally:
        print("🔄 Finalizando sistema...")
        # Não tenta exibir dashboard em modo headless (containers)
        try:
            if os.environ.get("DISPLAY"):
                print("📊 Exibindo dashboard...")
                plot_dashboard()
        except Exception as e:
            print(f"⚠️  Dashboard não disponível (modo headless): {e}")
        print("✅ Sistema finalizado")
