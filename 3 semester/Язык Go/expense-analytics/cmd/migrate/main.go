package main

import (
	"context"
	"log/slog"
	"os"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/adapter/postgres"
	"github.com/mipt-masters/expense-analytics/internal/pkg/config"
)

func main() {
	log := slog.New(slog.NewJSONHandler(os.Stdout, nil))
	cfg, err := config.Load(".env")
	if err != nil {
		log.Error("config", "err", err)
		os.Exit(1)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	var last error
	for attempt := 1; attempt <= 20; attempt++ {
		db, err := postgres.Open(ctx, cfg.PostgresDSN)
		if err != nil {
			last = err
			log.Warn("postgres not ready", "attempt", attempt, "err", err)
			time.Sleep(time.Second)
			continue
		}
		if err := postgres.Migrate(db); err != nil {
			_ = db.Close()
			last = err
			log.Warn("migrate retry", "attempt", attempt, "err", err)
			time.Sleep(time.Second)
			continue
		}
		_ = db.Close()
		log.Info("migrations applied")
		return
	}
	log.Error("migrate failed", "err", last)
	os.Exit(1)
}
