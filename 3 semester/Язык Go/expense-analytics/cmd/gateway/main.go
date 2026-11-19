package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	authv1 "github.com/mipt-masters/expense-analytics/api/gen/auth/v1"
	ledgerv1 "github.com/mipt-masters/expense-analytics/api/gen/ledger/v1"
	"github.com/mipt-masters/expense-analytics/internal/adapter/http/gateway"
	"github.com/mipt-masters/expense-analytics/internal/pkg/config"
	"github.com/mipt-masters/expense-analytics/internal/pkg/jwtutil"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo}))
	cfg, err := config.Load(".env")
	if err != nil {
		log.Error("config", "err", err)
		os.Exit(1)
	}

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	ledgerConn, err := dial(cfg.LedgerGRPCAddr)
	if err != nil {
		log.Error("dial ledger", "err", err)
		os.Exit(1)
	}
	defer ledgerConn.Close()

	authConn, err := dial(cfg.AuthGRPCAddr)
	if err != nil {
		log.Error("dial auth", "err", err)
		os.Exit(1)
	}
	defer authConn.Close()

	tokens := jwtutil.New(cfg.JWTSecret, cfg.JWTExpiresIn)
	h := gateway.NewHandler(
		ledgerv1.NewLedgerServiceClient(ledgerConn),
		authv1.NewAuthServiceClient(authConn),
	)
	router := gateway.NewRouter(h, tokens)

	server := &http.Server{
		Addr:              cfg.GatewayHTTPAddr,
		Handler:           router,
		ReadHeaderTimeout: 5 * time.Second,
	}

	go func() {
		log.Info("gateway HTTP started", "addr", cfg.GatewayHTTPAddr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Error("serve", "err", err)
			stop()
		}
	}()

	<-ctx.Done()
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	_ = server.Shutdown(shutdownCtx)
	log.Info("gateway stopped")
}

func dial(addr string) (*grpc.ClientConn, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	return grpc.DialContext(ctx, addr,
		grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithBlock(),
	)
}
