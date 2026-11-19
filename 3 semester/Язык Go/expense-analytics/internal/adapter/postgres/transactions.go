package postgres

import (
	"context"
	"database/sql"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type TransactionRepo struct {
	db *sql.DB
}

func NewTransactionRepo(db *sql.DB) *TransactionRepo {
	return &TransactionRepo{db: db}
}

func (r *TransactionRepo) Create(ctx context.Context, tx domain.Transaction) error {
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO transactions (id, user_id, amount, category, description, date, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`, tx.ID, tx.UserID, tx.Amount, tx.Category, tx.Description, tx.Date, tx.CreatedAt)
	return err
}

func (r *TransactionRepo) List(ctx context.Context, userID string, from, to *time.Time) ([]domain.Transaction, error) {
	query := `
		SELECT id, user_id, amount, category, description, date, created_at
		FROM transactions
		WHERE user_id = $1
	`
	args := []any{userID}
	argN := 2
	if from != nil {
		query += ` AND date >= $` + itoa(argN)
		args = append(args, *from)
		argN++
	}
	if to != nil {
		query += ` AND date <= $` + itoa(argN)
		args = append(args, *to)
	}
	query += ` ORDER BY date DESC, created_at DESC`

	rows, err := r.db.QueryContext(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]domain.Transaction, 0)
	for rows.Next() {
		var item domain.Transaction
		if err := rows.Scan(
			&item.ID, &item.UserID, &item.Amount, &item.Category,
			&item.Description, &item.Date, &item.CreatedAt,
		); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	return out, rows.Err()
}

func (r *TransactionRepo) SumByCategory(ctx context.Context, userID, category string, from, to time.Time) (float64, error) {
	var sum sql.NullFloat64
	err := r.db.QueryRowContext(ctx, `
		SELECT COALESCE(SUM(amount), 0)
		FROM transactions
		WHERE user_id = $1 AND category = $2 AND date >= $3 AND date <= $4
	`, userID, category, from, to).Scan(&sum)
	if err != nil {
		return 0, err
	}
	return sum.Float64, nil
}

func (r *TransactionRepo) SumAllByCategory(ctx context.Context, userID string, from, to time.Time) (map[string]float64, error) {
	rows, err := r.db.QueryContext(ctx, `
		SELECT category, COALESCE(SUM(amount), 0)
		FROM transactions
		WHERE user_id = $1 AND date >= $2 AND date <= $3
		GROUP BY category
	`, userID, from, to)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make(map[string]float64)
	for rows.Next() {
		var cat string
		var sum float64
		if err := rows.Scan(&cat, &sum); err != nil {
			return nil, err
		}
		out[cat] = sum
	}
	return out, rows.Err()
}

func itoa(n int) string {
	if n < 10 {
		return string(rune('0' + n))
	}
	return fmtInt(n)
}

func fmtInt(n int) string {
	if n == 0 {
		return "0"
	}
	var b [12]byte
	i := len(b)
	for n > 0 {
		i--
		b[i] = byte('0' + n%10)
		n /= 10
	}
	return string(b[i:])
}
