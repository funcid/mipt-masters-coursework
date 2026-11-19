package domain

import (
	"fmt"
	"strings"
	"time"
)

const PeriodMonthly = "monthly"

type Budget struct {
	ID          string
	UserID      string
	Category    string
	LimitAmount float64
	Period      string
	UpdatedAt   time.Time
}

type UpsertBudgetInput struct {
	UserID      string
	Category    string
	LimitAmount float64
	Period      string
}

func (in UpsertBudgetInput) Validate() error {
	if strings.TrimSpace(in.UserID) == "" {
		return fmt.Errorf("%w: user_id is required", ErrValidation)
	}
	if strings.TrimSpace(in.Category) == "" {
		return fmt.Errorf("%w: category is required", ErrValidation)
	}
	if in.LimitAmount <= 0 {
		return fmt.Errorf("%w: limit_amount must be > 0", ErrValidation)
	}
	period := strings.ToLower(strings.TrimSpace(in.Period))
	if period == "" {
		period = PeriodMonthly
	}
	if period != PeriodMonthly {
		return fmt.Errorf("%w: unsupported period %q", ErrValidation, in.Period)
	}
	return nil
}

func (in UpsertBudgetInput) NormalizedPeriod() string {
	period := strings.ToLower(strings.TrimSpace(in.Period))
	if period == "" {
		return PeriodMonthly
	}
	return period
}
