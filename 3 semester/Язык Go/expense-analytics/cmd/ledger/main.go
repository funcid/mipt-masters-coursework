package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	ledgerv1 "github.com/mipt-masters/expense-analytics/api/gen/ledger/v1"
	ledgergrpc "github.com/mipt-masters/expense-analytics/internal/adapter/grpc/ledger"
	"github.com/mipt-masters/expense-analytics/internal/adapter/postgres"
	rediscache "github.com/mipt-masters/expense-analytics/internal/adapter/redis"
	"github.com/mipt-masters/expense-analytics/internal/pkg/config"
	budgetuc "github.com/mipt-masters/expense-analytics/internal/usecase/budget"
	"github.com/mipt-masters/expense-analytics/internal/usecase/csvio"
	reportuc "github.com/mipt-masters/expense-analytics/internal/usecase/report"
	txuc "github.com/mipt-masters/expense-analytics/internal/usecase/transaction"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
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

	db, err := postgres.Open(ctx, cfg.PostgresDSN)
	if err != nil {
		log.Error("postgres", "err", err)
		os.Exit(1)
	}
	defer db.Close()

	cache, err := rediscache.New(cfg.RedisAddr, cfg.RedisDB)
	if err != nil {
		log.Error("redis", "err", err)
		os.Exit(1)
	}
	defer cache.Close()

	txRepo := postgres.NewTransactionRepo(db)
	budgetRepo := postgres.NewBudgetRepo(db)
	txSvc := txuc.NewService(txRepo, budgetRepo, cache, log)
	budgetSvc := budgetuc.NewService(budgetRepo, cache)
	reportSvc := reportuc.NewService(txRepo, budgetRepo, cache, cfg.ReportCacheTTL, log)
	csvSvc := csvio.NewService(txSvc)

	lis, err := net.Listen("tcp", cfg.LedgerGRPCAddr)
	if err != nil {
		log.Error("listen", "err", err)
		os.Exit(1)
	}

	server := grpc.NewServer()
	ledgerv1.RegisterLedgerServiceServer(server, ledgergrpc.NewServer(txSvc, budgetSvc, reportSvc, csvSvc))
	reflection.Register(server)

	go func() {
		log.Info("ledger gRPC started", "addr", cfg.LedgerGRPCAddr)
		if err := server.Serve(lis); err != nil {
			log.Error("serve", "err", err)
			stop()
		}
	}()

	<-ctx.Done()
	log.Info("shutting down ledger")
	stopped := make(chan struct{})
	go func() {
		server.GracefulStop()
		close(stopped)
	}()
	select {
	case <-stopped:
	case <-time.After(5 * time.Second):
		server.Stop()
	}
}
