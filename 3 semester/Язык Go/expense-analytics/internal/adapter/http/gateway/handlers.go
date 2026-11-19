package gateway

import (
	"encoding/json"
	"io"
	"net/http"

	authv1 "github.com/mipt-masters/expense-analytics/api/gen/auth/v1"
	ledgerv1 "github.com/mipt-masters/expense-analytics/api/gen/ledger/v1"
	"github.com/mipt-masters/expense-analytics/internal/adapter/http/middleware"
	"github.com/mipt-masters/expense-analytics/internal/pkg/apperr"
)

type Handler struct {
	ledger ledgerv1.LedgerServiceClient
	auth   authv1.AuthServiceClient
}

func NewHandler(ledger ledgerv1.LedgerServiceClient, auth authv1.AuthServiceClient) *Handler {
	return &Handler{ledger: ledger, auth: auth}
}

func (h *Handler) Ping(w http.ResponseWriter, _ *http.Request) {
	apperr.WriteJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

func (h *Handler) Register(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Email    string `json:"email"`
		Password string `json:"password"`
		Name     string `json:"name"`
	}
	if err := decodeJSON(r, &body); err != nil {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
		return
	}
	resp, err := h.auth.Register(r.Context(), &authv1.RegisterRequest{
		Email: body.Email, Password: body.Password, Name: body.Name,
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusCreated, mapAuth(resp))
}

func (h *Handler) Login(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Email    string `json:"email"`
		Password string `json:"password"`
	}
	if err := decodeJSON(r, &body); err != nil {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
		return
	}
	resp, err := h.auth.Login(r.Context(), &authv1.LoginRequest{Email: body.Email, Password: body.Password})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusOK, mapAuth(resp))
}

func (h *Handler) CreateTransaction(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Amount      float64 `json:"amount"`
		Category    string  `json:"category"`
		Description string  `json:"description"`
		Date        string  `json:"date"`
	}
	if err := decodeJSON(r, &body); err != nil {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
		return
	}
	resp, err := h.ledger.CreateTransaction(r.Context(), &ledgerv1.CreateTransactionRequest{
		UserId: middleware.UserIDFromContext(r.Context()),
		Amount: body.Amount, Category: body.Category,
		Description: body.Description, Date: body.Date,
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusCreated, mapTx(resp))
}

