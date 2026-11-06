#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <WebServer.h>
#include <Preferences.h>

// =====================================================
// CONFIGURAÇÃO DO DISPOSITIVO
// =====================================================

// Código deste módulo de rega
const char* DEVICE_CODE = "GGW-B381";

// Endereço da API
const char* API_URL = "";


// =====================================================
// RELÉ
// =====================================================

// GPIO ligado ao módulo relé
const int RELAY_PIN = 26;

// false = HIGH liga o relé
// true  = LOW liga o relé
const bool RELAY_ACTIVE_LOW = false;


// =====================================================
// ACCESS POINT
// =====================================================

const char* AP_PASSWORD = "Green1234";

WebServer server(80);
Preferences preferences;


// =====================================================
// CONFIGURAÇÕES
// =====================================================

const unsigned long HTTP_TIMEOUT = 8000;
const unsigned long INTERVALO_COMANDO = 10000;


// =====================================================
// ESTADO
// =====================================================

bool modoConfiguracao = false;
bool associacaoConfirmada = false;

unsigned long ultimaVerificacao = 0;
unsigned long ultimaVerificacaoAssociacao = 0;

const unsigned long INTERVALO_VERIFICACAO_ASSOCIACAO = 30000;


// =====================================================
// NOME DO ACCESS POINT
// =====================================================

String getAPName() {
    return String(DEVICE_CODE) + "-Setup";
}


// =====================================================
// CONTROLO DO RELÉ
// =====================================================

void ligarRele() {

    if (RELAY_ACTIVE_LOW) {
        digitalWrite(RELAY_PIN, LOW);
    } else {
        digitalWrite(RELAY_PIN, HIGH);
    }

    Serial.println("RELÉ: LIGADO");
}


void desligarRele() {

    if (RELAY_ACTIVE_LOW) {
        digitalWrite(RELAY_PIN, HIGH);
    } else {
        digitalWrite(RELAY_PIN, LOW);
    }

    Serial.println("RELÉ: DESLIGADO");
}


// =====================================================
// GUARDAR WIFI
// =====================================================

void guardarWiFi(const String& ssid, const String& password) {

    preferences.begin("wifi", false);
    preferences.putString("ssid", ssid);
    preferences.putString("password", password);
    preferences.end();

    Serial.println("Credenciais WiFi guardadas.");
}


// =====================================================
// APAGAR WIFI
// =====================================================

void apagarWiFi() {

    preferences.begin("wifi", false);
    preferences.clear();
    preferences.end();

    Serial.println("Credenciais WiFi apagadas.");

    WiFi.disconnect(true, true);
    delay(1000);
}


// =====================================================
// LIGAR AO WIFI GUARDADO
// =====================================================

bool conectarWiFiGuardado() {

    preferences.begin("wifi", true);
    String ssid = preferences.getString("ssid", "");
    String password = preferences.getString("password", "");
    preferences.end();

    if (ssid.length() == 0) {
        Serial.println("Nenhuma rede WiFi configurada.");
        return false;
    }

    Serial.println();
    Serial.println("==============================");
    Serial.println("A LIGAR AO WIFI");
    Serial.println("==============================");
    Serial.print("SSID: ");
    Serial.println(ssid);

    WiFi.mode(WIFI_STA);
    WiFi.begin(ssid.c_str(), password.c_str());

    unsigned long inicio = millis();

    while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
        delay(250);
        Serial.print(".");
    }

    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("WiFi ligado com sucesso!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
        return true;
    }

    Serial.println("Não foi possível ligar ao WiFi.");
    WiFi.disconnect();
    return false;
}

// =====================================================
// VERIFICAR ASSOCIAÇÃO COM A API
// =====================================================

// Retornos:
//  1 = associado
//  0 = desassociado
// -1 = erro de comunicação ou resposta inválida

