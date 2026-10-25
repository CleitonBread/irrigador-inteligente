"""Irrigador Inteligente - firmware em MicroPython (ESP8266 / NodeMCU)

O que ele faz, a cada INTERVALO_LEITURA_S segundos:
    1. Lê o sensor de umidade (A0) e converte para %.
    2. Envia a leitura ao servidor (POST /api/leituras).
    3. O servidor responde se deve irrigar e por quantos segundos.
    4. Se sim, liga a bomba (pelo relé) pelo tempo pedido e desliga.

A decisão de irrigar fica no servidor. A placa só obedece, mas tem
proteções próprias: tempo máximo da bomba e bomba desligada se o Wi-Fi cair.

Ligações:
    Sensor  VCC -> 3V3 | AOUT -> A0 | GND -> GND
    Relé    IN  -> D1  | VCC e COM -> 5 V | GND -> GND
    Bomba   + -> NO do relé | - -> GND

Este arquivo deve ser salvo na placa com o nome main.py: o MicroPython
executa o main.py sozinho toda vez que a placa liga.
"""

import json
import time

import network
from machine import ADC, Pin

try:
    import urequests as requests
except ImportError:
    import requests

# ===================== CONFIGURE AQUI =====================

WIFI_SSID = "NOME_DA_SUA_REDE"   # precisa ser rede 2,4 GHz
WIFI_SENHA = "SENHA_DA_REDE"

# IP do computador que está rodando o backend (veja com ipconfig / ifconfig).
SERVIDOR = "http://192.168.0.10:8000"

# Calibração do sensor: ligue MODO_CALIBRACAO, rode o programa e anote
#   - o valor com o sensor SECO, no ar
#   - o valor com a ponta do sensor dentro de um copo com água
# Depois escreva esses dois números abaixo e desligue o MODO_CALIBRACAO.
VALOR_SECO = 800
VALOR_MOLHADO = 400
MODO_CALIBRACAO = False

# A maioria dos módulos relé de 1 canal liga quando o pino vai para LOW (0).
# Se a bomba ligar quando deveria estar desligada, troque para False.
RELE_LIGA_COM_LOW = True

# ==========================================================

PINO_RELE = 5                 # D1 no NodeMCU = GPIO5 (seguro na inicialização)
INTERVALO_LEITURA_S = 10      # tempo entre leituras
TEMPO_MAX_BOMBA_S = 15        # nunca liga a bomba por mais que isso
NUM_AMOSTRAS = 10             # mediana de várias leituras reduz o ruído

# Primeira coisa: a bomba começa desligada. O valor já é definido ao criar o pino.
rele = Pin(PINO_RELE, Pin.OUT, value=1 if RELE_LIGA_COM_LOW else 0)
sensor = ADC(0)               # único pino analógico do ESP8266 (A0), valores de 0 a 1023


# ---------------------------------------------------------------- bomba

def bomba(ligada):
    if RELE_LIGA_COM_LOW:
        rele.value(0 if ligada else 1)
    else:
        rele.value(1 if ligada else 0)


def irrigar(segundos):
    segundos = min(segundos, TEMPO_MAX_BOMBA_S)
    print("Irrigando por", segundos, "s...")
    bomba(True)
    try:
        time.sleep(segundos)
    finally:
        bomba(False)  # desliga mesmo se acontecer um erro ou o programa for interrompido
    print("Bomba desligada.")


# ---------------------------------------------------------------- sensor

def ler_sensor_bruto():
    """Mediana de várias leituras: ignora picos isolados de ruído."""
    amostras = []
    for _ in range(NUM_AMOSTRAS):
        amostras.append(sensor.read())
        time.sleep(0.02)
    amostras.sort()
    return amostras[NUM_AMOSTRAS // 2]


def bruto_para_percentual(bruto):
    pct = (VALOR_SECO - bruto) * 100 / (VALOR_SECO - VALOR_MOLHADO)
    return max(0.0, min(100.0, pct))


def leitura_valida(bruto):
    """Valor perto de 0 ou do máximo costuma ser fio solto ou sensor com defeito."""
    return 50 < bruto < 1020


# ---------------------------------------------------------------- Wi-Fi e servidor

def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return True

    print("Conectando em", WIFI_SSID, end="")
    wlan.connect(WIFI_SSID, WIFI_SENHA)
    inicio = time.time()
    while not wlan.isconnected() and time.time() - inicio < 15:
        time.sleep(0.5)
        print(".", end="")
    print()

    if wlan.isconnected():
        print("Conectado. IP da placa:", wlan.ifconfig()[0])
        return True
    print("Falha ao conectar no Wi-Fi.")
    return False


def enviar_leitura(umidade, bruto):
    """Envia a leitura ao servidor. Devolve a duração da rega pedida (0 = não irrigar)."""
    corpo = json.dumps({"umidade": round(umidade, 1), "bruto": bruto})
    resposta = None
    try:
        resposta = requests.post(
            SERVIDOR + "/api/leituras",
            data=corpo,
            headers={"Content-Type": "application/json"},
        )
        if resposta.status_code != 200:
            print("Erro do servidor, código", resposta.status_code)
            return 0
        dados = resposta.json()  # exemplo: {"irrigar": True, "duracao_s": 5}
        print("Servidor:", dados)
        if dados.get("irrigar"):
            return int(dados.get("duracao_s", 0))
        return 0
    except Exception as erro:
        print("Falha ao falar com o servidor:", erro)
        return 0
    finally:
        if resposta is not None:
            resposta.close()


# ---------------------------------------------------------------- programa principal

def ciclo():
    bruto = ler_sensor_bruto()
    if not leitura_valida(bruto):
        print("Leitura invalida (", bruto, "). Confira os fios do sensor. Sem irrigar.")
        return

    umidade = bruto_para_percentual(bruto)
    print("Bruto:", bruto, "| Umidade: {:.1f}%".format(umidade))

    # Sem Wi-Fi, a placa não tem como saber se deve irrigar: a bomba fica desligada.
    if not conectar_wifi():
        return

    duracao = enviar_leitura(umidade, bruto)
    if duracao > 0:
        irrigar(duracao)


def main():
    print("Irrigador Inteligente iniciando...")

    if MODO_CALIBRACAO:
        while True:
            print("Valor bruto do sensor:", ler_sensor_bruto())
            time.sleep(1)

    conectar_wifi()
    while True:
        try:
            ciclo()
        except Exception as erro:
            print("Erro inesperado:", erro)
            bomba(False)
        time.sleep(INTERVALO_LEITURA_S)


if __name__ == "__main__":
    main()
