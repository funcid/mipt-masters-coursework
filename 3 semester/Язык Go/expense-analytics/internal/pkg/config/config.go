package config

import (
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/joho/godotenv"
)

type Config struct {
	AppEnv string

	GatewayHTTPAddr string
	LedgerGRPCAddr  string
	AuthGRPCAddr    string

	PostgresDSN string
	RedisAddr   string
	RedisDB     int

	JWTSecret     string
	JWTExpiresIn  time.Duration
	ReportCacheTTL time.Duration
}

func Load(envFiles ...string) (Config, error) {
	for _, f := range envFiles {
		_ = godotenv.Load(f)
	}

	cfg := Config{
		AppEnv:          getEnv("APP_ENV", "development"),
		GatewayHTTPAddr: getEnv("GATEWAY_HTTP_ADDR", ":8080"),
		LedgerGRPCAddr:  getEnv("LEDGER_GRPC_ADDR", ":9091"),
		AuthGRPCAddr:    getEnv("AUTH_GRPC_ADDR", ":9092"),
		PostgresDSN: getEnv("POSTGRES_DSN",
			"postgres://expense:expense@localhost:5432/expense?sslmode=disable"),
		RedisAddr:      getEnv("REDIS_ADDR", "localhost:6379"),
		RedisDB:        getEnvInt("REDIS_DB", 0),
		JWTSecret:      getEnv("JWT_SECRET", "dev-secret-change-me"),
		JWTExpiresIn:   getEnvDuration("JWT_EXPIRES_IN", 24*time.Hour),
		ReportCacheTTL: getEnvDuration("REPORT_CACHE_TTL", 2*time.Minute),
	}

	if cfg.JWTSecret == "" || cfg.JWTSecret == "change-me" {
		return Config{}, fmt.Errorf("JWT_SECRET must be set")
	}
	return cfg, nil
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return fallback
	}
	return n
}

func getEnvDuration(key string, fallback time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return fallback
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return fallback
	}
	return d
}
