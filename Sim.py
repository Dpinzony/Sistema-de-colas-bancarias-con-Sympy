"""
Simulación de sistema bancario con SimPy
-----------------------------------------
Comparación entre:
  - Cola única compartida entre 6 cajeros
  - Colas separadas (una por cajero)
"""
import simpy
import random
import numpy as np

# ====================================================
# PARÁMETROS DEL MODELO
# ====================================================

LAMBDA_HORA = 180                   # clientes/hora
LAMBDA = LAMBDA_HORA / 3600.0       # clientes/segundo
NUM_CAJEROS = 6
TIEMPO_SIMULACION = 8 * 60 * 60     # 8 horas en segundos

# Tipos de transacciones: (probabilidad, tiempo medio de servicio)
TRANSACCIONES = [
    (0.15, 45.0),
    (0.29, 75.0),
    (0.32, 120.0),
    (0.24, 180.0)
]

# ====================================================
# FUNCIONES AUXILIARES
# ====================================================

def generar_tipo_transaccion():
    """Devuelve el índice del tipo de transacción según frecuencias."""
    r = random.random()
    acum = 0
    for i, (p, _) in enumerate(TRANSACCIONES):
        acum += p
        if r <= acum:
            return i
    return len(TRANSACCIONES) - 1

def generar_tiempo_servicio(tipo):
    """Devuelve un tiempo de servicio exponencial según el tipo."""
    media = TRANSACCIONES[tipo][1]
    return random.expovariate(1 / media)

def generar_tiempo_llegada():
    """Devuelve el tiempo entre llegadas (exponencial)."""
    return random.expovariate(LAMBDA)

# ====================================================
# PROCESO: CLIENTE (cola única)
# ====================================================

def cliente_cola_unica(env, nombre, cajeros, tiempos_espera):
    llegada = env.now
    tipo = generar_tipo_transaccion()

    with cajeros.request() as req:
        yield req
        espera = env.now - llegada
        tiempos_espera.append(espera)
        yield env.timeout(generar_tiempo_servicio(tipo))

# ====================================================
# PROCESO: CLIENTE (colas separadas)
# ====================================================

def cliente_colas_separadas(env, nombre, cajeros, tiempos_espera):
    llegada = env.now
    tipo = generar_tipo_transaccion()
    # Escoger la cola más corta
    cajero = min(cajeros, key=lambda r: len(r.queue))
    with cajero.request() as req:
        yield req
        espera = env.now - llegada
        tiempos_espera.append(espera)
        yield env.timeout(generar_tiempo_servicio(tipo))

# ====================================================
# GENERADOR DE CLIENTES
# ====================================================

def generador_clientes(env, modo, cajeros, tiempos_espera):
    """Crea llegadas según el modo de simulación."""
    i = 0
    while True:
        yield env.timeout(generar_tiempo_llegada())
        i += 1
        if modo == "cola_unica":
            env.process(cliente_cola_unica(env, f"Cliente {i}", cajeros, tiempos_espera))
        elif modo == "colas_separadas":
            env.process(cliente_colas_separadas(env, f"Cliente {i}", cajeros, tiempos_espera))

# ====================================================
# FUNCIÓN DE SIMULACIÓN GENERAL
# ====================================================

def simular_banco(modo):
    """Ejecuta la simulación para el modo indicado."""
    env = simpy.Environment()
    tiempos_espera = []

    if modo == "cola_unica":
        cajeros = simpy.Resource(env, capacity=NUM_CAJEROS)
    else:
        cajeros = [simpy.Resource(env, capacity=1) for _ in range(NUM_CAJEROS)]

    env.process(generador_clientes(env, modo, cajeros, tiempos_espera))
    env.run(until=TIEMPO_SIMULACION)

    # Estadísticas
    promedio = np.mean(tiempos_espera) if tiempos_espera else 0
    maximo = np.max(tiempos_espera) if tiempos_espera else 0
    total = len(tiempos_espera)

    return {
        "modo": modo,
        "clientes": total,
        "espera_promedio": promedio,
        "espera_maxima": maximo
    }

# ====================================================
# PROGRAMA PRINCIPAL
# ====================================================

def main():
    random.seed(12345)

    print("\n=============================================")
    print(" SIMULACIÓN DE SISTEMA BANCARIO CON SIMPY")
    print("=============================================\n")

    # Simulación 1: Cola única
    resultado_unica = simular_banco("cola_unica")

    # Simulación 2: Colas separadas
    resultado_separadas = simular_banco("colas_separadas")

    # Mostrar resultados comparativos
    print("=== RESULTADOS COMPARATIVOS ===\n")
    print(f"{'Modo':<20}{'Clientes':<15}{'Espera Prom. (s)':<20}{'Espera Max (s)':<20}")
    print("-" * 75)
    for r in [resultado_unica, resultado_separadas]:
        print(f"{r['modo']:<20}{r['clientes']:<15}{r['espera_promedio']:<20.2f}{r['espera_maxima']:<20.2f}")
    print("-" * 75)


if __name__ == "__main__":
    main()
