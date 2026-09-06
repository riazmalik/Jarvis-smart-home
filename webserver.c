#include "webserver.h"
#include "esp_http_server.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "freertos/event_groups.h"
#include "cJSON.h"
#include "relay_control.h"
#include "urdu_voice.h"
#include <string.h>

static const char *TAG = "WEBSERVER";
static EventGroupHandle_t wifi_event_group;
const int WIFI_CONNECTED_BIT = BIT0;

// WiFi credentials - CHANGE THESE
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASS "YOUR_WIFI_PASSWORD"

// Simple HTML page (minified for space)
static const char* HTML_PAGE = "<!DOCTYPE html><html lang=\"ur\" dir=\"rtl\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><title>جاروس - سمارٹ ہوم</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI',Arial,sans-serif;background:#0a0e1a;color:#ccd6f6;padding:20px;text-align:center}.container{max-width:800px;margin:auto}.header{background:linear-gradient(135deg,#64ffda,#b388ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.5rem;margin:20px 0}.subtitle{color:#8892b0;font-size:1.1rem}.btn-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:15px;margin:20px 0}.btn{padding:20px;border:2px solid rgba(255,255,255,0.05);border-radius:15px;background:rgba(255,255,255,0.02);color:#ccd6f6;cursor:pointer;transition:all 0.3s;font-size:1rem}.btn:hover{background:rgba(100,255,218,0.05);transform:translateY(-3px)}.btn.on{border-color:#64ffda;background:rgba(100,255,218,0.1);color:#64ffda}.btn.off{border-color:#ff6b6b;background:rgba(255,107,107,0.08);color:#ff6b6b}.btn .icon{font-size:2rem;display:block;margin-bottom:8px}.master{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin:20px 0}.master-btn{padding:15px 30px;border:none;border-radius:25px;font-size:1.1rem;cursor:pointer;transition:all 0.3s}.master-btn:hover{transform:scale(1.05)}.master-btn.all-on{background:#64ffda;color:#080c18}.master-btn.all-off{background:#ff6b6b;color:#080c18}.status-bar{background:rgba(255,255,255,0.02);border-radius:10px;padding:15px;margin:20px 0}.log{background:rgba(0,0,0,0.3);border-radius:10px;padding:10px;max-height:150px;overflow-y:auto;text-align:right;font-size:0.9rem}.log::-webkit-scrollbar{width:4px}.log::-webkit-scrollbar-thumb{background:#64ffda;border-radius:10px}.log-entry{padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.02);color:#8892b0}.log-entry .time{color:#64ffda}.log-entry .urdu{color:#ffd93d}</style></head><body><div class=\"container\"><div class=\"header\">🔌 جاروس سمارٹ ہوم</div><div class=\"subtitle\">🎤 آواز · 🖐️ اشارہ · 🌐 ویب کنٹرول</div><div class=\"status-bar\"><div>💡 روشنی: <span id=\"bulbCount\">0/4</span> آن</div></div><div class=\"btn-grid\" id=\"bulbs\"><div class=\"btn off\" id=\"btn-living\" onclick=\"toggleBulb(0)\"><span class=\"icon\">🛋️</span><span>لونگ روم</span><span id=\"status-living\">بند</span></div><div class=\"btn off\" id=\"btn-bedroom\" onclick=\"toggleBulb(1)\"><span class=\"icon\">🛏️</span><span>بیڈ روم</span><span id=\"status-bedroom\">بند</span></div><div class=\"btn off\" id=\"btn-kitchen\" onclick=\"toggleBulb(2)\"><span class=\"icon\">🍳</span><span>کچن</span><span id=\"status-kitchen\">بند</span></div><div class=\"btn off\" id=\"btn-study\" onclick=\"toggleBulb(3)\"><span class=\"icon\">📚</span><span>سٹڈی</span><span id=\"status-study\">بند</span></div></div><div class=\"master\"><button class=\"master-btn all-on\" onclick=\"allOn()\">💡 سب آن</button><button class=\"master-btn all-off\" onclick=\"allOff()\">💡 سب بند</button></div><div class=\"log\" id=\"logContainer\"><div class=\"log-entry\"><span class=\"time\">[سیسٹم]</span> <span class=\"urdu\">جاروس تیار ہے</span></div></div></div><script>let bulbStates=[false,false,false,false];function updateUI(){const onCount=bulbStates.filter(v=>v).length;document.getElementById('bulbCount').textContent=onCount+'/4';['living','bedroom','kitchen','study'].forEach((name,i)=>{const btn=document.getElementById('btn-'+name);const status=document.getElementById('status-'+name);if(bulbStates[i]){btn.className='btn on';status.textContent='آن';}else{btn.className='btn off';status.textContent='بند';}});}function toggleBulb(index){bulbStates[index]=!bulbStates[index];updateUI();fetch('/api/bulb?index='+index+'&state='+(bulbStates[index]?'on':'off'));addLog('لائٹ '+(bulbStates[index]?'آن':'بند'),'urdu');}function allOn(){bulbStates=[true,true,true,true];updateUI();fetch('/api/bulb?all=on');addLog('سب لائٹس آن','urdu');}function allOff(){bulbStates=[false,false,false,false];updateUI();fetch('/api/bulb?all=off');addLog('سب لائٹس بند','urdu');}function addLog(msg,type){const container=document.getElementById('logContainer');const entry=document.createElement('div');entry.className='log-entry';const time=new Date().toLocaleTimeString('ur-PK');entry.innerHTML='<span class=\"time\">['+time+']</span> <span class=\"'+type+'\">'+msg+'</span>';container.appendChild(entry);if(container.children.length>20)container.removeChild(container.firstChild);container.scrollTop=container.scrollHeight;}fetch('/api/status').then(r=>r.json()).then(data=>{if(data.bulbs){bulbStates=data.bulbs;updateUI();}});</script></body></html>";

