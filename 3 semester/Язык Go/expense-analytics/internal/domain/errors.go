package domain

import "errors"

var (
	ErrNotFound            = errors.New("not found")
	ErrValidation          = errors.New("validation error")
	ErrConflict            = errors.New("conflict")
	ErrBudgetExceeded      = errors.New("budget limit exceeded")
	ErrUnauthorized        = errors.New("unauthorized")
	ErrAlreadyExists       = errors.New("already exists")
	ErrInvalidCredentials  = errors.New("invalid credentials")
)
