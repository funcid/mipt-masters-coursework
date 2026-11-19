package budget

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type Service struct {
	repo  domain.BudgetRepository
	cache domain.ReportCache
}

func NewService(repo domain.BudgetRepository, cache domain.ReportCache) *Service {
	return &Service{repo: repo, cache: cache}
}

func (s *Service) Upsert(ctx context.Context, in domain.UpsertBudgetInput) (domain.Budget, error) {
	if err := in.Validate(); err != nil {
		return domain.Budget{}, err
	}
	b := domain.Budget{
		ID:          uuid.NewString(),
		UserID:      in.UserID,
		Category:    in.Category,
		LimitAmount: in.LimitAmount,
		Period:      in.NormalizedPeriod(),
		UpdatedAt:   time.Now().UTC(),
	}
	saved, err := s.repo.Upsert(ctx, b)
	if err != nil {
		return domain.Budget{}, err
	}
	if s.cache != nil {
		_ = s.cache.InvalidateUser(ctx, in.UserID)
	}
	return saved, nil
}

func (s *Service) List(ctx context.Context, userID string) ([]domain.Budget, error) {
	if userID == "" {
		return nil, fmt.Errorf("%w: user_id is required", domain.ErrValidation)
	}
	return s.repo.List(ctx, userID)
}
