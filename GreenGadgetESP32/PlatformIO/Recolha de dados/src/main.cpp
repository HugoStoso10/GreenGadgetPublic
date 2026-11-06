#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <SSD1306Wire.h>
#include <DHT.h>
#include <esp_task_wdt.h>
#include <esp_sleep.h>
#include <WebServer.h>
#include <Preferences.h>

// =====================================================
// CONFIGURAÇÃO DO DISPOSITIVO
// =====================================================

// ID deste dispositivo na base de dados
const int DEVICE_ID = 13;

// Código deste dispositivo
const char* DEVICE_CODE = "GG-A7F2";

// Endereço da API
const char* API_URL = "";

// Intervalo entre ciclos completos (deep sleep), em minutos
const uint64_t INTERVALO_MINUTOS = 1;


// =====================================================
// PINOS DOS SENSORES
// =====================================================

#define PINO_DHT        13
#define PINO_SOLO_ADC   32
#define PINO_SOLO_VCC   25

DHT dht(PINO_DHT, DHT11);

// Calibração do KS0049
const int SOLO_SECO_RAW    = 0;
const int SOLO_MOLHADO_RAW = 1800;


// =====================================================
// CONFIGURAÇÃO DO OLED
// =====================================================

#define OLED_SDA 4
#define OLED_SCL 15
#define OLED_RST 16

SSD1306Wire display(0x3c, OLED_SDA, OLED_SCL);


// =====================================================
// CONFIGURAÇÃO DO ACCESS POINT
// =====================================================

const char* AP_PASSWORD = "Green1234";

String getAPName() {
  return String(DEVICE_CODE) + "-Setup";
}

WebServer server(80);
Preferences preferences;


// =====================================================
// TIMEOUTS
// =====================================================

const uint32_t HTTP_TIMEOUT_MS = 8000;
const uint32_t WATCHDOG_TIMEOUT_S = 60;

RTC_DATA_ATTR int totalCiclos = 0;


// =====================================================
// MOSTRAR INFORMAÇÃO DO PORTAL
// =====================================================

void mostrarInfoPortal() {

  display.clear();
  display.setFont(ArialMT_Plain_10);

  String apName = getAPName();

  display.drawString(0, 0, DEVICE_CODE);
  display.drawString(0, 18, "WiFi: " + apName);
  display.drawString(0, 36, "PW: " + String(AP_PASSWORD));

  display.display();
}


// =====================================================
// MOSTRAR WI-FI LIGADO
// =====================================================

void mostrarInfoLigado() {

  display.clear();
  display.setFont(ArialMT_Plain_10);

  display.drawString(0, 0, "WiFi conectado:");
  display.drawString(0, 20, WiFi.SSID());
  display.drawString(0, 40, "IP:");
  display.drawString(0, 52, WiFi.localIP().toString());

  display.display();
}


// =====================================================
// INICIALIZAR OLED
// =====================================================

void iniciarEcra() {

  pinMode(OLED_RST, OUTPUT);

  digitalWrite(OLED_RST, LOW);
  delay(50);

  digitalWrite(OLED_RST, HIGH);

  display.init();
  display.flipScreenVertically();
  display.clear();
  display.setFont(ArialMT_Plain_10);

  display.drawString(0, 0, "GreenGadget ESP32");
  display.drawString(0, 16, "A iniciar...");

  display.display();
}


// =====================================================
// CONFIGURAR WATCHDOG
// =====================================================

void configurarWatchdog() {

  esp_task_wdt_init(WATCHDOG_TIMEOUT_S, true);
  esp_task_wdt_add(NULL);
}


// =====================================================
// APAGAR CONFIGURAÇÃO WI-FI
// =====================================================

void apagarWiFi() {

  Serial.println();
  Serial.println("==============================");
  Serial.println("DISPOSITIVO DESASSOCIADO");
  Serial.println("==============================");

  display.clear();
  display.setFont(ArialMT_Plain_10);

  display.drawString(0, 0, "Dispositivo");
  display.drawString(0, 14, "desassociado!");
  display.drawString(0, 32, "A apagar WiFi...");

  display.display();

  delay(1500);

  preferences.begin("wifi", false);
  preferences.clear();
  preferences.end();

  WiFi.disconnect(true, true);

  delay(1000);

  display.clear();
  display.drawString(0, 0, "WiFi apagado!");
  display.drawString(0, 16, "A reiniciar...");
  display.display();

  delay(2000);

  ESP.restart();
}


