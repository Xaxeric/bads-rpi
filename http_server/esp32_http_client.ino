/*
ESP32 HTTP Camera Client
Connects to Flask HTTP server and displays images on TFT LCD

Hardware Requirements:
- ESP32 development board
- TFT LCD 240x320 (ST7789 or ILI9341)
- WiFi connection

Libraries needed:
- WiFi.h
- HTTPClient.h
- TJpg_Decoder (for JPEG decoding)
- TFT_eSPI (for display)

Install via Arduino Library Manager:
- TJpg_Decoder by Bodmer
- TFT_eSPI by Bodmer
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include <TJpg_Decoder.h>
#include <TFT_eSPI.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Raspberry Pi server settings
const char* serverIP = "192.168.1.XXX";  // Replace with your Pi's IP
const int serverPort = 5000;
const char* frameEndpoint = "/frame";

// Display setup
TFT_eSPI tft = TFT_eSPI();

// HTTP client
HTTPClient http;
WiFiClient client;

// Timing
unsigned long lastFrameTime = 0;
const unsigned long frameInterval = 500; // 500ms = ~2 FPS

void setup() {
  Serial.begin(115200);
  
  // Initialize display
  tft.init();
  tft.setRotation(0); // Portrait mode for 240x320
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  
  // Show startup message
  tft.setCursor(10, 10);
  tft.println("ESP32 Camera Client");
  tft.setCursor(10, 30);
  tft.println("Connecting to WiFi...");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
    tft.print(".");
  }
  
  Serial.println("WiFi connected!");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(10, 10);
  tft.println("WiFi Connected!");
  tft.setCursor(10, 30);
  tft.print("IP: ");
  tft.println(WiFi.localIP());
  
  // Initialize JPEG decoder
  TJpgDec.setJpgScale(1); // No scaling
  TJpgDec.setCallback(tft_output);
  
  delay(2000); // Show connection info
  tft.fillScreen(TFT_BLACK);
}

void loop() {
  unsigned long currentTime = millis();
  
  // Check if it's time for a new frame
  if (currentTime - lastFrameTime >= frameInterval) {
    fetchAndDisplayFrame();
    lastFrameTime = currentTime;
  }
  
  delay(10); // Small delay to prevent busy waiting
}

void fetchAndDisplayFrame() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected");
    return;
  }
  
  // Construct URL
  String url = "http://" + String(serverIP) + ":" + String(serverPort) + String(frameEndpoint);
  
  // Make HTTP request
  http.begin(client, url);
  http.setTimeout(5000); // 5 second timeout
  
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == HTTP_CODE_OK) {
    // Get the response as a stream
    WiFiClient* stream = http.getStreamPtr();
    int contentLength = http.getSize();
    
    if (contentLength > 0) {
      // Read JPEG data
      uint8_t* jpegBuffer = (uint8_t*)malloc(contentLength);
      if (jpegBuffer != nullptr) {
        
        int bytesRead = 0;
        while (bytesRead < contentLength && stream->available()) {
          int bytesToRead = min(1024, contentLength - bytesRead);
          int actualBytes = stream->readBytes(jpegBuffer + bytesRead, bytesToRead);
          bytesRead += actualBytes;
          
          if (actualBytes == 0) break; // Timeout or connection closed
        }
        
        if (bytesRead == contentLength) {
          // Decode and display JPEG
          TJpgDec.drawJpg(0, 0, jpegBuffer, contentLength);
          Serial.printf("Frame displayed: %d bytes\n", contentLength);
        } else {
          Serial.printf("Incomplete frame: %d/%d bytes\n", bytesRead, contentLength);
        }
        
        free(jpegBuffer);
      } else {
        Serial.println("Failed to allocate JPEG buffer");
      }
    }
  } else {
    Serial.printf("HTTP error: %d\n", httpResponseCode);
    
    // Show error on display
    tft.fillRect(0, 0, 240, 20, TFT_RED);
    tft.setTextColor(TFT_WHITE);
    tft.setCursor(5, 5);
    tft.printf("HTTP Error: %d", httpResponseCode);
  }
  
  http.end();
}

// Callback function for TJpg_Decoder
bool tft_output(int16_t x, int16_t y, uint16_t w, uint16_t h, uint16_t* bitmap) {
  // This function is called by TJpg_Decoder to output decoded image blocks
  if (y >= tft.height()) return 0;
  
  tft.pushImage(x, y, w, h, bitmap);
  return 1;
}

/*
Installation Instructions:

1. Install required libraries in Arduino IDE:
   - TJpg_Decoder by Bodmer
   - TFT_eSPI by Bodmer

2. Configure TFT_eSPI for your display:
   - Edit TFT_eSPI library's User_Setup.h
   - Uncomment your display driver (e.g., #define ST7789_DRIVER)
   - Set pin connections

3. Update WiFi credentials and server IP in this code

4. Upload to ESP32

Usage:
- The ESP32 will connect to WiFi
- Fetch JPEG frames from Pi HTTP server every 500ms
- Display on TFT LCD with face detection boxes if enabled

Server Endpoints:
- Single frame: http://pi-ip:5000/frame
- MJPEG stream: http://pi-ip:5000/stream  
- Server info: http://pi-ip:5000/info
*/