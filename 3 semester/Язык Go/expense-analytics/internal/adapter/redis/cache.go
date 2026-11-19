package rediscache

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/mipt-masters/expense-analytics/internal/domain"
	"github.com/redis/go-redis/v9"
)

type ReportCache struct {
	client *redis.Client
}

func New(addr string, db int) (*ReportCache, error) {
	client := redis.NewClient(&redis.Options{Addr: addr, DB: db})
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("ping redis: %w", err)
	}
	return &ReportCache{client: client}, nil
}

func (c *ReportCache) Get(ctx context.Context, key string) (*domain.SummaryReport, bool, error) {
	raw, err := c.client.Get(ctx, key).Bytes()
	if err == redis.Nil {
		return nil, false, nil
	}
	if err != nil {
		return nil, false, err
	}
	var report domain.SummaryReport
	if err := json.Unmarshal(raw, &report); err != nil {
		return nil, false, err
	}
	return &report, true, nil
}

func (c *ReportCache) Set(ctx context.Context, key string, report domain.SummaryReport, ttl time.Duration) error {
	raw, err := json.Marshal(report)
	if err != nil {
		return err
	}
	return c.client.Set(ctx, key, raw, ttl).Err()
}

func (c *ReportCache) InvalidateUser(ctx context.Context, userID string) error {
	pattern := fmt.Sprintf("report:%s:*", userID)
	iter := c.client.Scan(ctx, 0, pattern, 100).Iterator()
	var keys []string
	for iter.Next(ctx) {
		keys = append(keys, iter.Val())
	}
	if err := iter.Err(); err != nil {
		return err
	}
	if len(keys) == 0 {
		return nil
	}
	return c.client.Del(ctx, keys...).Err()
}

func (c *ReportCache) Close() error {
	return c.client.Close()
}
