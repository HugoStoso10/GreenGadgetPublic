# Comando para correr: python main.py

import json
import logging
import time

from pathlib import Path

import db

from agent import processar_leitura
from config import INTERVALO_SEGUNDOS


FICHEIRO_ESTADO = Path(__file__).with_name("agent_state.json")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [AGENTE] %(levelname)s: %(message)s",
)


def carregar_estado():

    if not FICHEIRO_ESTADO.exists():
        return None

    with open(FICHEIRO_ESTADO, "r", encoding="utf-8") as ficheiro:
        return json.load(ficheiro)


def guardar_estado(estado):

    temporario = FICHEIRO_ESTADO.with_suffix(".tmp")

    with open(temporario, "w", encoding="utf-8") as ficheiro:
        json.dump(estado, ficheiro, indent=2)

    temporario.replace(FICHEIRO_ESTADO)


def executar_ciclo():

    leituras = db.obter_ultimas_leituras()
    estado = carregar_estado()

    if estado is None:
        estado = {
            str(leitura["device_id"]): leitura["sensor_id"]
            for leitura in leituras
        }

        guardar_estado(estado)

        logging.info(
            "Estado inicial criado. A aguardar novas leituras."
        )
        return

    novas = []

    for leitura in leituras:

        chave = str(leitura["device_id"])

        if chave not in estado:
            # Dispositivo novo: regista a leitura atual,
            # sem processar dados anteriores à sua inclusão.
            estado[chave] = leitura["sensor_id"]
            guardar_estado(estado)
            continue

        if leitura["sensor_id"] > estado[chave]:
            novas.append(leitura)

    if not novas:
        logging.info("Não existem novas leituras.")
        return

    for leitura in novas:

        device_id = leitura["device_id"]
        chave = str(device_id)

        try:
            previsao = db.obter_previsao_media(device_id)

            resultado = processar_leitura(
                leitura,
                previsao,
            )

            logging.info(
                "Dispositivo %s: %s",
                device_id,
                resultado,
            )

            estado[chave] = leitura["sensor_id"]
            guardar_estado(estado)

        except Exception:
            logging.exception(
                "Erro ao processar dispositivo %s.",
                device_id,
            )


def main():

    logging.info("Agente inteligente GreenGadget iniciado.")

    while True:

        try:
            executar_ciclo()

        except Exception:
            logging.exception("Erro no ciclo do agente.")

        time.sleep(INTERVALO_SEGUNDOS)


if __name__ == "__main__":
    main()