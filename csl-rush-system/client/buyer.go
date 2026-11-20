package main

import (
	"context"
	"csl-rush-system/config"
	"csl-rush-system/protocol"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/chromedp/chromedp"
	"github.com/gorilla/websocket"
)

type Client struct {
	username    string
	password    string
	cookies     []*http.Cookie
	httpClient  *http.Client
	wsConn      *websocket.Conn
	targetColor string
	targetROM   string
}

func NewClient(username, password, color, rom string) *Client {
	return &Client{
		username:    username,
		password:    password,
		targetColor: color,
		targetROM:   rom,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) login(ctx context.Context) error {
	log.Println("Starting login with chromedp...")

	opts := append(chromedp.DefaultExecAllocatorOptions[:],
		chromedp.Flag("headless", false),
		chromedp.Flag("disable-gpu", true),
		chromedp.Flag("no-sandbox", true),
	)

	allocCtx, cancel := chromedp.NewExecAllocator(ctx, opts...)
	defer cancel()

	chromeCtx, cancel := chromedp.NewContext(allocCtx)
	defer cancel()

	loginURL := "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Login-Show"

	var cookies []*http.Cookie
	err := chromedp.Run(chromeCtx,
		chromedp.Navigate(loginURL),
		chromedp.Sleep(3*time.Second),
		chromedp.Click(`button.login-email-btn`, chromedp.ByQuery),
		chromedp.Sleep(1*time.Second),
		chromedp.SendKeys(`input[type="email"]`, c.username, chromedp.ByQuery),
		chromedp.Sleep(500*time.Millisecond),
		chromedp.SendKeys(`input[type="password"]`, c.password, chromedp.ByQuery),
		chromedp.Sleep(500*time.Millisecond),
		chromedp.Click(`input[type="checkbox"]`, chromedp.ByQuery),
		chromedp.Sleep(500*time.Millisecond),
		chromedp.Click(`button.btn-primary.js-action`, chromedp.ByQuery),
		chromedp.Sleep(5*time.Second),
		chromedp.ActionFunc(func(ctx context.Context) error {
			cookies, err := chromedp.Cookies(ctx)
			if err != nil {
				return err
			}
			for _, cookie := range cookies {
				c.cookies = append(c.cookies, &http.Cookie{
					Name:  cookie.Name,
					Value: cookie.Value,
				})
			}
			return nil
		}),
	)

	if err != nil {
		return fmt.Errorf("login failed: %w", err)
	}

	log.Printf("Login successful for %s, cookies extracted", c.username)
	return nil
}

func (c *Client) connectWebSocket(serverURL string) error {
	conn, _, err := websocket.DefaultDialer.Dial(serverURL, nil)
	if err != nil {
		return fmt.Errorf("websocket connection failed: %w", err)
	}

	c.wsConn = conn
	log.Println("Connected to monitor server")

	ready := protocol.Message{
		Type:      protocol.TypeClientReady,
		Timestamp: time.Now(),
		Data: protocol.ClientReady{
			ClientID: c.username,
			Username: c.username,
		},
	}

	if err := conn.WriteJSON(ready); err != nil {
		return err
	}

	return nil
}

func (c *Client) addToCart(productPID string) error {
	addURL := "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Cart-AddProduct"

	data := url.Values{}
	data.Set("pid", productPID)
	data.Set("quantity", "2")
	data.Set("options", "[]")

	req, err := http.NewRequest("POST", addURL, strings.NewReader(data.Encode()))
	if err != nil {
		return err
	}

	req.Header.Set("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
	req.Header.Set("X-Requested-With", "XMLHttpRequest")

	for _, cookie := range c.cookies {
		req.AddCookie(cookie)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)

	if resp.StatusCode != 200 {
		return fmt.Errorf("add to cart failed: status %d, body: %s", resp.StatusCode, string(body))
	}

	log.Printf("Successfully added to cart: %s", productPID)
	return nil
}

func (c *Client) checkout() error {
	checkoutURL := "https://eshop.hkcsl.com/on/demandware.store/Sites-hkt-hk-Site/zh_HK/Checkout-Begin?stage=payment"

	req, err := http.NewRequest("GET", checkoutURL, nil)
	if err != nil {
		return err
	}

	for _, cookie := range c.cookies {
		req.AddCookie(cookie)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return fmt.Errorf("checkout failed: status %d", resp.StatusCode)
	}

	log.Println("Successfully navigated to checkout page")
	return nil
}

func (c *Client) listenForAlerts() {
	for {
		var msg protocol.Message
		err := c.wsConn.ReadJSON(&msg)
		if err != nil {
			log.Printf("WebSocket read error: %v", err)
			return
		}

		if msg.Type == protocol.TypeStockAlert {
			log.Println("Stock alert received! Starting purchase...")

			productPID := "IP17scol"

			if err := c.addToCart(productPID); err != nil {
				log.Printf("Failed to add to cart: %v", err)
				continue
			}

			if err := c.checkout(); err != nil {
				log.Printf("Failed to checkout: %v", err)
				continue
			}

			result := protocol.Message{
				Type:      protocol.TypeOrderResult,
				Timestamp: time.Now(),
				Data: protocol.OrderResult{
					ClientID: c.username,
					Success:  true,
					Message:  "Order submitted successfully",
				},
			}

			c.wsConn.WriteJSON(result)
			log.Println("Purchase completed successfully!")
		}
	}
}

func (c *Client) Run(serverURL string) error {
	ctx := context.Background()

	if err := c.login(ctx); err != nil {
		return fmt.Errorf("login failed: %w", err)
	}

	if err := c.connectWebSocket(serverURL); err != nil {
		return fmt.Errorf("websocket connection failed: %w", err)
	}

	log.Println("Client ready, waiting for stock alerts...")
	c.listenForAlerts()

	return nil
}

func main() {
	configPath := flag.String("config", "config/config.yaml", "Path to config file")
	accountIndex := flag.Int("account", 0, "Account index to use (0-based)")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	if *accountIndex >= len(cfg.Accounts) {
		log.Fatalf("Account index %d out of range (total accounts: %d)", *accountIndex, len(cfg.Accounts))
	}

	account := cfg.Accounts[*accountIndex]
	log.Printf("Starting client for account: %s", account.Username)

	client := NewClient(account.Username, account.Password, cfg.Product.Color, cfg.Product.Storage)

	if err := client.Run(cfg.Client.ServerURL); err != nil {
		log.Fatalf("Client error: %v", err)
	}
}