func (h *Handler) ListTransactions(w http.ResponseWriter, r *http.Request) {
	resp, err := h.ledger.ListTransactions(r.Context(), &ledgerv1.ListTransactionsRequest{
		UserId: middleware.UserIDFromContext(r.Context()),
		From:   r.URL.Query().Get("from"),
		To:     r.URL.Query().Get("to"),
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	items := make([]map[string]any, 0, len(resp.GetItems()))
	for _, item := range resp.GetItems() {
		items = append(items, mapTx(item))
	}
	apperr.WriteJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *Handler) UpsertBudget(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Category    string  `json:"category"`
		LimitAmount float64 `json:"limit_amount"`
		Period      string  `json:"period"`
	}
	if err := decodeJSON(r, &body); err != nil {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
		return
	}
	resp, err := h.ledger.UpsertBudget(r.Context(), &ledgerv1.UpsertBudgetRequest{
		UserId: middleware.UserIDFromContext(r.Context()),
		Category: body.Category, LimitAmount: body.LimitAmount, Period: body.Period,
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusCreated, mapBudget(resp))
}

func (h *Handler) ListBudgets(w http.ResponseWriter, r *http.Request) {
	resp, err := h.ledger.ListBudgets(r.Context(), &ledgerv1.ListBudgetsRequest{
		UserId: middleware.UserIDFromContext(r.Context()),
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	items := make([]map[string]any, 0, len(resp.GetItems()))
	for _, item := range resp.GetItems() {
		items = append(items, mapBudget(item))
	}
	apperr.WriteJSON(w, http.StatusOK, map[string]any{"items": items})
}

func (h *Handler) SummaryReport(w http.ResponseWriter, r *http.Request) {
	from := r.URL.Query().Get("from")
	to := r.URL.Query().Get("to")
	if from == "" || to == "" {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{
			Error: "validation_error", Message: "from and to query params are required (YYYY-MM-DD)",
		})
		return
	}
	resp, err := h.ledger.GetSummaryReport(r.Context(), &ledgerv1.GetSummaryReportRequest{
		UserId: middleware.UserIDFromContext(r.Context()), From: from, To: to,
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	cats := make([]map[string]any, 0, len(resp.GetCategories()))
	for _, c := range resp.GetCategories() {
		cats = append(cats, map[string]any{
			"category":             c.GetCategory(),
			"spent":                c.GetSpent(),
			"budget_limit":         c.GetBudgetLimit(),
			"budget_usage_percent": c.GetBudgetUsagePercent(),
			"over_budget":          c.GetOverBudget(),
		})
	}
	apperr.WriteJSON(w, http.StatusOK, map[string]any{
		"from":        resp.GetFrom(),
		"to":          resp.GetTo(),
		"total_spent": resp.GetTotalSpent(),
		"categories":  cats,
		"cache_hit":   resp.GetCacheHit(),
	})
}

func (h *Handler) ExportCSV(w http.ResponseWriter, r *http.Request) {
	resp, err := h.ledger.ExportTransactionsCSV(r.Context(), &ledgerv1.ExportTransactionsRequest{
		UserId: middleware.UserIDFromContext(r.Context()),
		From:   r.URL.Query().Get("from"),
		To:     r.URL.Query().Get("to"),
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	w.Header().Set("Content-Type", "text/csv; charset=utf-8")
	w.Header().Set("Content-Disposition", `attachment; filename="`+resp.GetFilename()+`"`)
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(resp.GetContent()))
}

func (h *Handler) ImportCSV(w http.ResponseWriter, r *http.Request) {
	contentType := r.Header.Get("Content-Type")
	var csvContent string
	if contentType == "text/csv" || contentType == "application/csv" {
		raw, err := io.ReadAll(io.LimitReader(r.Body, 2<<20))
		if err != nil {
			apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
			return
		}
		csvContent = string(raw)
	} else {
		var body struct {
			CSV string `json:"csv"`
		}
		if err := decodeJSON(r, &body); err != nil {
			apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
			return
		}
		csvContent = body.CSV
	}
	resp, err := h.ledger.ImportTransactionsCSV(r.Context(), &ledgerv1.ImportTransactionsRequest{
		UserId: middleware.UserIDFromContext(r.Context()), CsvContent: csvContent,
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusOK, map[string]any{
		"imported": resp.GetImported(),
		"failed":   resp.GetFailed(),
		"errors":   resp.GetErrors(),
	})
}

func (h *Handler) BulkTransactions(w http.ResponseWriter, r *http.Request) {
	var body struct {
		Workers int `json:"workers"`
		Items   []struct {
			Amount      float64 `json:"amount"`
			Category    string  `json:"category"`
			Description string  `json:"description"`
			Date        string  `json:"date"`
		} `json:"items"`
	}
	if err := decodeJSON(r, &body); err != nil {
		apperr.WriteJSON(w, http.StatusBadRequest, apperr.ErrorBody{Error: "validation_error", Message: err.Error()})
		return
	}
	items := make([]*ledgerv1.CreateTransactionRequest, 0, len(body.Items))
	for _, item := range body.Items {
		items = append(items, &ledgerv1.CreateTransactionRequest{
			Amount: item.Amount, Category: item.Category,
			Description: item.Description, Date: item.Date,
		})
	}
	resp, err := h.ledger.BulkCreateTransactions(r.Context(), &ledgerv1.BulkCreateTransactionsRequest{
		UserId: middleware.UserIDFromContext(r.Context()), Items: items, Workers: int32(body.Workers),
	})
	if err != nil {
		apperr.WriteError(w, err)
		return
	}
	apperr.WriteJSON(w, http.StatusOK, map[string]any{
		"created": resp.GetCreated(),
		"failed":  resp.GetFailed(),
		"errors":  resp.GetErrors(),
	})
}

func decodeJSON(r *http.Request, dst any) error {
	dec := json.NewDecoder(io.LimitReader(r.Body, 1<<20))
	dec.DisallowUnknownFields()
	return dec.Decode(dst)
}

func mapAuth(resp *authv1.AuthResponse) map[string]any {
	return map[string]any{
		"access_token": resp.GetAccessToken(),
		"token_type":   resp.GetTokenType(),
		"expires_in":   resp.GetExpiresIn(),
		"user": map[string]any{
			"id":    resp.GetUser().GetId(),
			"email": resp.GetUser().GetEmail(),
			"name":  resp.GetUser().GetName(),
		},
	}
}

func mapTx(tx *ledgerv1.Transaction) map[string]any {
	return map[string]any{
		"id": tx.GetId(), "user_id": tx.GetUserId(), "amount": tx.GetAmount(),
		"category": tx.GetCategory(), "description": tx.GetDescription(),
		"date": tx.GetDate(), "created_at": tx.GetCreatedAt(),
	}
}

func mapBudget(b *ledgerv1.Budget) map[string]any {
	return map[string]any{
		"id": b.GetId(), "user_id": b.GetUserId(), "category": b.GetCategory(),
		"limit_amount": b.GetLimitAmount(), "period": b.GetPeriod(), "updated_at": b.GetUpdatedAt(),
	}
}
