# Sistema de Automação e Monitoramento Residencial IoT

Uma solução completa de automação residencial baseada em ESP32 e MicroPython, oferecendo monitoramento em tempo real, controle de dispositivos e integração com múltiplos protocolos de comunicação.

## 📋 Visão Geral

Sistema IoT modular que implementa:
- **Monitoramento ambiental**: temperatura, umidade, luminosidade, detecção de gás e movimento
- **Controle de acesso**: autenticação via teclado matricial com bloqueio de segurança
- **Automação inteligente**: controle de ar-condicionado baseado em temperatura e detecção de gás
- **Interface local**: display OLED para feedback imediato do sistema
- **Interface remota**: dashboard web em tempo real via HTTP e WebSocket
- **Conectividade**: WiFi, MQTT (HiveMQ) e HTTP local para integração de terceiros

## 🚀 Funcionalidades Principais

### Sensores e Leitura de Dados
- **Temperatura e Umidade**: DHT22 com termostato inteligente
- **Luminosidade**: Sensor LDR com faixa de 0-4095
- **Detecção de Movimento**: Sensor PIR para alertas de presença
- **Distância**: Sensor ultrassônico HC-SR04 (2-400 cm)
- **Qualidade do Ar**: Sensor de gás MQ com limiar configurável
- **Controle Manual**: Potenciômetro para ajuste dinâmico de limite de temperatura (20-40°C)

### Controle de Acesso
- Teclado matricial 4x4 com suporte a senha numérica (padrão: 1234)
- Sistema de bloqueio após 3 tentativas erradas (30 segundos)
- Feedback sonoro em cada interação
- Display local mostrando status da entrada em tempo real

### Automação de Climatização
- Controle de ar-condicionado com histerese para evitar ligar/desligar frequente
- Detecção e desativação automática do AC em caso de vazamento de gás
- Limite de temperatura ajustável dinamicamente via potenciômetro
- Estado persistente com feedback visual (LED RGB)

### Alertas e Monitoramento
- **Alerta de Temperatura**: quando excede limite + 5°C
- **Alerta de Luminosidade**: quando abaixo de 500 lux
- **Alerta de Movimento**: detecção em modo armado
- **Alerta de Proximidade**: objeto detectado a menos de 30 cm
- **Alerta de Gás**: concentração acima de 3800 ppm
- **Alerta de Invasão**: 3+ tentativas de entrada incorreta

### Feedback Visual e Sonoro
- **LED RGB**: indicação de estado (verde: normal, ciano: porta aberta, laranja: AC ligado, vermelho: alerta)
- **NeoPixel Ring (16 LEDs)**: animação de alerta (pulsante em vermelho) ou padrão de espera
- **Buzzer**: alertas sonoros com frequência variável conforme o tipo de evento

## 🔧 Hardware Necessário

| Componente | Modelo | Pino ESP32 | Quantidade |
|---|---|---|---|
| Microcontrolador | ESP32 DevKit V4 | - | 1 |
| Display OLED | SSD1306 (128x64) | GPIO 21/22 (I2C) | 1 |
| Sensor de Temperatura/Umidade | DHT22 | GPIO 4 (Data) | 1 |
| Sensor de Luz | LDR + ADC | GPIO 34 | 1 |
| Sensor de Gás | MQ-2/MQ-9 | GPIO 39 | 1 |
| Sensor de Movimento | PIR | GPIO 13 | 1 |
| Sensor de Distância | HC-SR04 | GPIO 5 (Trig), GPIO 18 (Echo) | 1 |
| Teclado Matricial | 4x4 | GPIO 2,15,19,33 (linhas), GPIO 26,27,14,16 (colunas) | 1 |
| LED RGB | Comum | GPIO 12 (R), GPIO 16 (G), GPIO 17 (B) | 1 |
| NeoPixel Ring | WS2812B 16-pixel | GPIO 17 (Data) | 1 |
| Buzzer | Passivo 1500Hz | GPIO 25 | 1 |
| Servo Motor | SG90/MG90 | GPIO 23 (PWM 50Hz) | 1 |
| Relé | 5V | GPIO 32 | 1 |
| Potenciômetro | Linear 10k | GPIO 35 | 1 |

## 📡 Protocolos de Comunicação

### WiFi
- Modo STA (Station)
- Rede: `Wokwi-GUEST` (configurável em `main.py`)
- Reconexão automática a cada 5 segundos

### HTTP
- **Porta**: 80
- **Endpoints**:
  - `GET /` - Retorna página HTML do dashboard
  - `GET /api/data` - JSON com estado completo do sistema
  - `GET /t/{campo}` - Toggle de variáveis booleanas (alerta, rele, buz_temp)
  - `GET /porta/{valor}` - Define ângulo da porta (0-180)

