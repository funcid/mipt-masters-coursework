package ledgergrpc

import (
	"context"
	"fmt"
	"time"

	ledgerv1 "github.com/mipt-masters/expense-analytics/api/gen/ledger/v1"
	"github.com/mipt-masters/expense-analytics/internal/domain"
	"github.com/mipt-masters/expense-analytics/internal/pkg/apperr"
	budgetuc "github.com/mipt-masters/expense-analytics/internal/usecase/budget"
	"github.com/mipt-masters/expense-analytics/internal/usecase/csvio"
	reportuc "github.com/mipt-masters/expense-analytics/internal/usecase/report"
	txuc "github.com/mipt-masters/expense-analytics/internal/usecase/transaction"
)

type Server struct {
	ledgerv1.UnimplementedLedgerServiceServer
	txs     *txuc.Service
	budgets *budgetuc.Service
	reports *reportuc.Service
	csv     *csvio.Service
}

func NewServer(
	txs *txuc.Service,
	budgets *budgetuc.Service,
	reports *reportuc.Service,
	csv *csvio.Service,
) *Server {
	return &Server{txs: txs, budgets: budgets, reports: reports, csv: csv}
}

func (s *Server) CreateTransaction(ctx context.Context, req *ledgerv1.CreateTransactionRequest) (*ledgerv1.Transaction, error) {
	date, err := parseDate(req.GetDate())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	tx, err := s.txs.Create(ctx, domain.NewTransactionInput{
		UserID:      req.GetUserId(),
		Amount:      req.GetAmount(),
		Category:    req.GetCategory(),
		Description: req.GetDescription(),
		Date:        date,
	})
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return mapTx(tx), nil
}

func (s *Server) ListTransactions(ctx context.Context, req *ledgerv1.ListTransactionsRequest) (*ledgerv1.ListTransactionsResponse, error) {
	from, to, err := optionalRange(req.GetFrom(), req.GetTo())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	items, err := s.txs.List(ctx, req.GetUserId(), from, to)
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	out := &ledgerv1.ListTransactionsResponse{Items: make([]*ledgerv1.Transaction, 0, len(items))}
	for _, item := range items {
		out.Items = append(out.Items, mapTx(item))
	}
	return out, nil
}

func (s *Server) ExportTransactionsCSV(ctx context.Context, req *ledgerv1.ExportTransactionsRequest) (*ledgerv1.CSVPayload, error) {
	from, to, err := optionalRange(req.GetFrom(), req.GetTo())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	content, filename, err := s.csv.Export(ctx, req.GetUserId(), from, to)
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return &ledgerv1.CSVPayload{Content: content, Filename: filename}, nil
}

func (s *Server) ImportTransactionsCSV(ctx context.Context, req *ledgerv1.ImportTransactionsRequest) (*ledgerv1.ImportResult, error) {
	result, err := s.csv.Import(ctx, req.GetUserId(), req.GetCsvContent())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	out := &ledgerv1.ImportResult{
		Imported: int32(result.Imported),
		Failed:   int32(result.Failed),
	}
	for _, e := range result.Errors {
		out.Errors = append(out.Errors, &ledgerv1.ImportError{Row: int32(e.Row), Message: e.Message})
	}
	return out, nil
}

func (s *Server) BulkCreateTransactions(ctx context.Context, req *ledgerv1.BulkCreateTransactionsRequest) (*ledgerv1.BulkCreateResult, error) {
	items := make([]domain.NewTransactionInput, 0, len(req.GetItems()))
	for _, item := range req.GetItems() {
		date, err := parseDate(item.GetDate())
		if err != nil {
			return nil, apperr.ToGRPC(err)
		}
		items = append(items, domain.NewTransactionInput{
			UserID:      req.GetUserId(),
			Amount:      item.GetAmount(),
			Category:    item.GetCategory(),
			Description: item.GetDescription(),
			Date:        date,
		})
	}
	result, err := s.txs.BulkCreate(ctx, req.GetUserId(), items, int(req.GetWorkers()))
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	out := &ledgerv1.BulkCreateResult{
		Created: int32(result.Created),
		Failed:  int32(result.Failed),
	}
	for _, e := range result.Errors {
		out.Errors = append(out.Errors, &ledgerv1.ImportError{Row: int32(e.Index), Message: e.Message})
	}
	return out, nil
}

