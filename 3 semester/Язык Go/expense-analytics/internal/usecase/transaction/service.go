package transaction

import (
	"context"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type Service struct {
	txs     domain.TransactionRepository
	budgets domain.BudgetRepository
	cache   domain.ReportCache
	log     *slog.Logger
}

func NewService(
	txs domain.TransactionRepository,
	budgets domain.BudgetRepository,
	cache domain.ReportCache,
	log *slog.Logger,
) *Service {
	if log == nil {
		log = slog.Default()
	}
	return &Service{txs: txs, budgets: budgets, cache: cache, log: log}
}

func (s *Service) Create(ctx context.Context, in domain.NewTransactionInput) (domain.Transaction, error) {
	if err := in.Validate(); err != nil {
		return domain.Transaction{}, err
	}

	budget, err := s.budgets.GetByCategory(ctx, in.UserID, in.Category)
	if err != nil {
		return domain.Transaction{}, err
	}
	if budget != nil {
		from, to := monthBounds(in.Date)
		spent, err := s.txs.SumByCategory(ctx, in.UserID, in.Category, from, to)
		if err != nil {
			return domain.Transaction{}, err
		}
		if err := domain.CheckBudgetExceeded(spent, in.Amount, budget.LimitAmount); err != nil {
			return domain.Transaction{}, fmt.Errorf(
				"%w: category=%s spent=%.2f + amount=%.2f > limit=%.2f",
				err, in.Category, spent, in.Amount, budget.LimitAmount,
			)
		}
	}

	now := time.Now().UTC()
	tx := domain.Transaction{
		ID:          uuid.NewString(),
		UserID:      in.UserID,
		Amount:      in.Amount,
		Category:    in.Category,
		Description: in.Description,
		Date:        in.Date.UTC().Truncate(24 * time.Hour),
		CreatedAt:   now,
	}
	if err := s.txs.Create(ctx, tx); err != nil {
		return domain.Transaction{}, err
	}
	if s.cache != nil {
		_ = s.cache.InvalidateUser(ctx, in.UserID)
	}
	return tx, nil
}

func (s *Service) List(ctx context.Context, userID string, from, to *time.Time) ([]domain.Transaction, error) {
	if userID == "" {
		return nil, fmt.Errorf("%w: user_id is required", domain.ErrValidation)
	}
	return s.txs.List(ctx, userID, from, to)
}

type BulkResult struct {
	Created int
	Failed  int
	Errors  []BulkError
}

type BulkError struct {
	Index   int
	Message string
}

// BulkCreate processes items concurrently with a worker pool. Safe under -race.
func (s *Service) BulkCreate(ctx context.Context, userID string, items []domain.NewTransactionInput, workers int) (BulkResult, error) {
	if userID == "" {
		return BulkResult{}, fmt.Errorf("%w: user_id is required", domain.ErrValidation)
	}
	if workers <= 0 {
		workers = 4
	}
	if workers > 32 {
		workers = 32
	}

	type job struct {
		idx int
		in  domain.NewTransactionInput
	}
	type outcome struct {
		idx int
		err error
	}

	jobs := make(chan job)
	outcomes := make(chan outcome, len(items))

	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				select {
				case <-ctx.Done():
					outcomes <- outcome{idx: j.idx, err: ctx.Err()}
					continue
				default:
				}
				j.in.UserID = userID
				_, err := s.Create(ctx, j.in)
				outcomes <- outcome{idx: j.idx, err: err}
			}
		}()
	}

	go func() {
		defer close(jobs)
		for i, item := range items {
			select {
			case <-ctx.Done():
				return
			case jobs <- job{idx: i, in: item}:
			}
		}
	}()

	go func() {
		wg.Wait()
		close(outcomes)
	}()

	result := BulkResult{}
	for out := range outcomes {
		if out.err != nil {
			result.Failed++
			result.Errors = append(result.Errors, BulkError{
				Index:   out.idx,
				Message: out.err.Error(),
			})
			continue
		}
		result.Created++
	}

	if ctx.Err() != nil && result.Created == 0 && result.Failed == 0 {
		return result, ctx.Err()
	}
	return result, nil
}

func monthBounds(d time.Time) (time.Time, time.Time) {
	d = d.UTC()
	from := time.Date(d.Year(), d.Month(), 1, 0, 0, 0, 0, time.UTC)
	to := from.AddDate(0, 1, 0).Add(-time.Nanosecond)
	return from, to
}