### MQTT
- **Broker**: broker.hivemq.com:1883
- **Tópicos subscritos**:
  - `casa/henrique/alerta` - Ligação/desligação de alerta
  - `casa/henrique/rele` - Ligação/desligação do AC
  - `casa/henrique/buz_temp` - Controle do buzzer
  - `casa/henrique/porta` - Ângulo da porta
- **Publicação**: `casa/henrique/status` (a cada 5 segundos)

## 📊 Estrutura de Dados do Estado

```python
{
  "alerta": bool,           # Alerta geral ativo
  "rele": bool,             # Ar-condicionado ligado
  "porta": int (0-180),     # Ângulo do servo
  "porta_aberta": bool,     # Status da porta
  "buz_temp": bool,         # Buzzer por temperatura
  "temp": float,            # Temperatura em °C
  "hum": float,             # Umidade em %
  "luz": int,               # Luminosidade (0-4095)
  "pot": int,               # Valor do potenciômetro
  "gas": int,               # Leitura do sensor de gás
  "limite": float,          # Limite de temperatura atual
  "mov": int,               # Movimento detectado (0 ou 1)
  "dist": float,            # Distância em cm
  "wifi": bool,             # WiFi conectado
  "mqtt": bool,             # MQTT conectado
  "oled": bool,             # Display inicializado
  "kp_buf": str,            # Buffer de entrada do teclado
  "kp_msg": str,            # Mensagem de feedback do teclado
  "sistema_armado": bool,   # Sistema em modo armado
  "alarmes": [{...}]        # Array de alertas ativos
}
```

## 🔐 Segurança

- Limite de 3 tentativas de entrada antes de bloqueio
- Bloqueio de 30 segundos após limite de tentativas
- CORS habilitado para integração com dashboards
- Nenhuma sensibilidade a erros de decode (ignorados silenciosamente)
- Validação de entrada para valores numéricos

## 📦 Instalação e Execução

### Pré-requisitos
- MicroPython para ESP32
- Bibliotecas: `dht`, `umqtt.simple`, `neopixel`
- Simulador Wokwi (opcional, para teste sem hardware)

### Setup
1. Flash MicroPython no ESP32
2. Copie `main.py` para o dispositivo
3. Configure WiFi em `main.py` (linha 49)
4. Configure MQTT broker se necessário (linha 244)
5. Reinicie o ESP32

### Arquivos Necessários
- `main.py` - Firmware principal
- `page.html` - Dashboard web (gerado automaticamente)
- `boot.py` - Script de inicialização (opcional)

## 🌐 Acesso ao Dashboard

1. Obtenha o IP do ESP32 via console
2. Acesse `http://<ESP32_IP>` em qualquer navegador
3. Dashboard atualiza em tempo real (1Hz)
4. Controle direto de estados via botões de toggle

## 🧪 Teste e Simulação

Projeto compatível com **Wokwi** (simulador online):
- Arquivo de configuração: `wokwi.toml`
- Arquivo de diagrama: `diagram.json`
- Simula hardware completo sem necessidade de placa física

## 📝 Notas de Implementação

### Performance
- Loop principal: 10ms (100Hz)
- Atualização de sensores: 1500ms
- Atualização MQTT: 5000ms
- Timeout de conexão HTTP: 300ms

### Gerenciamento de Memória
- Garbage collection automático ativado
- Buffer OLED otimizado (1024 bytes)
- Stream chunked para envio de página.html

### Tratamento de Erros
- Tentativas de reconexão WiFi a cada 5 segundos
- Fallback para modo offline com funcionalidade local
- Logs detalhados via UART para debugging

## 🔄 Fluxo de Operação

```
Inicialização
├── WiFi Connect
├── MQTT Connect (se WiFi OK)
├── I2C Scan (OLED)
├── Inicializa Sensores
└── HTTP Server (porta 80)
    │
    ├── Main Loop (10ms)
    │   ├── Keypad Scan
    │   ├── HTTP Accept & Process
    │   ├── Sensor Read (1.5s)
    │   ├── Smart Logic (Thermostat, Alerts)
    │   ├── Output Update (PWM, LED, Display)
    │   └── MQTT Publish (5s)
    │
    └── Shutdown Graceful
```

## 🛠️ Manutenção

### Logs via UART
```
[WIFI]: Iniciando conexao...
WiFi: IP_Address
I2C: [hex_addresses]
OLED: OK
[MQTT]: Conectando...
[MQTT]: Conectado!
```

### Debugging
- Descomente prints adicionais em `main.py`
- Monitore MQTT topics com cliente externo
- Use simulador Wokwi para análise de pinos

## 📄 Licença

Este projeto é fornecido como está para fins educacionais e pessoais.

---

**Versão**: 1.0  
**Autor**: Henrique Castro  