// =====================================================
// CONECTAR À REDE GUARDADA
// =====================================================

bool conectarWiFiGuardado() {

  preferences.begin("wifi", true);

  String ssid = preferences.getString("ssid", "");
  String password = preferences.getString("password", "");

  preferences.end();

  if (ssid.length() == 0) {

    Serial.println("Nenhuma rede WiFi guardada.");

    return false;
  }

  Serial.println();
  Serial.println("A ligar à rede WiFi guardada...");
  Serial.print("SSID: ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid.c_str(), password.c_str());

  uint32_t inicio = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - inicio < 15000) {

    delay(250);

    Serial.print(".");
  }

  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {

    Serial.println("WiFi ligado!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    mostrarInfoLigado();

    return true;
  }

  Serial.println("Não foi possível ligar à rede guardada.");

  WiFi.disconnect();

  return false;
}


// =====================================================
// ENDPOINT /wifi
//
// Recebe da aplicação:
// {
//     "ssid": "...",
//     "password": "..."
// }
//
// =====================================================

bool associarDispositivoComAPI(int userId) {

  HTTPClient http;

  String url = String(API_URL) + "/devices/add";

  Serial.println();
  Serial.println("A associar dispositivo à API...");
  Serial.print("URL: ");
  Serial.println(url);
  Serial.print("Device code: ");
  Serial.println(DEVICE_CODE);
  Serial.print("User ID: ");
  Serial.println(userId);

  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(HTTP_TIMEOUT_MS);

  JsonDocument doc;
  doc["code"] = DEVICE_CODE;
  doc["user_id"] = userId;

  String payload;
  serializeJson(doc, payload);

  Serial.print("POST /devices/add: ");
  Serial.println(payload);

  int codigoHTTP = http.POST(payload);
  String resposta = http.getString();

  Serial.print("Resposta API (HTTP ");
  Serial.print(codigoHTTP);
  Serial.println("):");
  Serial.println(resposta);

  http.end();

  if (codigoHTTP < 200 || codigoHTTP >= 300) {
    Serial.printf("Falha ao associar dispositivo (HTTP %d).\\n", codigoHTTP);
    return false;
  }

  JsonDocument respostaDoc;
  DeserializationError erro = deserializeJson(respostaDoc, resposta);

  if (erro) {
    Serial.println("Erro ao interpretar resposta da API.");
    return false;
  }

  bool success = respostaDoc["success"] | false;

  if (!success) {
    const char* mensagem = respostaDoc["message"] | "Não foi possível associar o dispositivo.";
    Serial.print("API recusou a associação: ");
    Serial.println(mensagem);
    return false;
  }

  Serial.println("Dispositivo associado à API com sucesso!");
  return true;
}


// =====================================================
// ENDPOINT /wifi
//
// Recebe da aplicação:
// {
//     "ssid": "...",
//     "password": "...",
//     "user_id": 123
// }
//
// O ESP32 liga-se à rede WiFi e, usando essa ligação,
// associa diretamente o dispositivo ao utilizador na API.
// =====================================================

void configurarWiFiPeloApp() {

  Serial.println();
  Serial.println("==============================");
  Serial.println("PEDIDO DE CONFIGURAÇÃO WIFI");
  Serial.println("==============================");

  if (!server.hasArg("plain")) {

    server.send(
      400,
      "application/json",
      "{\"success\":false,\"message\":\"Dados WiFi não recebidos.\"}"
    );

    return;
  }

  String body = server.arg("plain");

  Serial.print("JSON recebido: ");
  Serial.println(body);

  JsonDocument doc;

  DeserializationError erro = deserializeJson(doc, body);

  if (erro) {

    Serial.print("Erro JSON: ");
    Serial.println(erro.c_str());

    server.send(
      400,
      "application/json",
      "{\"success\":false,\"message\":\"JSON inválido.\"}"
    );

    return;
  }

  const char* ssid = doc["ssid"];
  const char* password = doc["password"];

  if (ssid == nullptr || password == nullptr ||
      strlen(ssid) == 0) {

    server.send(
      400,
      "application/json",
      "{\"success\":false,\"message\":\"SSID ou password inválidos.\"}"
    );

    return;
  }

  if (doc["user_id"].isNull()) {

    server.send(
      400,
      "application/json",
      "{\"success\":false,\"message\":\"User ID não recebido.\"}"
    );

    return;
  }

  int userId = doc["user_id"].as<int>();

  if (userId <= 0) {

    server.send(
      400,
      "application/json",
      "{\"success\":false,\"message\":\"User ID inválido.\"}"
    );

    return;
  }

  Serial.print("SSID recebido: ");
  Serial.println(ssid);

  Serial.print("User ID recebido: ");
  Serial.println(userId);

  Serial.println("A testar ligação à rede...");

  // Mantemos o AP ativo enquanto o ESP32 se liga à rede.
  // Assim, a aplicação continua ligada ao ESP32.
  WiFi.mode(WIFI_AP_STA);
  WiFi.begin(ssid, password);

  uint32_t inicio = millis();

  while (WiFi.status() != WL_CONNECTED &&
         millis() - inicio < 15000) {

    server.handleClient();
    delay(250);
    Serial.print(".");
    esp_task_wdt_reset();
  }

  Serial.println();

  if (WiFi.status() != WL_CONNECTED) {

    Serial.println("Falha ao ligar à rede.");

    WiFi.disconnect(false, false);

    server.send(
      200,
      "application/json",
      "{\"success\":false,\"message\":\"Não foi possível ligar à rede WiFi.\"}"
    );

    return;
  }

  Serial.println("WiFi configurado com sucesso!");
  Serial.print("IP atribuído: ");
  Serial.println(WiFi.localIP());

  // Pequena espera para garantir que a ligação IP está pronta.
  delay(500);

  // IMPORTANTE:
  // O ESP32 faz agora a associação diretamente à API.
  // A aplicação não precisa de conseguir chegar à Internet.
  bool associado = associarDispositivoComAPI(userId);

  if (!associado) {

    Serial.println("A associação falhou.");

    // Não guardamos as credenciais se a associação falhar.
    WiFi.disconnect(false, false);

    server.send(
      200,
      "application/json",
      "{\"success\":false,\"message\":\"Não foi possível associar o dispositivo. Verifique a ligação à Internet ou se o dispositivo já está associado.\"}"
    );

    return;
  }

  // Guardar credenciais apenas depois de confirmar:
  // 1. WiFi funciona
  // 2. Dispositivo foi associado à conta
  preferences.begin("wifi", false);

  preferences.putString("ssid", ssid);
  preferences.putString("password", password);

  preferences.end();

  // =========================================================
  // RESPONDER À APLICAÇÃO
  // =========================================================
 

  Serial.println("Associação concluída com sucesso.");
  Serial.println("A enviar confirmação para a aplicação...");

  String respostaSucesso =
    "{\"success\":true,"
    "\"message\":\"Dispositivo associado com sucesso.\"}";

  server.send(
    200,
    "application/json",
    respostaSucesso
  );

  Serial.println("Resposta enviada à aplicação.");

  // Dar tempo para a ligação HTTP da aplicação terminar.
  delay(2500);

  Serial.println();
  Serial.println("==============================");
  Serial.println("ASSOCIAÇÃO CONCLUÍDA");
  Serial.println("A reiniciar...");
  Serial.println("==============================");

  delay(500);

  ESP.restart();
}


// =====================================================
// INICIAR ACCESS POINT
// =====================================================

void iniciarPortalWiFi() {

  Serial.println();
  Serial.println("==============================");
  Serial.println("A INICIAR PORTAL WIFI");
  Serial.println("==============================");

  WiFi.disconnect(true, true);

  delay(500);

  WiFi.mode(WIFI_AP);

  String apName = getAPName();

  bool resultado = WiFi.softAP(
    apName.c_str(),
    AP_PASSWORD
  );

  if (!resultado) {

    Serial.println("ERRO ao iniciar Access Point.");

    return;
  }

  IPAddress ip = WiFi.softAPIP();

  Serial.print("AP iniciado: ");
  Serial.println(apName);

  Serial.print("IP do ESP32: ");
  Serial.println(ip);

  mostrarInfoPortal();

  // Endpoint usado pela aplicação GreenGadget.
  server.on(
    "/wifi",
    HTTP_POST,
    configurarWiFiPeloApp
  );

  // Endpoint simples para testar no browser.
  server.on(
    "/",
    HTTP_GET,
    []() {

      server.send(
        200,
        "text/plain",
        "GreenGadget ESP32"
      );
    }
  );

  server.begin();

  Serial.println("Servidor HTTP iniciado.");
  Serial.println("POST /wifi disponível.");
}


// =====================================================
// AGUARDAR CONFIGURAÇÃO PELO APP
// =====================================================

bool aguardarConfiguracaoWiFi() {

  iniciarPortalWiFi();

  Serial.println();
  Serial.println("A aguardar configuração através da aplicação...");

  while (WiFi.status() != WL_CONNECTED) {

    server.handleClient();

    delay(2);

    esp_task_wdt_reset();
  }

  return true;
}


// =====================================================
// VERIFICAR ASSOCIAÇÃO COM A API
// =====================================================

bool verificarAssociacao() {

  HTTPClient http;

  String url =
    String(API_URL) +
    "/device/" +
    String(DEVICE_ID);

  Serial.println("A verificar associação...");
  Serial.print("URL: ");
  Serial.println(url);

  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT_MS);

  int codigoHTTP = http.GET();

  if (codigoHTTP != 200) {

    Serial.printf(
      "Erro/aviso ao verificar associação (HTTP %d) — assume associado.\n",
      codigoHTTP
    );

    http.end();

    return true;
  }

  String resposta = http.getString();

  http.end();

  JsonDocument doc;

  DeserializationError erro =
    deserializeJson(doc, resposta);

  if (erro) {

    Serial.println(
      "Erro ao interpretar JSON — assume associado."
    );

    return true;
  }

  bool success = doc["success"] | false;

  if (!success)
    return true;

  JsonObject device = doc["device"];

  if (device.isNull())
    return true;

  JsonVariant userId = device["user_id"];

  if (userId.isNull()) {

    Serial.println(
      "DISPOSITIVO SEM UTILIZADOR!"
    );

    return false;
  }

  Serial.print(
    "Associado ao utilizador: "
  );

  Serial.println(
    userId.as<int>()
  );

  return true;
}


