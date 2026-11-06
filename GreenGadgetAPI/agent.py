from datetime import timezone
from statistics import mean

from config import LIMIAR_REGA

from weights import (
    pontuar_solo,
    pontuar_precipitacao,
    pontuar_temperatura,
    pontuar_humidade_ar,
    pontuar_historico,
    calcular_pontuacao,
)


def normalizar_data(valor):

    if valor is None:
        return None

    if valor.tzinfo is None:
        return valor.replace(
            tzinfo=timezone.utc
        )

    return valor.astimezone(timezone.utc)


def media_valida(leituras, campo):

    valores = [
        float(r[campo])
        for r in leituras
        if r.get(campo) is not None
    ]

    return mean(valores) if valores else None


def resumir_leituras(leituras):

    """
    Analisa as leituras das últimas 24 horas.

    Calcula:
    - Temperatura média do ar.
    - Humidade média do ar.
    - Humidade média do solo.
    - Humidade mínima do solo.
    - Última humidade do solo.
    """

    if not leituras:
        return None

    ordenadas = sorted(
        leituras,
        key=lambda r: normalizar_data(r["timestamp"])
    )

    ultimas = ordenadas[-1]

    solos = [
        float(r["soil_humidity"])
        for r in ordenadas
        if r.get("soil_humidity") is not None
    ]

    return {
        "device_id": ultimas["device_id"],
        "plant_id": ultimas["plant_id"],

        "latest_sensor_id": ultimas["sensor_id"],

        "latest_timestamp": normalizar_data(
            ultimas["timestamp"]
        ),

        "temperature_avg": media_valida(
            ordenadas,
            "temperature"
        ),

        "air_humidity_avg": media_valida(
            ordenadas,
            "air_humidity"
        ),

        "soil_humidity_avg": media_valida(
            ordenadas,
            "soil_humidity"
        ),

        "soil_humidity_min": (
            min(solos) if solos else None
        ),

        "soil_humidity_latest": (
            float(ultimas["soil_humidity"])
            if ultimas.get("soil_humidity") is not None
            else None
        ),

        "reading_count": len(ordenadas),
    }


def analisar_planta(
    dados,
    planta,
    previsao,
    horas_desde_rega,
    limiar=LIMIAR_REGA
):

    """
    Calcula a necessidade de rega da planta.

    Considera:
    - Humidade do solo.
    - Precipitação.
    - Temperatura do ar.
    - Humidade do ar.
    - Histórico de regas.
    """

    solo_media = pontuar_solo(
        dados.get("soil_humidity_avg"),
        planta.get("min_soil_humidity"),
        planta.get("max_soil_humidity"),
    )

    solo_minimo = pontuar_solo(
        dados.get("soil_humidity_min"),
        planta.get("min_soil_humidity"),
        planta.get("max_soil_humidity"),
    )

    solo_atual = pontuar_solo(
        dados.get("soil_humidity_latest"),
        planta.get("min_soil_humidity"),
        planta.get("max_soil_humidity"),
    )

    if (
        solo_media is None
        or solo_minimo is None
        or solo_atual is None
    ):
        return {
            "action": "wait",
            "score": None,
            "reason": (
                "Não existem valores válidos "
                "de humidade do solo."
            ),
        }

    # A média é o indicador principal.
    # A leitura atual e o mínimo ajudam a identificar
    # situações em que o solo está a secar rapidamente.

    solo = max(
        solo_media,
        solo_atual,
        solo_minimo * 0.85
    )

    temperatura = dados.get(
        "temperature_avg"
    )

    temperatura_prevista = previsao.get(
        "temperature_max"
    )

    if (
        temperatura is not None
        and temperatura_prevista is not None
    ):
        temperatura = max(
            float(temperatura),
            float(temperatura_prevista)
        )

    elif temperatura is None:
        temperatura = temperatura_prevista

    criterios = {

        "solo": solo,

        "precipitacao": pontuar_precipitacao(
            previsao.get(
                "precipitation_probability"
            )
        ),

        "temperatura": pontuar_temperatura(
            temperatura,
            planta.get("max_air_temperature"),
            planta.get("heat_stress_air_temperature"),
        ),

        "humidade_ar": pontuar_humidade_ar(
            dados.get("air_humidity_avg"),
            planta.get("min_air_humidity"),
            planta.get("max_air_humidity"),
        ),

        "historico": pontuar_historico(
            horas_desde_rega,
            planta.get("watering_cooldown_hours"),
        ),
    }

    score = round(
        calcular_pontuacao(criterios),
        2
    )

    water = score >= limiar

    return {
        "action": "water" if water else "wait",

        "score": score,

        "criteria": criterios,

        "reason": (
            f"Pontuação {score}/100; "
            f"limiar de rega {limiar}."
            if water
            else
            f"Pontuação {score}/100 abaixo "
            f"do limiar {limiar}."
        ),
    }


def calcular_duracao(
    planta,
    temperatura_media
):

    """
    Calcula a duração da rega.

    Utiliza a duração configurada na planta.
    Se existir stress térmico, pode utilizar
    uma duração específica.
    """

    duracao = (
        planta.get("watering_duration_seconds")
        or 5
    )

    stress = planta.get(
        "heat_stress_air_temperature"
    )

    if (
        temperatura_media is not None
        and stress is not None
        and temperatura_media >= float(stress)
    ):

        duracao = (
            planta.get(
                "heat_stress_watering_duration_seconds"
            )
            or duracao
        )

    duracao = int(duracao)

    if not 1 <= duracao <= 600:
        raise ValueError(
            "Duração de rega fora do intervalo permitido."
        )

    return duracao