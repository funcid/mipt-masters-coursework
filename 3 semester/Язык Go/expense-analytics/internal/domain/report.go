package domain

import "time"

type CategorySpend struct {
	Category           string
	Spent              float64
	BudgetLimit        float64
	BudgetUsagePercent float64
	OverBudget         bool
}

type SummaryReport struct {
	From       time.Time
	To         time.Time
	TotalSpent float64
	Categories []CategorySpend
	CacheHit   bool
}

// CheckBudgetExceeded returns ErrBudgetExceeded when adding amount would exceed limit.
func CheckBudgetExceeded(currentSpent, amount, limit float64) error {
	if limit <= 0 {
		return nil
	}
	if currentSpent+amount > limit {
		return ErrBudgetExceeded
	}
	return nil
}

func BuildCategorySpend(category string, spent, limit float64) CategorySpend {
	usage := 0.0
	if limit > 0 {
		usage = (spent / limit) * 100
	}
	return CategorySpend{
		Category:           category,
		Spent:              spent,
		BudgetLimit:        limit,
		BudgetUsagePercent: usage,
		OverBudget:         limit > 0 && spent > limit,
	}
}