// =====================================================
// LER SENSORES
// =====================================================

struct LeituraSensores {

  float temp_ar;
  float humidade_ar;
  bool ar_ok;

  int humidade_solo_raw;
  float humidade_solo_pct;
  bool solo_ok;
};


LeituraSensores lerSensores() {

  LeituraSensores l;

  // --- AM2302 ---

  l.humidade_ar =
    dht.readHumidity();

  l.temp_ar =
    dht.readTemperature();

  l.ar_ok =
    !isnan(l.humidade_ar) &&
    !isnan(l.temp_ar);

  if (!l.ar_ok) {

    Serial.println(
      "AVISO: falha a ler o AM2302"
    );

    l.temp_ar = 0;
    l.humidade_ar = 0;
  }


  // --- KS0049 ---

  digitalWrite(
    PINO_SOLO_VCC,
    HIGH
  );

  delay(200);

  int soloRaw =
    analogRead(PINO_SOLO_ADC);

  digitalWrite(
    PINO_SOLO_VCC,
    LOW
  );

  l.humidade_solo_raw =
    soloRaw;

  if (soloRaw <= 0 &&
      SOLO_SECO_RAW == 0) {

    l.solo_ok = true;

  } else {

    l.solo_ok = true;
  }


  float pct =
    (float)(
      soloRaw -
      SOLO_SECO_RAW
    ) *
    100.0 /
    (
      SOLO_MOLHADO_RAW -
      SOLO_SECO_RAW
    );

  l.humidade_solo_pct =
    constrain(
      pct,
      0,
      100
    );

  return l;
}


