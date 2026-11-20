package protocol

import "time"

type MessageType string

const (
	TypeStockAlert   MessageType = "stock_alert"
	TypeClientReady  MessageType = "client_ready"
	TypeOrderResult  MessageType = "order_result"
	TypeHeartbeat    MessageType = "heartbeat"
)

type Message struct {
	Type      MessageType `json:"type"`
	Timestamp time.Time   `json:"timestamp"`
	Data      interface{} `json:"data"`
}

type StockAlert struct {
	ProductName string `json:"product_name"`
	Color       string `json:"color"`
	Storage     string `json:"storage"`
	Available   bool   `json:"available"`
}

type ClientReady struct {
	ClientID string `json:"client_id"`
	Username string `json:"username"`
}

type OrderResult struct {
	ClientID  string `json:"client_id"`
	Success   bool   `json:"success"`
	Message   string `json:"message"`
	OrderID   string `json:"order_id,omitempty"`
}
