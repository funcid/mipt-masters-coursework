package auth

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/mipt-masters/expense-analytics/internal/domain"
)

type Service struct {
	users  domain.UserRepository
	tokens domain.TokenService
	hasher domain.PasswordHasher
}

type AuthResult struct {
	AccessToken string
	TokenType   string
	ExpiresIn   int64
	User        domain.User
}

func NewService(users domain.UserRepository, tokens domain.TokenService, hasher domain.PasswordHasher) *Service {
	return &Service{users: users, tokens: tokens, hasher: hasher}
}

func (s *Service) Register(ctx context.Context, in domain.RegisterInput) (AuthResult, error) {
	if err := in.Validate(); err != nil {
		return AuthResult{}, err
	}
	email := in.NormalizedEmail()
	existing, err := s.users.GetByEmail(ctx, email)
	if err != nil {
		return AuthResult{}, err
	}
	if existing != nil {
		return AuthResult{}, domain.ErrAlreadyExists
	}
	hash, err := s.hasher.Hash(in.Password)
	if err != nil {
		return AuthResult{}, err
	}
	user := domain.User{
		ID:           uuid.NewString(),
		Email:        email,
		Name:         in.Name,
		PasswordHash: hash,
		CreatedAt:    time.Now().UTC(),
	}
	if err := s.users.Create(ctx, user); err != nil {
		return AuthResult{}, err
	}
	return s.issue(user)
}

func (s *Service) Login(ctx context.Context, email, password string) (AuthResult, error) {
	email = domain.RegisterInput{Email: email}.NormalizedEmail()
	user, err := s.users.GetByEmail(ctx, email)
	if err != nil {
		return AuthResult{}, err
	}
	if user == nil {
		return AuthResult{}, domain.ErrInvalidCredentials
	}
	if err := s.hasher.Compare(user.PasswordHash, password); err != nil {
		return AuthResult{}, domain.ErrInvalidCredentials
	}
	return s.issue(*user)
}

func (s *Service) Validate(ctx context.Context, token string) (userID, email string, err error) {
	_ = ctx
	if token == "" {
		return "", "", domain.ErrUnauthorized
	}
	userID, email, err = s.tokens.Parse(token)
	if err != nil {
		return "", "", fmt.Errorf("%w: %v", domain.ErrUnauthorized, err)
	}
	return userID, email, nil
}

func (s *Service) issue(user domain.User) (AuthResult, error) {
	token, expiresIn, err := s.tokens.Issue(user.ID, user.Email)
	if err != nil {
		return AuthResult{}, err
	}
	return AuthResult{
		AccessToken: token,
		TokenType:   "Bearer",
		ExpiresIn:   expiresIn,
		User:        user,
	}, nil
}
