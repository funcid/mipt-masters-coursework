package report

import (
	"context"
	"fmt"
	"log/slog"
	"sort"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type Service struct {
	txs     domain.TransactionRepository
	budgets domain.BudgetRepository
	cache   domain.ReportCache
	ttl     time.Duration
	log     *slog.Logger
}

func NewService(
	txs domain.TransactionRepository,
	budgets domain.BudgetRepository,
	cache domain.ReportCache,
	ttl time.Duration,
	log *slog.Logger,
) *Service {
	if ttl <= 0 {
		ttl = 2 * time.Minute
	}
	if log == nil {
		log = slog.Default()
	}
	return &Service{txs: txs, budgets: budgets, cache: cache, ttl: ttl, log: log}
}

func (s *Service) Summary(ctx context.Context, userID string, from, to time.Time) (domain.SummaryReport, error) {
	if userID == "" {
		return domain.SummaryReport{}, fmt.Errorf("%w: user_id is required", domain.ErrValidation)
	}
	if from.IsZero() || to.IsZero() {
		return domain.SummaryReport{}, fmt.Errorf("%w: from and to are required", domain.ErrValidation)
	}
	if to.Before(from) {
		return domain.SummaryReport{}, fmt.Errorf("%w: to must be >= from", domain.ErrValidation)
	}

	from = from.UTC().Truncate(24 * time.Hour)
	to = to.UTC().Truncate(24 * time.Hour)
	cacheKey := fmt.Sprintf("report:%s:%s:%s", userID, from.Format("2006-01-02"), to.Format("2006-01-02"))

	if s.cache != nil {
		if cached, ok, err := s.cache.Get(ctx, cacheKey); err == nil && ok && cached != nil {
			s.log.Info("report cache hit", "key", cacheKey)
			cached.CacheHit = true
			return *cached, nil
		}
		s.log.Info("report cache miss", "key", cacheKey)
	}

	spentByCat, err := s.txs.SumAllByCategory(ctx, userID, from, to)
	if err != nil {
		return domain.SummaryReport{}, err
	}
	budgets, err := s.budgets.List(ctx, userID)
	if err != nil {
		return domain.SummaryReport{}, err
	}
	budgetMap := make(map[string]float64, len(budgets))
	for _, b := range budgets {
		budgetMap[b.Category] = b.LimitAmount
	}

	cats := make([]string, 0, len(spentByCat))
	for cat := range spentByCat {
		cats = append(cats, cat)
	}
	sort.Strings(cats)

	report := domain.SummaryReport{
		From:       from,
		To:         to,
		Categories: make([]domain.CategorySpend, 0, len(cats)),
		CacheHit:   false,
	}
	for _, cat := range cats {
		spent := spentByCat[cat]
		report.TotalSpent += spent
		report.Categories = append(report.Categories, domain.BuildCategorySpend(cat, spent, budgetMap[cat]))
	}

	if s.cache != nil {
		if err := s.cache.Set(ctx, cacheKey, report, s.ttl); err != nil {
			s.log.Warn("failed to cache report", "err", err)
		}
	}
	return report, nil
}
