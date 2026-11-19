package domain

import (
	"fmt"
	"strings"
	"time"
)

type Transaction struct {
	ID          string
	UserID      string
	Amount      float64
	Category    string
	Description string
	Date        time.Time
	CreatedAt   time.Time
}

type NewTransactionInput struct {
	UserID      string
	Amount      float64
	Category    string
	Description string
	Date        time.Time
}

func (in NewTransactionInput) Validate() error {
	if strings.TrimSpace(in.UserID) == "" {
		return fmt.Errorf("%w: user_id is required", ErrValidation)
	}
	if in.Amount <= 0 {
		return fmt.Errorf("%w: amount must be > 0", ErrValidation)
	}
	if strings.TrimSpace(in.Category) == "" {
		return fmt.Errorf("%w: category is required", ErrValidation)
	}
	if in.Date.IsZero() {
		return fmt.Errorf("%w: date is required", ErrValidation)
	}
	return nil
}