int verificarAssociacao() {

    HTTPClient http;

    String url = String(API_URL) +
        "/watering-devices/code/" +
        String(DEVICE_CODE);

    Serial.println();
    Serial.println("==============================");
    Serial.println("A VERIFICAR ASSOCIAÇÃO");
    Serial.println("==============================");
    Serial.print("URL: ");
    Serial.println(url);

    http.begin(url);
    http.setTimeout(HTTP_TIMEOUT);

    int codigoHTTP = http.GET();

    if (codigoHTTP != 200) {

        Serial.print("Erro HTTP ao verificar associação: ");
        Serial.println(codigoHTTP);

        http.end();

        return -1;
    }

    String resposta = http.getString();
    http.end();

    Serial.print("Resposta da API: ");
    Serial.println(resposta);

    JsonDocument doc;

    DeserializationError erro = deserializeJson(doc, resposta);

    if (erro) {

        Serial.println(
            "Erro ao interpretar resposta da API."
        );

        return -1;
    }

    bool success = doc["success"] | false;

    if (!success) {

        Serial.println(
            "A API não confirmou a consulta."
        );

        return -1;
    }

    JsonObject dispositivo = doc["watering_device"];

    if (dispositivo.isNull()) {

        Serial.println(
            "Dados do módulo de rega não encontrados na resposta."
        );

        return -1;
    }

    JsonVariant userId = dispositivo["user_id"];
    JsonVariant deviceId = dispositivo["device_id"];

    if (userId.isNull() || deviceId.isNull()) {

        Serial.println();
        Serial.println("MÓDULO DE REGA DESASSOCIADO!");

        return 0;
    }

    Serial.println();
    Serial.println("Módulo de rega associado.");
    Serial.print("User ID: ");
    Serial.println(userId.as<int>());
    Serial.print("Device ID: ");
    Serial.println(deviceId.as<int>());

    return 1;
}


// =====================================================
// ASSOCIAR DISPOSITIVO À API
// =====================================================

bool associarDispositivoComAPI(int userId, int deviceId) {

    HTTPClient http;
    String url = String(API_URL) + "/watering-devices/add";

    Serial.println();
    Serial.println("==============================");
    Serial.println("ASSOCIAÇÃO À API");
    Serial.println("==============================");
    Serial.print("URL: "); Serial.println(url);
    Serial.print("Código: "); Serial.println(DEVICE_CODE);
    Serial.print("User ID: "); Serial.println(userId);
    Serial.print("Device ID: "); Serial.println(deviceId);

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT);

    JsonDocument doc;
    doc["code"] = DEVICE_CODE;
    doc["user_id"] = userId;
    doc["device_id"] = deviceId;

    String payload;
    serializeJson(doc, payload);
    Serial.print("Payload: "); Serial.println(payload);

    int codigoHTTP = http.POST(payload);
    String resposta = http.getString();

    Serial.print("HTTP: "); Serial.println(codigoHTTP);
    Serial.print("Resposta: "); Serial.println(resposta);

    http.end();

    if (codigoHTTP < 200 || codigoHTTP >= 300) {
        Serial.println("Falha na associação.");
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
        const char* mensagem = respostaDoc["message"] | "Associação recusada pela API.";
        Serial.print("API recusou: "); Serial.println(mensagem);
        return false;
    }

    Serial.println("Módulo de rega associado com sucesso!");
    return true;
}


// =====================================================
// ENDPOINT /wifi
// =====================================================

