package gateway_test

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	authv1 "github.com/mipt-masters/expense-analytics/api/gen/auth/v1"
	ledgerv1 "github.com/mipt-masters/expense-analytics/api/gen/ledger/v1"
	"github.com/mipt-masters/expense-analytics/internal/adapter/http/gateway"
	"github.com/mipt-masters/expense-analytics/internal/pkg/jwtutil"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type fakeAuth struct {
	authv1.AuthServiceClient
}

func (f *fakeAuth) Register(context.Context, *authv1.RegisterRequest, ...grpc.CallOption) (*authv1.AuthResponse, error) {
	return &authv1.AuthResponse{
		AccessToken: "tok", TokenType: "Bearer", ExpiresIn: 3600,
		User: &authv1.User{Id: "u1", Email: "a@b.c", Name: "A"},
	}, nil
}

func (f *fakeAuth) Login(context.Context, *authv1.LoginRequest, ...grpc.CallOption) (*authv1.AuthResponse, error) {
	return &authv1.AuthResponse{
		AccessToken: "tok", TokenType: "Bearer", ExpiresIn: 3600,
		User: &authv1.User{Id: "u1", Email: "a@b.c", Name: "A"},
	}, nil
}

type fakeLedger struct {
	ledgerv1.LedgerServiceClient
	createErr error
}

func (f *fakeLedger) CreateTransaction(_ context.Context, req *ledgerv1.CreateTransactionRequest, _ ...grpc.CallOption) (*ledgerv1.Transaction, error) {
	if f.createErr != nil {
		return nil, f.createErr
	}
	if req.GetAmount() <= 0 || req.GetCategory() == "" {
		return nil, status.Error(codes.InvalidArgument, "validation error")
	}
	return &ledgerv1.Transaction{
		Id: "t1", UserId: req.GetUserId(), Amount: req.GetAmount(),
		Category: req.GetCategory(), Description: req.GetDescription(),
		Date: req.GetDate(), CreatedAt: time.Now().UTC().Format(time.RFC3339),
	}, nil
}

func (f *fakeLedger) ListTransactions(context.Context, *ledgerv1.ListTransactionsRequest, ...grpc.CallOption) (*ledgerv1.ListTransactionsResponse, error) {
	return &ledgerv1.ListTransactionsResponse{Items: []*ledgerv1.Transaction{}}, nil
}

func (f *fakeLedger) UpsertBudget(_ context.Context, req *ledgerv1.UpsertBudgetRequest, _ ...grpc.CallOption) (*ledgerv1.Budget, error) {
	if req.GetLimitAmount() <= 0 {
		return nil, status.Error(codes.InvalidArgument, "validation error")
	}
	return &ledgerv1.Budget{
		Id: "b1", UserId: req.GetUserId(), Category: req.GetCategory(),
		LimitAmount: req.GetLimitAmount(), Period: "monthly",
		UpdatedAt: time.Now().UTC().Format(time.RFC3339),
	}, nil
}

func (f *fakeLedger) ListBudgets(context.Context, *ledgerv1.ListBudgetsRequest, ...grpc.CallOption) (*ledgerv1.ListBudgetsResponse, error) {
	return &ledgerv1.ListBudgetsResponse{Items: []*ledgerv1.Budget{}}, nil
}

func setupRouter(t *testing.T, ledger *fakeLedger) http.Handler {
	t.Helper()
	tokens := jwtutil.New("test-secret", time.Hour)
	h := gateway.NewHandler(ledger, &fakeAuth{})
	return gateway.NewRouter(h, tokens)
}

func authHeader(t *testing.T) string {
	t.Helper()
	tokens := jwtutil.New("test-secret", time.Hour)
	tok, _, err := tokens.Issue("u1", "a@b.c")
	if err != nil {
		t.Fatal(err)
	}
	return "Bearer " + tok
}

func TestPing(t *testing.T) {
	t.Parallel()
	r := setupRouter(t, &fakeLedger{})
	req := httptest.NewRequest(http.MethodGet, "/ping", nil)
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)
	if rec.Code != http.StatusOK {
		t.Fatalf("status=%d", rec.Code)
	}
}

func TestCreateTransaction_Created(t *testing.T) {
	t.Parallel()
	r := setupRouter(t, &fakeLedger{})
	body := `{"amount":12.5,"category":"food","description":"lunch","date":"2024-05-01"}`
	req := httptest.NewRequest(http.MethodPost, "/api/transactions", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader(t))
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)
	if rec.Code != http.StatusCreated {
		t.Fatalf("status=%d body=%s", rec.Code, rec.Body.String())
	}
}

func TestCreateTransaction_Validation(t *testing.T) {
	t.Parallel()
	r := setupRouter(t, &fakeLedger{})
	body := `{"amount":-1,"category":"food","date":"2024-05-01"}`
	req := httptest.NewRequest(http.MethodPost, "/api/transactions", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader(t))
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)
	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status=%d body=%s", rec.Code, rec.Body.String())
	}
	var payload map[string]any
	_ = json.Unmarshal(rec.Body.Bytes(), &payload)
	if payload["error"] != "validation_error" {
		t.Fatalf("unexpected payload: %v", payload)
	}
}

func TestCreateTransaction_BudgetExceeded(t *testing.T) {
	t.Parallel()
	r := setupRouter(t, &fakeLedger{createErr: status.Error(codes.FailedPrecondition, "budget limit exceeded")})
	body := `{"amount":999,"category":"food","date":"2024-05-01"}`
	req := httptest.NewRequest(http.MethodPost, "/api/transactions", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader(t))
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)
	if rec.Code != http.StatusConflict {
		t.Fatalf("status=%d body=%s", rec.Code, rec.Body.String())
	}
}

func TestProtectedWithoutToken(t *testing.T) {
	t.Parallel()
	r := setupRouter(t, &fakeLedger{})
	req := httptest.NewRequest(http.MethodGet, "/api/budgets", nil)
	rec := httptest.NewRecorder()
	r.ServeHTTP(rec, req)
	if rec.Code != http.StatusUnauthorized {
		t.Fatalf("status=%d", rec.Code)
	}
}
