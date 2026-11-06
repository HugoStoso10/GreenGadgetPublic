import logging
from datetime import datetime

import requests
import db

from weights import (
    pontuar_solo,
    pontuar_precipitacao,
    pontuar_temperatura,
    pontuar_humidade_ar,
    pontuar_historico,
    calcular_pontuacao,
)

from config import (
    LIMIAR_REGA,
    IDADE_MAXIMA_LEITURA_MINUTOS,
    MODO_SIMULACAO,
    MODO_TESTE,
    TESTE_COOLDOWN_HORAS,
    TESTE_LIMIAR_REGA,
    API_BASE_URL,
    API_TIMEOUT,
)


def normalizar_data(data):
    """
    A base de dados utiliza timestamp without time zone.
    Mantemos a hora local do servidor para as comparações.
    """
    if data is None:
        return None

    if data.tzinfo is not None:
        return data.replace(tzinfo=None)

    return data


def analisar_planta(dados, planta, previsao, horas_desde_rega):

    solo = pontuar_solo(
        dados.get("soil_humidity"),
        planta.get("min_soil_humidity"),
        planta.get("max_soil_humidity"),
    )

    if solo is None:
        return {
            "action": "wait",
            "score": None,
            "reason": "Humidade do solo inválida.",
        }

    temperaturas = [
        valor
        for valor in (
            dados.get("temperature"),
            previsao.get("temperature_max"),
        )
        if valor is not None
    ]

    temperatura = max(temperaturas) if temperaturas else None

    criterios = {
        "solo": solo,

        "precipitacao": pontuar_precipitacao(
            previsao.get("precipitation_probability")
        ),

        "temperatura": pontuar_temperatura(
            temperatura,
            planta.get("max_air_temperature"),
            planta.get("heat_stress_air_temperature"),
        ),

        "humidade_ar": pontuar_humidade_ar(
            dados.get("air_humidity"),
            planta.get("min_air_humidity"),
            planta.get("max_air_humidity"),
        ),

        "historico": pontuar_historico(
            horas_desde_rega,
            planta.get("watering_cooldown_hours"),
        ),
    }

    pontuacao = calcular_pontuacao(criterios)

    necessita_rega = pontuacao >= LIMIAR_REGA

    return {
        "action": "water" if necessita_rega else "wait",
        "score": round(pontuacao, 2),
        "criteria": criterios,
        "reason": (
            "Pontuação igual ou superior ao limiar."
            if necessita_rega
            else "A pontuação não atingiu o limiar de rega."
        ),
    }


def enviar_comando_rega(watering_device_id, duracao, motivo):
    """
    Envia o comando através da API existente.
    Em simulação, não efetua qualquer pedido POST.
    """

    if MODO_SIMULACAO:
        logging.info(
            "[SIMULAÇÃO] Enviaria comando de rega: "
            "módulo=%s, duração=%s segundos, motivo=%s",
            watering_device_id,
            duracao,
            motivo,
        )
        return "Simulação: comando não enviado."

    url = (
        f"{API_BASE_URL}/watering-devices/"
        f"{watering_device_id}/command"
    )

    payload = {
        "duration_seconds": duracao,
        "reason": motivo,
    }

    resposta = requests.post(
        url,
        json=payload,
        timeout=API_TIMEOUT,
    )

    resposta.raise_for_status()

    return resposta.json()



def avaliar_dispositivo(leitura, previsao):

    device_id = leitura["device_id"]
    plant_id = leitura["plant_id"]

    data_leitura = normalizar_data(leitura["timestamp"])

    if data_leitura is None:
        return "Leitura sem data; avaliação ignorada."

    idade = (
        datetime.now() - data_leitura
    ).total_seconds() / 60

    if idade < 0 or idade > IDADE_MAXIMA_LEITURA_MINUTOS:
        return "Leitura desatualizada; avaliação ignorada."

    planta = db.obter_planta(plant_id)

    if planta is None:
        return f"Planta {plant_id} não encontrada."

    modulo_id = db.obter_modulo_rega(device_id)

    if modulo_id is None:
        return "Não existe módulo de rega associado."

    if db.existe_comando_pendente(modulo_id):
        return "Já existe um comando de rega pendente."

    ultima_rega = db.obter_ultima_rega(modulo_id)

    if ultima_rega is not None:
        ultima_rega = normalizar_data(ultima_rega)

        horas_desde_rega = (
            datetime.now() - ultima_rega
        ).total_seconds() / 3600
    else:
        horas_desde_rega = None

    dados = {
        "temperature": leitura["temperature"],
        "air_humidity": leitura["air_humidity"],
        "soil_humidity": leitura["soil_humidity"],
    }

    decisao = analisar_planta(
        dados,
        planta,
        previsao,
        horas_desde_rega,
    )

    # Selecionar o limiar de rega
    if MODO_TESTE:
        limiar = TESTE_LIMIAR_REGA
    else:
        limiar = LIMIAR_REGA

    # Aplicar o limiar configurado
    pontuacao = decisao.get("score")

    if pontuacao is None:
        return decisao["reason"]

    if pontuacao >= limiar:
        decisao["action"] = "water"
    else:
        decisao["action"] = "wait"

    logging.info(
        "Dispositivo %s | Leitura %s | IPMA %s | "
        "Pontuação: %s | Limiar: %s | Decisão: %s",
        device_id,
        leitura["sensor_id"],
        previsao.get("location_name"),
        pontuacao,
        limiar,
        decisao,
    )

    if decisao["action"] != "water":
        return decisao["reason"]

    # Selecionar o cooldown
    if MODO_TESTE:
        cooldown = TESTE_COOLDOWN_HORAS
    else:
        cooldown = planta.get("watering_cooldown_hours")

        if cooldown is None:
            cooldown = COOLDOWN_PADRAO_HORAS

    # Verificar intervalo mínimo entre regas
    if (
        horas_desde_rega is not None
        and cooldown is not None
        and horas_desde_rega < float(cooldown)
    ):
        return (
            f"Rega bloqueada pelo intervalo mínimo "
            f"({cooldown} horas)."
        )

    # Determinar duração da rega
    duracao = planta.get("watering_duration_seconds") or 5

    temperatura = dados["temperature"]
    temperatura_stress = planta.get("heat_stress_air_temperature")

    if (
        temperatura is not None
        and temperatura_stress is not None
        and temperatura >= temperatura_stress
    ):
        duracao = (
            planta.get("heat_stress_watering_duration_seconds")
            or duracao
        )

    duracao = int(duracao)

    if not 1 <= duracao <= 600:
        return "Duração de rega inválida."

    motivo = (
        f"Agente inteligente GreenGadget: "
        f"pontuação {pontuacao}/100"
    )

    # Enviar ou simular o comando
    resultado = enviar_comando_rega(
        modulo_id,
        duracao,
        motivo,
    )

    return str(resultado)



def processar_leitura(leitura, previsao):
    return avaliar_dispositivo(leitura, previsao)