void configurarWiFiPeloApp() {

    Serial.println();
    Serial.println("==============================");
    Serial.println("CONFIGURAÇÃO RECEBIDA DA APP");
    Serial.println("==============================");

    if (!server.hasArg("plain")) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Dados não recebidos.\"}");
        return;
    }

    String body = server.arg("plain");
    Serial.print("JSON: "); Serial.println(body);

    JsonDocument doc;
    DeserializationError erro = deserializeJson(doc, body);

    if (erro) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"JSON inválido.\"}");
        return;
    }

    const char* ssid = doc["ssid"];
    const char* password = doc["password"];

    if (ssid == nullptr || password == nullptr || strlen(ssid) == 0) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"SSID ou password inválidos.\"}");
        return;
    }

    if (doc["user_id"].isNull()) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"User ID não recebido.\"}");
        return;
    }

    if (doc["device_id"].isNull()) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"Device ID não recebido.\"}");
        return;
    }

    int userId = doc["user_id"].as<int>();
    int deviceId = doc["device_id"].as<int>();

    if (userId <= 0 || deviceId <= 0) {
        server.send(400, "application/json", "{\"success\":false,\"message\":\"IDs inválidos.\"}");
        return;
    }

    Serial.print("SSID: "); Serial.println(ssid);
    Serial.print("User ID: "); Serial.println(userId);
    Serial.print("Device ID: "); Serial.println(deviceId);

    // =================================================
    // LIGAR AO WIFI
    // =================================================

    WiFi.mode(WIFI_AP_STA);
    WiFi.begin(ssid, password);

    unsigned long inicio = millis();

    while (WiFi.status() != WL_CONNECTED && millis() - inicio < 15000) {
        server.handleClient();
        delay(250);
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("Falha ao ligar ao WiFi.");
        server.send(200, "application/json", "{\"success\":false,\"message\":\"Não foi possível ligar ao WiFi.\"}");
        return;
    }

    Serial.println("WiFi ligado!");
    Serial.print("IP: "); Serial.println(WiFi.localIP());

    delay(500);

    // =================================================
    // ASSOCIAR NA API
    // =================================================

    bool associado = associarDispositivoComAPI(userId, deviceId);

    if (!associado) {
        Serial.println("Associação falhou.");
        WiFi.disconnect(false, false);
        server.send(200, "application/json", "{\"success\":false,\"message\":\"Não foi possível associar o módulo de rega.\"}");
        return;
    }

    // =================================================
    // GUARDAR WIFI
    // =================================================

    guardarWiFi(String(ssid), String(password));

    // =================================================
    // RESPONDER À APP
    // =================================================

    server.send(200, "application/json", "{\"success\":true,\"message\":\"Módulo de rega configurado com sucesso.\"}");

    Serial.println("Configuração concluída.");

    delay(2500);

    Serial.println("A reiniciar ESP32...");
    ESP.restart();
}


// =====================================================
// INICIAR PORTAL WIFI
// =====================================================

void iniciarPortalWiFi() {

    Serial.println();
    Serial.println("==============================");
    Serial.println("PORTAL DE CONFIGURAÇÃO");
    Serial.println("==============================");

    WiFi.disconnect(true, true);
    delay(500);
    WiFi.mode(WIFI_AP);

    String apName = getAPName();
    bool resultado = WiFi.softAP(apName.c_str(), AP_PASSWORD);

    if (!resultado) {
        Serial.println("ERRO AO CRIAR ACCESS POINT.");
        return;
    }

    IPAddress ip = WiFi.softAPIP();

    Serial.print("Rede: "); Serial.println(apName);
    Serial.print("Password: "); Serial.println(AP_PASSWORD);
    Serial.print("IP: "); Serial.println(ip);

    server.on("/wifi", HTTP_POST, configurarWiFiPeloApp);
    server.on("/", HTTP_GET, []() {
        server.send(200, "text/plain", "GreenGadget Watering ESP32");
    });

    server.begin();

    Serial.println("Servidor HTTP iniciado.");
    Serial.println("A aguardar configuração da aplicação...");
}


// =====================================================
// AGUARDAR CONFIGURAÇÃO
// =====================================================

void aguardarConfiguracaoWiFi() {

    iniciarPortalWiFi();

    while (WiFi.status() != WL_CONNECTED) {
        server.handleClient();
        delay(2);
    }
}


// =====================================================
// OBTER COMANDO DE REGA
// =====================================================

