package domain

import (
	"context"
	"time"
)

type TransactionRepository interface {
	Create(ctx context.Context, tx Transaction) error
	List(ctx context.Context, userID string, from, to *time.Time) ([]Transaction, error)
	SumByCategory(ctx context.Context, userID, category string, from, to time.Time) (float64, error)
	SumAllByCategory(ctx context.Context, userID string, from, to time.Time) (map[string]float64, error)
}

type BudgetRepository interface {
	Upsert(ctx context.Context, budget Budget) (Budget, error)
	List(ctx context.Context, userID string) ([]Budget, error)
	GetByCategory(ctx context.Context, userID, category string) (*Budget, error)
}

type UserRepository interface {
	Create(ctx context.Context, user User) error
	GetByEmail(ctx context.Context, email string) (*User, error)
	GetByID(ctx context.Context, id string) (*User, error)
}

type ReportCache interface {
	Get(ctx context.Context, key string) (*SummaryReport, bool, error)
	Set(ctx context.Context, key string, report SummaryReport, ttl time.Duration) error
	InvalidateUser(ctx context.Context, userID string) error
}

type TokenService interface {
	Issue(userID, email string) (token string, expiresIn int64, err error)
	Parse(token string) (userID, email string, err error)
}

type PasswordHasher interface {
	Hash(password string) (string, error)
	Compare(hash, password string) error
}
