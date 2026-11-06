import json
import requests
from db import get_connection

IPMA_BASE_URL = "https://api.ipma.pt/open-data"
IPMA_TIMEOUT = 30

# Esta função chama a API do IPMA para obter toda a informação em json
def fazer_pedido_ipma(url):
    resposta = requests.get(url, timeout=IPMA_TIMEOUT)
    resposta.raise_for_status()
    return resposta.json()

# Esta função vai buscar todas as localidades do IPMA, permitindo relacionar o ID com o nome da localidade,
# distrito, latitude e longitude
def buscar_localizacoes_ipma():
    url = f"{IPMA_BASE_URL}/distrits-islands.json"
    dados = fazer_pedido_ipma(url)
    localizacoes = {}

    for local in dados.get("data", []):
        global_id = int(local["globalIdLocal"])
        localizacoes[global_id] = {
            "location_name": local.get("local"),
            "district": str(local.get("idDistrito")),
            "latitude": local.get("latitude"),
            "longitude": local.get("longitude"),
            "raw_location": local,
        }

    return localizacoes

# Esta função vai buscar as previsões do dia atual
def buscar_previsoes_ipma():
    previsoes = []
    url = f"{IPMA_BASE_URL}/forecast/meteorology/cities/daily/hp-daily-forecast-day0.json"
    dados = fazer_pedido_ipma(url)
    data_update = dados.get("dataUpdate")
    forecast_date = dados.get("forecastDate")

    for item in dados.get("data", []):
        item["dataUpdate"] = data_update
        item["forecastDate"] = forecast_date
        previsoes.append(item)

    return previsoes

#Esta função faz a atualização dos dados da tabela. Como só interessa os dados atuais, todos os dados anteriores
#serão eliminados
def atualizar_previsoes_ipma():
    localizacoes = buscar_localizacoes_ipma()
    previsoes = buscar_previsoes_ipma()
    total = 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ipma;")

            for previsao in previsoes:
                global_id = int(previsao["globalIdLocal"])
                local_info = localizacoes.get(global_id, {})
                district = local_info.get("district", "0")
                location_name = local_info.get("location_name", "Desconhecido")
                latitude = previsao.get("latitude") or local_info.get("latitude")
                longitude = previsao.get("longitude") or local_info.get("longitude")

                cur.execute(
                    """
                    INSERT INTO ipma (
                        global_id_local,
                        district,
                        location_name,
                        forecast_date,
                        temperature_min,
                        temperature_max,
                        precipitation_probability,
                        precipitation_class,
                        wind_direction,
                        wind_speed_class,
                        weather_type_id,
                        latitude,
                        longitude,
                        ipma_data_update,
                        raw_data,
                        updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
                    )
                    """,
                    (
                        global_id,
                        district,
                        location_name,
                        previsao.get("forecastDate"),
                        previsao.get("tMin"),
                        previsao.get("tMax"),
                        previsao.get("precipitaProb"),
                        previsao.get("classPrecInt"),
                        previsao.get("predWindDir"),
                        previsao.get("classWindSpeed"),
                        previsao.get("idWeatherType"),
                        latitude,
                        longitude,
                        previsao.get("dataUpdate"),
                        json.dumps(previsao),
                    )
                )
                total += 1

    return total