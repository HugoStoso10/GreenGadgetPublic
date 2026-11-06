PESOS = {
    "solo": 0.50,
    "precipitacao": 0.20,
    "temperatura": 0.15,
    "humidade_ar": 0.05,
    "historico": 0.10,
}

LIMIAR_REGA = 70


def limitar(valor):
    return max(0.0, min(100.0, float(valor)))


def pontuar_solo(humidade, minimo, maximo):

    if None in (humidade, minimo, maximo):
        return None

    if maximo <= minimo:
        return None

    if humidade <= minimo:
        return 100.0

    if humidade >= maximo:
        return 0.0

    return limitar(
        100 * (maximo - humidade) / (maximo - minimo)
    )


def pontuar_precipitacao(probabilidade):

    if probabilidade is None:
        return None

    return 100.0 - limitar(probabilidade)


def pontuar_temperatura(temperatura, maxima, stress):

    if temperatura is None or maxima is None:
        return None

    if stress is None or stress <= maxima:
        stress = maxima + 10.0

    if temperatura <= maxima:
        return 0.0

    if temperatura >= stress:
        return 100.0

    return limitar(
        100 * (temperatura - maxima) / (stress - maxima)
    )


def pontuar_humidade_ar(humidade, minimo, maximo):

    if None in (humidade, minimo, maximo):
        return None

    if maximo <= minimo:
        return None

    if humidade <= minimo:
        return 100.0

    if humidade >= maximo:
        return 0.0

    return limitar(
        100 * (maximo - humidade) / (maximo - minimo)
    )


def pontuar_historico(horas_desde_rega, cooldown):
    if horas_desde_rega is None:
        return 100.0

    if cooldown is None or cooldown <= 0:
        return 100.0

    return limitar(
        100 * horas_desde_rega / cooldown
    )


def calcular_pontuacao(criterios):
    if criterios.get("solo") is None:
        raise ValueError(
            "Não é possível calcular a decisão sem humidade do solo."
        )

    disponiveis = {
        nome: valor
        for nome, valor in criterios.items()
        if nome in PESOS and valor is not None
    }

    soma_pesos = sum(
        PESOS[nome] for nome in disponiveis
    )

    if soma_pesos <= 0:
        raise ValueError("Não existem critérios válidos.")

    return sum(
        PESOS[nome] * limitar(valor)
        for nome, valor in disponiveis.items()
    ) / soma_pesos