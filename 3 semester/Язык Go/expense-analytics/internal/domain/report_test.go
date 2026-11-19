package domain_test

import (
	"errors"
	"testing"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
)

func TestCheckBudgetExceeded(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name         string
		currentSpent float64
		amount       float64
		limit        float64
		wantErr      error
	}{
		{name: "no budget limit", currentSpent: 100, amount: 50, limit: 0, wantErr: nil},
		{name: "within budget", currentSpent: 40, amount: 10, limit: 100, wantErr: nil},
		{name: "exact limit ok", currentSpent: 90, amount: 10, limit: 100, wantErr: nil},
		{name: "exceeds budget", currentSpent: 90, amount: 11, limit: 100, wantErr: domain.ErrBudgetExceeded},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			err := domain.CheckBudgetExceeded(tt.currentSpent, tt.amount, tt.limit)
			if !errors.Is(err, tt.wantErr) {
				t.Fatalf("got %v, want %v", err, tt.wantErr)
			}
		})
	}
}

func TestBuildCategorySpend(t *testing.T) {
	t.Parallel()

	tests := []struct {
		name       string
		spent      float64
		limit      float64
		wantUsage  float64
		overBudget bool
	}{
		{name: "no limit", spent: 50, limit: 0, wantUsage: 0, overBudget: false},
		{name: "half used", spent: 50, limit: 100, wantUsage: 50, overBudget: false},
		{name: "over", spent: 120, limit: 100, wantUsage: 120, overBudget: true},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			got := domain.BuildCategorySpend("food", tt.spent, tt.limit)
			if got.BudgetUsagePercent != tt.wantUsage {
				t.Fatalf("usage=%v want=%v", got.BudgetUsagePercent, tt.wantUsage)
			}
			if got.OverBudget != tt.overBudget {
				t.Fatalf("over=%v want=%v", got.OverBudget, tt.overBudget)
			}
		})
	}
}

func TestNewTransactionInput_Validate(t *testing.T) {
	t.Parallel()

	validDate := time.Date(2024, 1, 15, 0, 0, 0, 0, time.UTC)

	tests := []struct {
		name    string
		input   domain.NewTransactionInput
		wantErr bool
	}{
		{
			name: "valid",
			input: domain.NewTransactionInput{
				UserID: "u1", Amount: 10, Category: "food", Date: validDate,
			},
		},
		{
			name: "missing category",
			input: domain.NewTransactionInput{
				UserID: "u1", Amount: 10, Date: validDate,
			},
			wantErr: true,
		},
		{
			name: "non positive amount",
			input: domain.NewTransactionInput{
				UserID: "u1", Amount: 0, Category: "food", Date: validDate,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			err := tt.input.Validate()
			if tt.wantErr && err == nil {
				t.Fatal("expected error")
			}
			if !tt.wantErr && err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
		})
	}
}