bool obterComandoRega(int& commandId, int& durationSeconds) {

    HTTPClient http;
    String url = String(API_URL) + "/watering-devices/code/" + String(DEVICE_CODE) + "/command";

    Serial.println();
    Serial.println("A verificar comandos de rega...");

    http.begin(url);
    http.setTimeout(HTTP_TIMEOUT);

    int codigoHTTP = http.GET();

    if (codigoHTTP != 200) {
        Serial.print("Erro HTTP: "); Serial.println(codigoHTTP);
        http.end();
        return false;
    }

    String resposta = http.getString();
    http.end();

    Serial.print("Resposta: "); Serial.println(resposta);

    JsonDocument doc;
    DeserializationError erro = deserializeJson(doc, resposta);

    if (erro) {
        Serial.println("Erro ao interpretar resposta.");
        return false;
    }

    bool success = doc["success"] | false;
    if (!success) return false;

    JsonVariant command = doc["command"];
    if (command.isNull()) return false;

    commandId = command["id"] | 0;
    durationSeconds = command["duration_seconds"] | 0;

    if (commandId <= 0 || durationSeconds <= 0) {
        Serial.println("Comando inválido.");
        return false;
    }

    Serial.println();
    Serial.println("==============================");
    Serial.println("COMANDO ENCONTRADO");
    Serial.println("==============================");
    Serial.print("Command ID: "); Serial.println(commandId);
    Serial.print("Duração: "); Serial.print(durationSeconds); Serial.println(" segundos");

    return true;
}


// =====================================================
// CONCLUIR COMANDO
// =====================================================

bool concluirComando(int commandId) {

    HTTPClient http;
    String url = String(API_URL) + "/watering-devices/code/" + String(DEVICE_CODE) + "/command/" + String(commandId) + "/complete";

    Serial.println();
    Serial.println("A marcar comando como executado...");

    http.begin(url);
    http.addHeader("Content-Type", "application/json");
    http.setTimeout(HTTP_TIMEOUT);

    int codigoHTTP = http.POST("{}");
    String resposta = http.getString();

    Serial.print("HTTP: "); Serial.println(codigoHTTP);
    Serial.print("Resposta: "); Serial.println(resposta);

    http.end();

    if (codigoHTTP >= 200 && codigoHTTP < 300) {
        Serial.println("Comando concluído.");
        return true;
    }

    Serial.println("Falha ao concluir comando.");
    return false;
}


// =====================================================
// EXECUTAR REGA
// =====================================================

void executarRega(int commandId, int durationSeconds) {

    Serial.println();
    Serial.println("==============================");
    Serial.println("A INICIAR REGA");
    Serial.println("==============================");
    Serial.print("Duração: "); Serial.print(durationSeconds); Serial.println(" segundos");

    ligarRele();

    unsigned long inicio = millis();
    unsigned long duracao = (unsigned long)durationSeconds * 1000UL;

    while (millis() - inicio < duracao) {

        unsigned long restante = duracao - (millis() - inicio);
        int segundosRestantes = (restante + 999) / 1000;

        static unsigned long ultimoPrint = 0;
        if (millis() - ultimoPrint > 1000) {
            Serial.print("Restante: ");
            Serial.print(segundosRestantes);
            Serial.println(" segundos");
            ultimoPrint = millis();
        }

        delay(250);
        yield();
    }

    desligarRele();
    Serial.println("Rega terminada.");

    concluirComando(commandId);

    delay(1500);
}


// =====================================================
// VERIFICAR COMANDOS
// =====================================================

void verificarComandos() {

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("WiFi desligado.");
        return;
    }

    int commandId = 0;
    int durationSeconds = 0;

    bool existeComando = obterComandoRega(commandId, durationSeconds);

    if (!existeComando) {
        Serial.println("Nenhum comando pendente.");
        return;
    }

    executarRega(commandId, durationSeconds);
}


// =====================================================
// SETUP
// =====================================================

