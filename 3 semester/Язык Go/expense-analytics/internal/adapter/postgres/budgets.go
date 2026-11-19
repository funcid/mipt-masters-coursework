package postgres

import (
	"context"
	"database/sql"
	"errors"

	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type BudgetRepo struct {
	db *sql.DB
}

func NewBudgetRepo(db *sql.DB) *BudgetRepo {
	return &BudgetRepo{db: db}
}

func (r *BudgetRepo) Upsert(ctx context.Context, budget domain.Budget) (domain.Budget, error) {
	row := r.db.QueryRowContext(ctx, `
		INSERT INTO budgets (id, user_id, category, limit_amount, period, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (user_id, category) DO UPDATE
		SET limit_amount = EXCLUDED.limit_amount,
		    period = EXCLUDED.period,
		    updated_at = EXCLUDED.updated_at
		RETURNING id, user_id, category, limit_amount, period, updated_at
	`, budget.ID, budget.UserID, budget.Category, budget.LimitAmount, budget.Period, budget.UpdatedAt)

	var out domain.Budget
	if err := row.Scan(&out.ID, &out.UserID, &out.Category, &out.LimitAmount, &out.Period, &out.UpdatedAt); err != nil {
		return domain.Budget{}, err
	}
	return out, nil
}

func (r *BudgetRepo) List(ctx context.Context, userID string) ([]domain.Budget, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT id, user_id, category, limit_amount, period, updated_at
		FROM budgets
		WHERE user_id = $1
		ORDER BY category
	`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]domain.Budget, 0)
	for rows.Next() {
		var b domain.Budget
		if err := rows.Scan(&b.ID, &b.UserID, &b.Category, &b.LimitAmount, &b.Period, &b.UpdatedAt); err != nil {
			return nil, err
		}
		out = append(out, b)
	}
	return out, rows.Err()
}

func (r *BudgetRepo) GetByCategory(ctx context.Context, userID, category string) (*domain.Budget, error) {
	row := r.db.QueryRowContext(ctx, `
		SELECT id, user_id, category, limit_amount, period, updated_at
		FROM budgets
		WHERE user_id = $1 AND category = $2
	`, userID, category)

	var b domain.Budget
	err := row.Scan(&b.ID, &b.UserID, &b.Category, &b.LimitAmount, &b.Period, &b.UpdatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &b, nil
}
