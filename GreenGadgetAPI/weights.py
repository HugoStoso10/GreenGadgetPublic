PESOS = {
    "solo": 0.50,
    "precipitacao": 0.20,
    "temperatura": 0.15,
    "humidade_ar": 0.05,
    "historico": 0.10,
}


def limitar(valor):
    return max(0.0, min(100.0, float(valor)))


def pontuar_solo(humidade, minimo, maximo):

    if None in (humidade, minimo, maximo):
        return None

    if float(maximo) <= float(minimo):
        return None

    if humidade <= minimo:
        return 100.0

    if humidade >= maximo:
        return 0.0

    return limitar(
        100 * (float(maximo) - float(humidade)) /
        (float(maximo) - float(minimo))
    )


def pontuar_precipitacao(probabilidade):

    if probabilidade is None:
        return None

    return 100.0 - limitar(probabilidade)


def pontuar_temperatura(temperatura, maxima, stress):

    if temperatura is None or maxima is None:
        return None

    maxima = float(maxima)

    if stress is None or float(stress) <= maxima:
        stress = maxima + 10.0

    stress = float(stress)

    if temperatura <= maxima:
        return 0.0

    if temperatura >= stress:
        return 100.0

    return limitar(
        100 * (float(temperatura) - maxima) /
        (stress - maxima)
    )


def pontuar_humidade_ar(humidade, minimo, maximo):

    if None in (humidade, minimo, maximo):
        return None

    if float(maximo) <= float(minimo):
        return None

    if humidade <= minimo:
        return 100.0

    if humidade >= maximo:
        return 0.0

    return limitar(
        100 * (float(maximo) - float(humidade)) /
        (float(maximo) - float(minimo))
    )


def pontuar_historico(horas_desde_rega, cooldown):

    if horas_desde_rega is None:
        return 100.0

    if cooldown is None or float(cooldown) <= 0:
        return 100.0

    return limitar(
        100 * float(horas_desde_rega) / float(cooldown)
    )


def calcular_pontuacao(criterios):

    # A humidade do solo é obrigatória.
    if criterios.get("solo") is None:
        raise ValueError(
            "Sem humidade do solo não é possível decidir."
        )

    validos = {
        k: limitar(v)
        for k, v in criterios.items()
        if k in PESOS and v is not None
    }

    soma = sum(PESOS[k] for k in validos)

    if soma <= 0:
        raise ValueError(
            "Não existem critérios válidos."
        )

    resultado = sum(
        PESOS[k] * v
        for k, v in validos.items()
    )

    return resultado / soma