// =====================================================
// ENVIAR DADOS À API
// =====================================================

bool enviarDados(
  const LeituraSensores& l
) {

  HTTPClient http;

  String url =
    String(API_URL) +
    "/devices/data";

  http.begin(url);

  http.addHeader(
    "Content-Type",
    "application/json"
  );

  http.setTimeout(
    HTTP_TIMEOUT_MS
  );

  JsonDocument doc;

  doc["device_code"] =
    DEVICE_CODE;

  doc["temperature"] =
    l.temp_ar;

  doc["air_humidity"] =
    l.humidade_ar;

  doc["soil_humidity"] =
    l.humidade_solo_pct;

  String payload;

  serializeJson(
    doc,
    payload
  );

  Serial.print("A enviar: ");
  Serial.println(payload);

  int codigoHTTP =
    http.POST(payload);

  http.end();

  if (
    codigoHTTP > 0 &&
    codigoHTTP < 300
  ) {

    Serial.printf(
      "Envio OK (HTTP %d)\n",
      codigoHTTP
    );

    return true;
  }

  Serial.printf(
    "Falha no envio (HTTP %d)\n",
    codigoHTTP
  );

  return false;
}


// =====================================================
// DORMIR ATÉ AO PRÓXIMO CICLO
// =====================================================

void irDormir() {

  uint64_t microssegundos =
    INTERVALO_MINUTOS *
    60ULL *
    1000000ULL;

  Serial.printf(
    "A dormir por %llu minutos...\n",
    INTERVALO_MINUTOS
  );

  esp_task_wdt_delete(NULL);

  esp_sleep_enable_timer_wakeup(
    microssegundos
  );

  esp_deep_sleep_start();
}


