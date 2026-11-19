package csvio

import (
	"bytes"
	"context"
	"encoding/csv"
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
	txuc "github.com/mipt-masters/expense-analytics/internal/usecase/transaction"
)

type Service struct {
	txs *txuc.Service
}

func NewService(txs *txuc.Service) *Service {
	return &Service{txs: txs}
}

type ImportResult struct {
	Imported int
	Failed   int
	Errors   []ImportError
}

type ImportError struct {
	Row     int
	Message string
}

func (s *Service) Export(ctx context.Context, userID string, from, to *time.Time) (string, string, error) {
	items, err := s.txs.List(ctx, userID, from, to)
	if err != nil {
		return "", "", err
	}

	var buf bytes.Buffer
	w := csv.NewWriter(&buf)
	_ = w.Write([]string{"date", "amount", "category", "description"})
	for _, item := range items {
		_ = w.Write([]string{
			item.Date.Format("2006-01-02"),
			strconv.FormatFloat(item.Amount, 'f', 2, 64),
			item.Category,
			item.Description,
		})
	}
	w.Flush()
	if err := w.Error(); err != nil {
		return "", "", err
	}
	filename := fmt.Sprintf("transactions_%s.csv", time.Now().UTC().Format("20060102"))
	return buf.String(), filename, nil
}

func (s *Service) Import(ctx context.Context, userID, content string) (ImportResult, error) {
	r := csv.NewReader(strings.NewReader(content))
	r.TrimLeadingSpace = true
	r.FieldsPerRecord = -1

	result := ImportResult{}
	rowNum := 0
	headerSkipped := false

	for {
		record, err := r.Read()
		if err == io.EOF {
			break
		}
		rowNum++
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, ImportError{Row: rowNum, Message: err.Error()})
			continue
		}
		if len(record) == 0 {
			continue
		}
		if !headerSkipped && looksLikeHeader(record) {
			headerSkipped = true
			continue
		}
		if len(record) < 3 {
			result.Failed++
			result.Errors = append(result.Errors, ImportError{Row: rowNum, Message: "expected at least date,amount,category"})
			continue
		}

		date, err := time.Parse("2006-01-02", strings.TrimSpace(record[0]))
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, ImportError{Row: rowNum, Message: "invalid date, want YYYY-MM-DD"})
			continue
		}
		amount, err := strconv.ParseFloat(strings.TrimSpace(record[1]), 64)
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, ImportError{Row: rowNum, Message: "invalid amount"})
			continue
		}
		desc := ""
		if len(record) > 3 {
			desc = strings.TrimSpace(record[3])
		}
		_, err = s.txs.Create(ctx, domain.NewTransactionInput{
			UserID:      userID,
			Amount:      amount,
			Category:    strings.TrimSpace(record[2]),
			Description: desc,
			Date:        date,
		})
		if err != nil {
			result.Failed++
			result.Errors = append(result.Errors, ImportError{Row: rowNum, Message: err.Error()})
			continue
		}
		result.Imported++
	}
	return result, nil
}

func looksLikeHeader(record []string) bool {
	if len(record) == 0 {
		return false
	}
	first := strings.ToLower(strings.TrimSpace(record[0]))
	return first == "date" || first == "дата"
}
