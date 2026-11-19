package postgres

import (
	"context"
	"database/sql"
	"errors"

	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type UserRepo struct {
	db *sql.DB
}

func NewUserRepo(db *sql.DB) *UserRepo {
	return &UserRepo{db: db}
}

func (r *UserRepo) Create(ctx context.Context, user domain.User) error {
	_, err := r.db.ExecContext(ctx, `
		INSERT INTO users (id, email, name, password_hash, created_at)
		VALUES ($1, $2, $3, $4, $5)
	`, user.ID, user.Email, user.Name, user.PasswordHash, user.CreatedAt)
	return err
}

func (r *UserRepo) GetByEmail(ctx context.Context, email string) (*domain.User, error) {
	return r.scanOne(ctx, `
		SELECT id, email, name, password_hash, created_at
		FROM users WHERE email = $1
	`, email)
}

func (r *UserRepo) GetByID(ctx context.Context, id string) (*domain.User, error) {
	return r.scanOne(ctx, `
		SELECT id, email, name, password_hash, created_at
		FROM users WHERE id = $1
	`, id)
}

func (r *UserRepo) scanOne(ctx context.Context, query string, arg any) (*domain.User, error) {
	row := r.db.QueryRowContext(ctx, query, arg)
	var u domain.User
	err := row.Scan(&u.ID, &u.Email, &u.Name, &u.PasswordHash, &u.CreatedAt)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &u, nil
}
