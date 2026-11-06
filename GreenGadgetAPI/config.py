import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega as configurações do ficheiro .env
load_dotenv(Path(__file__).with_name(".env"))

# Configuração PostgreSQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", ""),
    "port": int(os.getenv("DB_PORT", "")),
    "dbname": os.getenv("DB_NAME", ""),
    "user": os.getenv("DB_USER", ""),
    "password": os.getenv("DB_PASSWORD", ""),
    "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
}

# Configuração da API
API_BASE_URL = os.getenv(
    "API_BASE_URL",
    ""
).rstrip("/")

API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))

# Modo de simulação
DRY_RUN = os.getenv(
    "AGENT_DRY_RUN",
    "true"
).strip().lower() in {
    "1", "true", "yes", "sim", "on"
}

# Configurações do agente
INTERVALO_SEGUNDOS = int(
    os.getenv("AGENT_INTERVAL_SECONDS", "300")
)

JANELA_HORAS = 24

LIMIAR_REGA = float(
    os.getenv("AGENT_WATERING_THRESHOLD", "70")
)

IDADE_MAXIMA_LEITURA_MINUTOS = int(
    os.getenv("AGENT_MAX_READING_AGE_MINUTES", "30")
)