
import psycopg

# Configuração PostgreSQL.
# Mantém aqui as credenciais que já colocaste no projeto.
DB_CONFIG = {
    "host": "",
    "port": 5432,
    "dbname": "",
    "user": "",
    "password": "",
    "connect_timeout": 10,
}


def get_connection():
    return psycopg.connect(**DB_CONFIG)


def obter_ultimas_leituras():
    query = """
        SELECT DISTINCT ON (d.id)
            d.id AS device_id,
            d.plant_id,
            sd.id AS sensor_id,
            sd.timestamp,
            sd.temperature,
            sd.air_humidity,
            sd.soil_humidity
        FROM devices d
        INNER JOIN sensor_data sd ON sd.device_id = d.id
        WHERE d.plant_id IS NOT NULL
        ORDER BY d.id, sd.timestamp DESC, sd.id DESC
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            columns = [c.name for c in cur.description]
            return [
                dict(zip(columns, row))
                for row in cur.fetchall()
            ]


def obter_planta(plant_id):
    query = """
        SELECT
            id,
            name,
            min_soil_humidity,
            max_soil_humidity,
            min_air_temperature,
            max_air_temperature,
            min_air_humidity,
            max_air_humidity,
            watering_duration_seconds,
            watering_cooldown_hours,
            heat_stress_air_temperature,
            heat_stress_watering_duration_seconds
        FROM plants
        WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (plant_id,))
            row = cur.fetchone()

            if row is None:
                return None

            columns = [c.name for c in cur.description]
            return dict(zip(columns, row))


def obter_previsao_media(device_id):
    """
    Seleciona a previsão do IPMA cuja temperatura média
    mais se aproxima da temperatura média do dispositivo
    nas últimas 24 horas.
    """

    query = """
        WITH media_sensor AS (
            SELECT AVG(sd.temperature) AS temperatura_media
            FROM sensor_data sd
            WHERE sd.device_id = %s
              AND sd.timestamp >=
                  CURRENT_TIMESTAMP - INTERVAL '24 hours'
              AND sd.temperature IS NOT NULL
        ),
        previsoes AS (
            SELECT DISTINCT ON (global_id_local)
                global_id_local,
                location_name,
                forecast_date,
                temperature_min,
                temperature_max,
                precipitation_probability
            FROM ipma
            WHERE forecast_date >= CURRENT_DATE
            ORDER BY
                global_id_local,
                forecast_date ASC,
                updated_at DESC
        )
        SELECT
            p.location_name,
            p.temperature_min,
            p.temperature_max,
            p.precipitation_probability,
            m.temperatura_media
        FROM previsoes p
        CROSS JOIN media_sensor m
        ORDER BY
            CASE
                WHEN m.temperatura_media IS NULL THEN 0
                ELSE ABS(
                    ((p.temperature_min + p.temperature_max) / 2)
                    - m.temperatura_media
                )
            END,
            p.location_name
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (device_id,))
            row = cur.fetchone()

            if row is None:
                return {
                    "location_name": None,
                    "temperature_max": None,
                    "precipitation_probability": None,
                }

            return {
                "location_name": row[0],
                "temperature_min": (
                    float(row[1]) if row[1] is not None else None
                ),
                "temperature_max": (
                    float(row[2]) if row[2] is not None else None
                ),
                "precipitation_probability": (
                    float(row[3]) if row[3] is not None else None
                ),
                "sensor_temperature_average": (
                    float(row[4]) if row[4] is not None else None
                ),
            }


def obter_modulo_rega(device_id):
    query = """
        SELECT id
        FROM watering_devices
        WHERE device_id = %s
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (device_id,))
            row = cur.fetchone()

    return row[0] if row else None


def obter_ultima_rega(watering_device_id):
    query = """
        SELECT executed_at
        FROM watering_commands
        WHERE watering_device_id = %s
          AND status = 'executed'
          AND executed_at IS NOT NULL
        ORDER BY executed_at DESC
        LIMIT 1
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (watering_device_id,))
            row = cur.fetchone()

    return row[0] if row else None


def existe_comando_pendente(watering_device_id):
    query = """
        SELECT EXISTS (
            SELECT 1
            FROM watering_commands
            WHERE watering_device_id = %s
              AND status = 'pending'
        )
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (watering_device_id,))
            return cur.fetchone()[0]