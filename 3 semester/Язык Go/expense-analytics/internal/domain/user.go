package domain

import (
	"fmt"
	"strings"
	"time"
)

type User struct {
	ID           string
	Email        string
	Name         string
	PasswordHash string
	CreatedAt    time.Time
}

type RegisterInput struct {
	Email    string
	Password string
	Name     string
}

func (in RegisterInput) Validate() error {
	email := strings.TrimSpace(strings.ToLower(in.Email))
	if email == "" || !strings.Contains(email, "@") {
		return fmt.Errorf("%w: invalid email", ErrValidation)
	}
	if len(in.Password) < 6 {
		return fmt.Errorf("%w: password must be at least 6 characters", ErrValidation)
	}
	if strings.TrimSpace(in.Name) == "" {
		return fmt.Errorf("%w: name is required", ErrValidation)
	}
	return nil
}

func (in RegisterInput) NormalizedEmail() string {
	return strings.TrimSpace(strings.ToLower(in.Email))
}