func (s *Server) UpsertBudget(ctx context.Context, req *ledgerv1.UpsertBudgetRequest) (*ledgerv1.Budget, error) {
	b, err := s.budgets.Upsert(ctx, domain.UpsertBudgetInput{
		UserID:      req.GetUserId(),
		Category:    req.GetCategory(),
		LimitAmount: req.GetLimitAmount(),
		Period:      req.GetPeriod(),
	})
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return mapBudget(b), nil
}

func (s *Server) ListBudgets(ctx context.Context, req *ledgerv1.ListBudgetsRequest) (*ledgerv1.ListBudgetsResponse, error) {
	items, err := s.budgets.List(ctx, req.GetUserId())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	out := &ledgerv1.ListBudgetsResponse{Items: make([]*ledgerv1.Budget, 0, len(items))}
	for _, item := range items {
		out.Items = append(out.Items, mapBudget(item))
	}
	return out, nil
}

func (s *Server) GetSummaryReport(ctx context.Context, req *ledgerv1.GetSummaryReportRequest) (*ledgerv1.SummaryReport, error) {
	from, err := parseDate(req.GetFrom())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	to, err := parseDate(req.GetTo())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	report, err := s.reports.Summary(ctx, req.GetUserId(), from, to)
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	out := &ledgerv1.SummaryReport{
		From:       report.From.Format("2006-01-02"),
		To:         report.To.Format("2006-01-02"),
		TotalSpent: report.TotalSpent,
		CacheHit:   report.CacheHit,
	}
	for _, c := range report.Categories {
		out.Categories = append(out.Categories, &ledgerv1.CategorySpend{
			Category:           c.Category,
			Spent:              c.Spent,
			BudgetLimit:        c.BudgetLimit,
			BudgetUsagePercent: c.BudgetUsagePercent,
			OverBudget:         c.OverBudget,
		})
	}
	return out, nil
}

func mapTx(tx domain.Transaction) *ledgerv1.Transaction {
	return &ledgerv1.Transaction{
		Id:          tx.ID,
		UserId:      tx.UserID,
		Amount:      tx.Amount,
		Category:    tx.Category,
		Description: tx.Description,
		Date:        tx.Date.Format("2006-01-02"),
		CreatedAt:   tx.CreatedAt.Format(time.RFC3339),
	}
}

func mapBudget(b domain.Budget) *ledgerv1.Budget {
	return &ledgerv1.Budget{
		Id:          b.ID,
		UserId:      b.UserID,
		Category:    b.Category,
		LimitAmount: b.LimitAmount,
		Period:      b.Period,
		UpdatedAt:   b.UpdatedAt.Format(time.RFC3339),
	}
}

func parseDate(value string) (time.Time, error) {
	if value == "" {
		return time.Time{}, fmt.Errorf("%w: date is required (YYYY-MM-DD)", domain.ErrValidation)
	}
	t, err := time.Parse("2006-01-02", value)
	if err != nil {
		return time.Time{}, fmt.Errorf("%w: invalid date %q", domain.ErrValidation, value)
	}
	return t, nil
}

func optionalRange(fromStr, toStr string) (*time.Time, *time.Time, error) {
	var from, to *time.Time
	if fromStr != "" {
		t, err := parseDate(fromStr)
		if err != nil {
			return nil, nil, err
		}
		from = &t
	}
	if toStr != "" {
		t, err := parseDate(toStr)
		if err != nil {
			return nil, nil, err
		}
		to = &t
	}
	return from, to, nil
}