void setup() {

    Serial.begin(115200);
    delay(1000);

    Serial.println();
    Serial.println();
    Serial.println("================================");
    Serial.println("GREEN GADGET - MÓDULO DE REGA");
    Serial.println("================================");
    Serial.print("Código: ");
    Serial.println(DEVICE_CODE);

    // =================================================
    // RELÉ
    // =================================================

    pinMode(RELAY_PIN, OUTPUT);
    desligarRele();

    // =================================================
    // WIFI
    // =================================================

    bool conectado = conectarWiFiGuardado();

    if (!conectado) {

        modoConfiguracao = true;

        aguardarConfiguracaoWiFi();

        modoConfiguracao = false;
    }

    if (WiFi.status() != WL_CONNECTED) {

        Serial.println("WiFi não está ligado.");
        return;
    }

    Serial.println();
    Serial.println("================================");
    Serial.println("WIFI LIGADO");
    Serial.println("================================");

    Serial.print("IP: ");
    Serial.println(WiFi.localIP());

    // =================================================
    // VERIFICAR ASSOCIAÇÃO
    // =================================================

    int estadoAssociacao = verificarAssociacao();

    if (estadoAssociacao == 0) {

        Serial.println();
        Serial.println("Módulo desassociado.");
        Serial.println("A apagar credenciais WiFi...");

        apagarWiFi();

        modoConfiguracao = true;

        aguardarConfiguracaoWiFi();

        modoConfiguracao = false;

        return;
    }

    if (estadoAssociacao == 1) {

        associacaoConfirmada = true;

        ultimaVerificacaoAssociacao = millis();

        Serial.println();
        Serial.println("================================");
        Serial.println("MÓDULO DE REGA PRONTO");
        Serial.println("================================");
    }

    if (estadoAssociacao == -1) {

        associacaoConfirmada = false;

        Serial.println();
        Serial.println(
            "Não foi possível confirmar a associação."
        );

        Serial.println(
            "O módulo ficará em segurança e tentará novamente."
        );
    }

    delay(1000);
}


// =====================================================
// LOOP
// =====================================================

void loop() {

    if (modoConfiguracao) {

        server.handleClient();

        delay(2);

        return;
    }

    // =================================================
    // VERIFICAR WIFI
    // =================================================

    if (WiFi.status() != WL_CONNECTED) {

        associacaoConfirmada = false;

        Serial.println("WiFi perdido.");

        WiFi.reconnect();

        unsigned long inicio = millis();

        while (
            WiFi.status() != WL_CONNECTED &&
            millis() - inicio < 10000
        ) {
            delay(250);
        }

        if (WiFi.status() != WL_CONNECTED) {

            Serial.println(
                "Não foi possível reconectar."
            );

            delay(5000);

            return;
        }

        Serial.println("WiFi reconectado!");

        // Forçar nova verificação da associação
        ultimaVerificacaoAssociacao = 0;
    }

    // =================================================
    // VERIFICAR ASSOCIAÇÃO PERIODICAMENTE
    // =================================================

    if (
        millis() - ultimaVerificacaoAssociacao >=
        INTERVALO_VERIFICACAO_ASSOCIACAO
    ) {

        ultimaVerificacaoAssociacao = millis();

        int estadoAssociacao = verificarAssociacao();

        if (estadoAssociacao == 0) {

            Serial.println();
            Serial.println(
                "DESASSOCIAÇÃO DETETADA!"
            );

            associacaoConfirmada = false;

            // Garantir que o relé está desligado
            desligarRele();

            // Apagar credenciais WiFi
            apagarWiFi();

            // Abrir portal de configuração
            modoConfiguracao = true;

            aguardarConfiguracaoWiFi();

            modoConfiguracao = false;

            return;
        }

        if (estadoAssociacao == 1) {

            associacaoConfirmada = true;

        } else {

            associacaoConfirmada = false;

            Serial.println(
                "Associação não confirmada. "
                "Comandos de rega bloqueados."
            );
        }
    }

    // =================================================
    // CONSULTAR COMANDOS DE REGA
    // =================================================

    if (!associacaoConfirmada) {

        delay(100);

        return;
    }

    if (millis() - ultimaVerificacao >= INTERVALO_COMANDO) {

        ultimaVerificacao = millis();

        verificarComandos();
    }

    delay(10);
}