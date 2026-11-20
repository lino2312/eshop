package main

import (
	"csl-rush-system/config"
	"csl-rush-system/protocol"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type Monitor struct {
	clients    map[*websocket.Conn]bool
	clientsMux sync.RWMutex
	upgrader   websocket.Upgrader
	lastStock  map[string]bool
}

func NewMonitor() *Monitor {
	return &Monitor{
		clients:   make(map[*websocket.Conn]bool),
		lastStock: make(map[string]bool),
		upgrader: websocket.Upgrader{
			CheckOrigin: func(r *http.Request) bool { return true },
		},
	}
}

func (m *Monitor) handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := m.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}

	m.clientsMux.Lock()
	m.clients[conn] = true
	m.clientsMux.Unlock()

	log.Printf("Client connected. Total: %d", len(m.clients))

	defer func() {
		m.clientsMux.Lock()
		delete(m.clients, conn)
		m.clientsMux.Unlock()
		conn.Close()
		log.Printf("Client disconnected. Total: %d", len(m.clients))
	}()

	for {
		_, _, err := conn.ReadMessage()
		if err != nil {
			break
		}
	}
}

func (m *Monitor) broadcast(msg protocol.Message) {
	m.clientsMux.RLock()
	defer m.clientsMux.RUnlock()

	data, _ := json.Marshal(msg)
	for conn := range m.clients {
		if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
			log.Printf("Broadcast error: %v", err)
		}
	}
}

func (m *Monitor) checkStock(productURL, color, storage string) (bool, error) {
	variationURL := fmt.Sprintf("%s?dwvar_%s_color=%s&dwvar_%s_internal_storage_rom=%s",
		productURL, extractPID(productURL), color, extractPID(productURL), storage)

	resp, err := http.Get(variationURL)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return false, fmt.Errorf("status code: %d", resp.StatusCode)
	}

	body, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return false, err
	}

	product, ok := result["product"].(map[string]interface{})
	if !ok {
		return false, fmt.Errorf("invalid response structure")
	}

	available, ok := product["available"].(bool)
	return ok && available, nil
}

func extractPID(url string) string {
	return "IP17scol"
}

func (m *Monitor) startMonitoring(cfg config.ProductConfig, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for range ticker.C {
		available, err := m.checkStock(cfg.URL, cfg.Color, cfg.Storage)
		if err != nil {
			log.Printf("Stock check error: %v", err)
			continue
		}

		key := fmt.Sprintf("%s_%s_%s", cfg.URL, cfg.Color, cfg.Storage)
		if available && !m.lastStock[key] {
			log.Printf("Stock available! %s %s %s", cfg.Name, cfg.Color, cfg.Storage)
			m.broadcast(protocol.Message{
				Type:      protocol.TypeStockAlert,
				Timestamp: time.Now(),
				Data: protocol.StockAlert{
					ProductName: cfg.Name,
					Color:       cfg.Color,
					Storage:     cfg.Storage,
					Available:   true,
				},
			})
		}
		m.lastStock[key] = available
	}
}

func main() {
	configPath := flag.String("config", "config/config.yaml", "Path to config file")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	monitor := NewMonitor()
	http.HandleFunc("/ws", monitor.handleWebSocket)

	interval := time.Duration(cfg.Server.CheckIntervalMs) * time.Millisecond
	go monitor.startMonitoring(cfg.Product, interval)

	addr := fmt.Sprintf(":%d", cfg.Server.Port)
	log.Printf("Monitor server started on %s", addr)
	log.Printf("Monitoring: %s (Color: %s, Storage: %s)", cfg.Product.Name, cfg.Product.Color, cfg.Product.Storage)
	log.Fatal(http.ListenAndServe(addr, nil))
}
