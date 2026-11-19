package gateway

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	chimw "github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/mipt-masters/expense-analytics/internal/adapter/http/middleware"
	"github.com/mipt-masters/expense-analytics/internal/pkg/jwtutil"
)

func NewRouter(h *Handler, tokens *jwtutil.Service) http.Handler {
	r := chi.NewRouter()
	r.Use(chimw.RequestID)
	r.Use(chimw.RealIP)
	r.Use(chimw.Logger)
	r.Use(chimw.Recoverer)
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: false,
		MaxAge:           300,
	}))

	r.Get("/ping", h.Ping)
	r.Get("/healthz", h.Ping)

	r.Post("/api/auth/register", h.Register)
	r.Post("/api/auth/login", h.Login)

	r.Group(func(r chi.Router) {
		r.Use(middleware.JWT(tokens))

		r.Get("/api/transactions", h.ListTransactions)
		r.Post("/api/transactions", h.CreateTransaction)
		r.Post("/api/transactions/bulk", h.BulkTransactions)
		r.Post("/api/transactions/import", h.ImportCSV)
		r.Get("/api/transactions/export.csv", h.ExportCSV)

		r.Get("/api/budgets", h.ListBudgets)
		r.Post("/api/budgets", h.UpsertBudget)

		r.Get("/api/reports/summary", h.SummaryReport)
	})

	return r
}