// ===== WiFi Event Handler =====
static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                                int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        esp_wifi_connect();
        xEventGroupClearBits(wifi_event_group, WIFI_CONNECTED_BIT);
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "🌐 Got IP: " IPSTR, IP2STR(&event->ip_info.ip));
        xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void init_wifi(void) {
    wifi_event_group = xEventGroupCreate();
    
    ESP_ERROR_CHECK(esp_netif_init());
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));
    
    esp_event_handler_instance_t instance_any_id;
    esp_event_handler_instance_t instance_got_ip;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_any_id));
    ESP_ERROR_CHECK(esp_event_handler_instance_register(IP_EVENT,
                                                        IP_EVENT_STA_GOT_IP,
                                                        &wifi_event_handler,
                                                        NULL,
                                                        &instance_got_ip));
    
    wifi_config_t wifi_config = {
        .sta = {
            .ssid = "Your Wifi SSID",
            .password = "Your Wifi Password",
        },
    };
    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());
    
    ESP_LOGI(TAG, "📶 WiFi connecting...");
    
    EventBits_t bits = xEventGroupWaitBits(wifi_event_group,
                                           WIFI_CONNECTED_BIT,
                                           pdFALSE,
                                           pdFALSE,
                                           pdMS_TO_TICKS(30000));
    if (bits & WIFI_CONNECTED_BIT) {
        ESP_LOGI(TAG, "✅ WiFi connected!");
    } else {
        ESP_LOGE(TAG, "❌ WiFi connection failed");
    }
}

// ===== HTTP Handlers =====
static esp_err_t root_get_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "text/html");
    httpd_resp_set_hdr(req, "Content-Type", "text/html; charset=utf-8");
    return httpd_resp_send(req, HTML_PAGE, strlen(HTML_PAGE));
}

static esp_err_t bulb_get_handler(httpd_req_t *req) {
    char buf[100];
    size_t len = httpd_req_get_url_query_len(req) + 1;
    if (len > 1) {
        char *query = malloc(len);
        httpd_req_get_url_query_str(req, query, len);
        
        char param[10], value[10];
        
        if (httpd_query_key_value(query, "index", param, sizeof(param)) == ESP_OK) {
            int index = atoi(param);
            if (httpd_query_key_value(query, "state", value, sizeof(value)) == ESP_OK) {
                if (strcmp(value, "on") == 0) {
                    turn_on_bulb(index);
                } else if (strcmp(value, "off") == 0) {
                    turn_off_bulb(index);
                }
            }
        }
        if (httpd_query_key_value(query, "all", param, sizeof(param)) == ESP_OK) {
            if (strcmp(param, "on") == 0) turn_all_on();
            else if (strcmp(param, "off") == 0) turn_all_off();
        }
        free(query);
    }
    httpd_resp_send(req, "OK", 2);
    return ESP_OK;
}

static esp_err_t status_get_handler(httpd_req_t *req) {
    char json[100];
    snprintf(json, sizeof(json), 
             "{\"bulbs\":[%d,%d,%d,%d]}",
             get_bulb_state(0), get_bulb_state(1),
             get_bulb_state(2), get_bulb_state(3));
    httpd_resp_set_type(req, "application/json");
    httpd_resp_send(req, json, strlen(json));
    return ESP_OK;
}

void init_webserver(void) {
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.lru_purge_enable = true;
    
    if (httpd_start(&server, &config) == ESP_OK) {
        httpd_uri_t root_uri = {
            .uri       = "/",
            .method    = HTTP_GET,
            .handler   = root_get_handler,
            .user_ctx  = NULL
        };
        httpd_register_uri_handler(server, &root_uri);
        
        httpd_uri_t bulb_uri = {
            .uri       = "/api/bulb",
            .method    = HTTP_GET,
            .handler   = bulb_get_handler,
            .user_ctx  = NULL
        };
        httpd_register_uri_handler(server, &bulb_uri);
        
        httpd_uri_t status_uri = {
            .uri       = "/api/status",
            .method    = HTTP_GET,
            .handler   = status_get_handler,
            .user_ctx  = NULL
        };
        httpd_register_uri_handler(server, &status_uri);
        
        ESP_LOGI(TAG, "🌐 Web server started on port 80");
    }
}
