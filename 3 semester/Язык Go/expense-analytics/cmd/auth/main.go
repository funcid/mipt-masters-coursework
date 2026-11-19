package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	authv1 "github.com/mipt-masters/expense-analytics/api/gen/auth/v1"
	authgrpc "github.com/mipt-masters/expense-analytics/internal/adapter/grpc/auth"
	"github.com/mipt-masters/expense-analytics/internal/adapter/postgres"
	"github.com/mipt-masters/expense-analytics/internal/pkg/config"
	"github.com/mipt-masters/expense-analytics/internal/pkg/jwtutil"
	authuc "github.com/mipt-masters/expense-analytics/internal/usecase/auth"
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

	tokens := jwtutil.New(cfg.JWTSecret, cfg.JWTExpiresIn)
	hasher := jwtutil.NewBcryptHasher()
	users := postgres.NewUserRepo(db)
	svc := authuc.NewService(users, tokens, hasher)

	lis, err := net.Listen("tcp", cfg.AuthGRPCAddr)
	if err != nil {
		log.Error("listen", "err", err)
		os.Exit(1)
	}

	server := grpc.NewServer()
	authv1.RegisterAuthServiceServer(server, authgrpc.NewServer(svc))
	reflection.Register(server)

	go func() {
		log.Info("auth gRPC started", "addr", cfg.AuthGRPCAddr)
		if err := server.Serve(lis); err != nil {
			log.Error("serve", "err", err)
			stop()
		}
	}()

	<-ctx.Done()
	log.Info("shutting down auth")
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