// =====================================================
// SETUP
// =====================================================

void setup() {

  Serial.begin(115200);

  delay(1000);

  totalCiclos++;

  Serial.printf(
    "\n===== Ciclo #%d =====\n",
    totalCiclos
  );

  configurarWatchdog();

  iniciarEcra();

  dht.begin();

  pinMode(
    PINO_SOLO_VCC,
    OUTPUT
  );

  digitalWrite(
    PINO_SOLO_VCC,
    LOW
  );


  // ===================================================
  // BOTÃO BOOT/PRG
  // ===================================================

  pinMode(
    0,
    INPUT_PULLUP
  );

  bool botaoPremido =
    (digitalRead(0) == LOW);


  if (botaoPremido) {

    Serial.println(
      "Botão BOOT premido — "
      "a apagar rede guardada..."
    );

    preferences.begin(
      "wifi",
      false
    );

    preferences.clear();

    preferences.end();

    WiFi.disconnect(
      true,
      true
    );

    delay(500);
  }


  // ===================================================
  // TENTAR LIGAR À REDE GUARDADA
  // ===================================================

  bool connected = false;

  if (!botaoPremido) {

    connected =
      conectarWiFiGuardado();
  }


  // ===================================================
  // SE NÃO HOUVER REDE, ABRIR PORTAL
  // ===================================================

  if (!connected) {

    aguardarConfiguracaoWiFi();
  }


  // ===================================================
  // GARANTIR QUE ESTÁ LIGADO
  // ===================================================

  if (WiFi.status() != WL_CONNECTED) {

    Serial.println(
      "WiFi não está ligado."
    );

    irDormir();
  }


  Serial.print(
    "Wi-Fi ligado! IP: "
  );

  Serial.println(
    WiFi.localIP()
  );

  mostrarInfoLigado();


  // ===================================================
  // VERIFICAR ASSOCIAÇÃO
  // ===================================================

  bool associado =
    verificarAssociacao();

  if (!associado) {

    apagarWiFi();
  }


  // ===================================================
  // LER SENSORES
  // ===================================================

  LeituraSensores leitura =
    lerSensores();

  Serial.printf(
    "Ar: %.1fC, %.1f%% | Solo: %.1f%% (raw=%d)\n",
    leitura.temp_ar,
    leitura.humidade_ar,
    leitura.humidade_solo_pct,
    leitura.humidade_solo_raw
  );


  // ===================================================
  // ENVIAR DADOS
  // ===================================================

  enviarDados(
    leitura
  );


  // ===================================================
  // DESLIGAR WIFI
  // ===================================================

  WiFi.disconnect(true);

  WiFi.mode(WIFI_OFF);


  // ===================================================
  // DEEP SLEEP
  // ===================================================

  irDormir();
}


void loop() {
}