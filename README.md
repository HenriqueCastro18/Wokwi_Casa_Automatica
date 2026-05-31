# 🏠 Casa Automática IoT — ESP32 + MicroPython

> Uma maquete de casa inteligente que monitora o ambiente, decide sozinha quando ligar o ar-condicionado, dispara alarmes e ainda entrega um painel web bonito em tempo real — tudo rodando num ESP32 simulado no Wokwi.

Este projeto nasceu como um sistema de automação residencial: um punhado de sensores conectados a um ESP32 que lê o ambiente, toma decisões automáticas (um termostato com lógica própria), avisa de situações de risco e publica tudo em três frentes ao mesmo tempo — um **display OLED** local, um **dashboard web** servido pelo próprio ESP32, e a nuvem via **MQTT** (que alimenta um fluxo no **Node-RED** e até uma planilha do Google).

---

## 📑 Índice

- [O que ele faz](#-o-que-ele-faz)
- [Como rodar no Wokwi](#-como-rodar-no-wokwi-passo-a-passo) ← *comece por aqui*
- [O hardware (circuito)](#-o-hardware-circuito)
- [A lógica por trás](#-a-lógica-por-trás)
- [As três interfaces](#-as-três-interfaces)
- [Comunicação: HTTP e MQTT](#-comunicação-http-e-mqtt)
- [Os arquivos do projeto](#-os-arquivos-do-projeto)

---

## ✨ O que ele faz

- **Lê o ambiente** — temperatura e umidade (DHT22), luminosidade (LDR), presença (PIR), distância (HC-SR04), gás (sensor MQ) e um potenciômetro para ajuste manual.
- **Climatiza sozinho** — um termostato inteligente liga e desliga o ar-condicionado (relé) com base num limite de temperatura que *você* ajusta no potenciômetro, sem ficar piscando ligado/desligado.
- **Vigia a casa** — dispara alertas de temperatura alta, pouca luz, movimento + objeto próximo e vazamento de gás.
- **Avisa de três jeitos** — LED RGB colorido, buzzer e display OLED, todos refletindo o estado atual.
- **Tem painel web próprio** — o ESP32 sobe um servidor HTTP e serve um dashboard que atualiza a cada 1 segundo, com botões para controlar os atuadores.
- **Vai pra nuvem** — publica o estado via MQTT no broker público da HiveMQ, pronto pra ser consumido pelo Node-RED incluído (que ainda registra o histórico numa planilha Google).

---

## 🚀 Como rodar no Wokwi (passo a passo)

> ⚠️ **A ordem importa.** O firmware serve uma página web (`page.html`), mas essa página precisa existir no sistema de arquivos do ESP32 **antes** do servidor começar a respondê-la. Por isso são **dois passos**.

O código pronto para colar está em **[`para_rodar.md`](para_rodar.md)** — ele contém os dois trechos na ordem certa.

### Passo 1 — Gerar a página web

Abra o simulador em MicroPython no [Wokwi](https://wokwi.com/), carregue o [`diagram.json`](diagram.json) e cole **o primeiro trecho** do [`para_rodar.md`](para_rodar.md) (o bloco `# html`). Esse trecho monta o HTML inteiro numa string e grava em `page.html`.

Rode e **espere aparecer no console**:

```
HTML Atualizado com Sucesso!
```

Pronto — a página está salva no ESP32.

### Passo 2 — Subir o firmware

Agora cole e rode **o segundo trecho** do [`para_rodar.md`](para_rodar.md) (o bloco `# Python`). Ele inicializa tudo e entra no loop principal. **Espere conectar** — você vai ver algo assim no console:

```
[WIFI]: Iniciando conexao...
WiFi: ('10.13.37.2', ...)
I2C: ['0x3c']
[MQTT]: Conectando...
[MQTT]: Conectado!
```

A partir daí o sistema está vivo: o OLED mostra os dados, os sensores são lidos a cada 1,5 s, e o servidor web está no ar.

### Passo 3 — Abrir o dashboard

O [`wokwi.toml`](wokwi.toml) já redireciona a porta 80 do ESP32 para a sua máquina:

```toml
[[net.forward]]
from = "localhost:8180"
to = "target:80"
```

Abra **http://localhost:8180** no navegador e o painel aparece. 🎉

> 💡 **Por que dois passos e não um arquivo `main.py` só?** Gerar o HTML é pesado pra memória do ESP32. Separar a geração (que roda uma vez) da execução (que roda sempre) mantém o firmware principal mais leve e evita estouro de RAM. Depois de gerado uma vez, o `page.html` fica salvo e o Passo 1 não precisa ser repetido.

---

## 🔌 O hardware (circuito)

Tudo isto está montado no [`diagram.json`](diagram.json) — um ESP32 DevKit numa protoboard com os periféricos abaixo. **A pinagem desta tabela é a que de fato roda** (a do `para_rodar.md`):

| Componente | Modelo | Pino(s) ESP32 | Função |
|---|---|---|---|
| Microcontrolador | ESP32 DevKit V1 | — | Cérebro de tudo |
| Display OLED | SSD1306 128×64 | D21 (SDA), D22 (SCL) — I²C | Status local |
| Temperatura / Umidade | DHT22 | D12 | Leitura ambiental |
| Luminosidade | LDR (foto-resistor) | D34 (ADC) | Sensor de luz |
| Gás | Sensor MQ | VN / D39 (ADC) | Detecção de vazamento |
| Movimento | PIR | D13 | Presença |
| Distância | HC-SR04 | D5 (Trig), D18 (Echo) | Ultrassônico |
| Ajuste de limite | Potenciômetro 10 k | D35 (ADC) | Define o limite de temp. |
| LED RGB | Catodo comum + 3×220 Ω | D14 (R), D26 (G), D27 (B) | Indicador de estado |
| Relé | Módulo 5 V | D32 | Liga/desliga o ar |
| Servo | SG90 | D23 (PWM 50 Hz) | Abre/fecha a "porta" |
| Buzzer | Passivo | D25 (PWM) | Alarme sonoro |

### O que cada cor do LED RGB significa

O LED RGB resume o estado da casa num relance (lógica em `ap()`):

| Cor | Estado |
|---|---|
| ⚪ Branco | Tudo normal |
| 🔵 Azul | Luz da sala ligada |
| 🟣 Magenta | Luz do quarto ligada |
| 🩵 Ciano | **Alerta ativo** (acompanha o buzzer) |

---

## 🧠 A lógica por trás

A parte mais interessante do projeto é o **termostato com temperatura virtual**. Em vez de simplesmente comparar a leitura do DHT22 com um limite, o firmware mantém uma temperatura simulada (`v_temp`) que sobe e desce de forma gradual — dá pra "ver" a casa esquentando e o ar resfriando, o que fica ótimo na demonstração.

**Como funciona o ciclo:**

1. **Você define o limite** girando o potenciômetro → `limite = 20 + (pot/4095) × 20`, ou seja, de **20 °C a 40 °C**.
2. **Casa esquentando** (ar desligado): a temperatura virtual sobe devagar (+0,1 por ciclo) em direção à leitura real, até no máximo `limite + 5`.
3. **Ponto crítico**: ao bater em `limite + 5`, entra em modo **emergência** — dispara o alerta e o buzzer, e aguarda 1,5 s.
4. **Ar liga**: passada a espera, o relé liga e a temperatura virtual começa a cair (−0,5 por ciclo).
5. **Ar desliga**: quando a temperatura chega perto de `limite − 1`, o ar desliga e o ciclo recomeça.

Essa histerese (a folga entre ligar e desligar) evita o relé ficar "batendo" sem parar — exatamente como um ar-condicionado de verdade.

> 🛟 **Segurança contra gás:** se a leitura de gás passar de 3800, o ar-condicionado é **forçado a desligar** na hora.

### Os alarmes

A função `al()` avalia cinco condições a cada ciclo e o dashboard mostra cada uma como ATIVO ou OK:

| Alarme | Dispara quando |
|---|---|
| 🌡️ Temperatura Alta | `temp > limite` |
| 💡 Pouca Luz | `0 < luz < 500` |
| 🚶 Movimento | PIR detecta presença |
| 📏 Objeto Próximo | `0 < distância < 30 cm` |
| ☁️ Gás | `gás > 3800` |

O **alerta geral** (LED ciano + sirene) acende quando há movimento com objeto próximo, vazamento de gás, ou temperatura acima de `limite + 5` com o ar desligado.

---

## 🖥️ As três interfaces

O mesmo estado é exibido em três lugares ao mesmo tempo:

1. **OLED (local)** — mostra temperatura, limite, luz, gás, movimento e distância direto na maquete.
2. **Dashboard web** — cards animados com todos os sensores, lista de alarmes e botões de controle. Servido pelo próprio ESP32, atualiza 1×/segundo.
3. **Node-RED / nuvem** — via MQTT (veja abaixo).

---

## 📡 Comunicação: HTTP e MQTT

### Servidor HTTP (porta 80)

O firmware sobe um servidor não-bloqueante que responde:

| Rota | O que faz |
|---|---|
| `GET /` | Devolve o dashboard (`page.html`) |
| `GET /api/data` | JSON com o estado completo + lista de alarmes |
| `GET /t/<campo>` | Inverte um booleano (`luz_quarto`, `luz_sala`, `rele`, `buz_temp`…) |
| `GET /porta/<ângulo>` | Posiciona o servo (0–180°) |

### MQTT (broker.hivemq.com:1883)

O ESP32 **publica** o estado em `casa/henrique/status` a cada 5 segundos e **assina** os tópicos de controle:

| Tópico | Ação |
|---|---|
| `casa/henrique/alerta` | Liga/desliga o alerta |
| `casa/henrique/rele` | Liga/desliga o ar-condicionado |
| `casa/henrique/buz_temp` | Controla o buzzer |
| `casa/henrique/porta` | Define o ângulo da porta |

### Node-RED incluso

O [`Node_Red.json`](Node_Red.json) é um fluxo pronto para importar no Node-RED. Ele:

- Assina `casa/henrique/status` e monta um **dashboard** com gauges de temperatura/umidade e textos de luz, distância, gás, movimento e status geral.
- Tem **botões** que publicam de volta nos tópicos de controle (ar, alerta, buzzer, abrir porta).
- Registra o histórico numa **planilha do Google Sheets** (via Apps Script), limitado a 1 envio por minuto.

---

## 📂 Os arquivos do projeto

> Existem **três variantes** do firmware no repositório. Vale entender a diferença para não se confundir:

| Arquivo | É o quê | Observação |
|---|---|---|
| **[`para_rodar.md`](para_rodar.md)** | ✅ **O código que realmente roda.** Os dois trechos para colar no Wokwi (gerar HTML + firmware). | Bate com o `diagram.json`. **Use este.** |
| [`diagram.json`](diagram.json) | O circuito do Wokwi | Pinagem oficial do projeto |
| [`page.html`](page.html) | O dashboard web (gerado pelo Passo 1) | Não edite à mão; é gerado |
| [`wokwi.toml`](wokwi.toml) | Config do Wokwi + redirecionamento de porta | — |
| [`Node_Red.json`](Node_Red.json) | Fluxo Node-RED (dashboard + Google Sheets) | Importe no Node-RED |
| [`firmware.py`](firmware.py) | Versão **estendida** com teclado 4×4 (senha `1234`), anel NeoPixel e sirene | ⚠️ Usa **outra pinagem** (DHT no D4, RGB em 12/16/17) e periféricos que **não estão** no `diagram.json` |
| [`main.py`](main.py) | Versão **enxuta** e local (sem MQTT, sem teclado, sem NeoPixel) | Importa a classe do OLED do `firmware.py`; DHT no D4 |

### ⚠️ Sobre a inconsistência de pinos

Se você for portar `firmware.py` ou `main.py` para hardware real, **confira a pinagem** — ela difere do `para_rodar.md`/`diagram.json` (principalmente o pino do DHT22 e os do LED RGB). A versão de referência, testada e alinhada ao circuito, é a do **`para_rodar.md`**. As outras são experimentos/variações.

---

## 🧰 Pré-requisitos (hardware real, opcional)

Para rodar fora do simulador você precisa de MicroPython no ESP32 e das libs `dht`, `umqtt.simple` e (se for usar o anel) `neopixel`. No Wokwi tudo isso já vem incluído.

---

## 📄 Licença

Projeto educacional/pessoal, fornecido "como está".

---

<div align="center">

**Feito por Henrique Castro** · ESP32 + MicroPython + MQTT + Node-RED

</div>
