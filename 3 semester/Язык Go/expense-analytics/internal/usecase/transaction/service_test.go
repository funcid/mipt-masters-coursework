package transaction_test

import (
	"context"
	"errors"
	"sync"
	"testing"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
	"github.com/mipt-masters/expense-analytics/internal/usecase/transaction"
)

type memTxRepo struct {
	mu   sync.Mutex
	items []domain.Transaction
}

func (m *memTxRepo) Create(_ context.Context, tx domain.Transaction) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.items = append(m.items, tx)
	return nil
}

func (m *memTxRepo) List(_ context.Context, userID string, from, to *time.Time) ([]domain.Transaction, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := make([]domain.Transaction, 0)
	for _, item := range m.items {
		if item.UserID != userID {
			continue
		}
		if from != nil && item.Date.Before(*from) {
			continue
		}
		if to != nil && item.Date.After(*to) {
			continue
		}
		out = append(out, item)
	}
	return out, nil
}

func (m *memTxRepo) SumByCategory(_ context.Context, userID, category string, from, to time.Time) (float64, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	var sum float64
	for _, item := range m.items {
		if item.UserID == userID && item.Category == category && !item.Date.Before(from) && !item.Date.After(to) {
			sum += item.Amount
		}
	}
	return sum, nil
}

func (m *memTxRepo) SumAllByCategory(_ context.Context, userID string, from, to time.Time) (map[string]float64, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	out := map[string]float64{}
	for _, item := range m.items {
		if item.UserID == userID && !item.Date.Before(from) && !item.Date.After(to) {
			out[item.Category] += item.Amount
		}
	}
	return out, nil
}

type memBudgetRepo struct {
	items map[string]domain.Budget
}

func (m *memBudgetRepo) Upsert(_ context.Context, budget domain.Budget) (domain.Budget, error) {
	key := budget.UserID + ":" + budget.Category
	m.items[key] = budget
	return budget, nil
}

func (m *memBudgetRepo) List(_ context.Context, userID string) ([]domain.Budget, error) {
	out := make([]domain.Budget, 0)
	for _, b := range m.items {
		if b.UserID == userID {
			out = append(out, b)
		}
	}
	return out, nil
}

func (m *memBudgetRepo) GetByCategory(_ context.Context, userID, category string) (*domain.Budget, error) {
	b, ok := m.items[userID+":"+category]
	if !ok {
		return nil, nil
	}
	cp := b
	return &cp, nil
}

type noopCache struct{}

func (noopCache) Get(context.Context, string) (*domain.SummaryReport, bool, error) {
	return nil, false, nil
}
func (noopCache) Set(context.Context, string, domain.SummaryReport, time.Duration) error { return nil }
func (noopCache) InvalidateUser(context.Context, string) error                           { return nil }

func TestCreate_RejectsWhenBudgetExceeded(t *testing.T) {
	t.Parallel()

	txs := &memTxRepo{}
	budgets := &memBudgetRepo{items: map[string]domain.Budget{
		"u1:food": {UserID: "u1", Category: "food", LimitAmount: 100},
	}}
	svc := transaction.NewService(txs, budgets, noopCache{}, nil)

	date := time.Date(2024, 3, 10, 0, 0, 0, 0, time.UTC)
	_, err := svc.Create(context.Background(), domain.NewTransactionInput{
		UserID: "u1", Amount: 60, Category: "food", Date: date,
	})
	if err != nil {
		t.Fatalf("first create: %v", err)
	}

	_, err = svc.Create(context.Background(), domain.NewTransactionInput{
		UserID: "u1", Amount: 50, Category: "food", Date: date,
	})
	if !errors.Is(err, domain.ErrBudgetExceeded) {
		t.Fatalf("got %v, want budget exceeded", err)
	}
	if len(txs.items) != 1 {
		t.Fatalf("expected 1 stored transaction, got %d", len(txs.items))
	}
}

func TestBulkCreate_RaceSafe(t *testing.T) {
	t.Parallel()

	txs := &memTxRepo{}
	budgets := &memBudgetRepo{items: map[string]domain.Budget{}}
	svc := transaction.NewService(txs, budgets, noopCache{}, nil)

	date := time.Date(2024, 4, 1, 0, 0, 0, 0, time.UTC)
	items := make([]domain.NewTransactionInput, 50)
	for i := range items {
		items[i] = domain.NewTransactionInput{
			Amount: float64(i + 1), Category: "misc", Date: date,
		}
	}

	result, err := svc.BulkCreate(context.Background(), "u1", items, 8)
	if err != nil {
		t.Fatal(err)
	}
	if result.Created != 50 || result.Failed != 0 {
		t.Fatalf("created=%d failed=%d", result.Created, result.Failed)
	}
}
