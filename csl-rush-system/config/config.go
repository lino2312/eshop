package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

type Config struct {
	Server   ServerConfig   `yaml:"server"`
	Product  ProductConfig  `yaml:"product"`
	Accounts []Account      `yaml:"accounts"`
	Client   ClientConfig   `yaml:"client"`
}

type ServerConfig struct {
	Port            int `yaml:"port"`
	CheckIntervalMs int `yaml:"check_interval_ms"`
}

type ProductConfig struct {
	Name    string `yaml:"name"`
	URL     string `yaml:"url"`
	PID     string `yaml:"pid"`
	Color   string `yaml:"color"`
	Storage string `yaml:"storage"`
}

type Account struct {
	Username string `yaml:"username"`
	Password string `yaml:"password"`
}

type ClientConfig struct {
	ServerURL        string `yaml:"server_url"`
	Headless         bool   `yaml:"headless"`
	PurchaseQuantity int    `yaml:"purchase_quantity"`
}

func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read config file: %w", err)
	}

	var cfg Config
	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	return &cfg, nil
}
