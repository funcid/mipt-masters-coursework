package authgrpc

import (
	"context"

	authv1 "github.com/mipt-masters/expense-analytics/api/gen/auth/v1"
	"github.com/mipt-masters/expense-analytics/internal/domain"
	"github.com/mipt-masters/expense-analytics/internal/pkg/apperr"
	authuc "github.com/mipt-masters/expense-analytics/internal/usecase/auth"
)

type Server struct {
	authv1.UnimplementedAuthServiceServer
	svc *authuc.Service
}

func NewServer(svc *authuc.Service) *Server {
	return &Server{svc: svc}
}

func (s *Server) Register(ctx context.Context, req *authv1.RegisterRequest) (*authv1.AuthResponse, error) {
	result, err := s.svc.Register(ctx, domain.RegisterInput{
		Email:    req.GetEmail(),
		Password: req.GetPassword(),
		Name:     req.GetName(),
	})
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return mapAuth(result), nil
}

func (s *Server) Login(ctx context.Context, req *authv1.LoginRequest) (*authv1.AuthResponse, error) {
	result, err := s.svc.Login(ctx, req.GetEmail(), req.GetPassword())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return mapAuth(result), nil
}

func (s *Server) ValidateToken(ctx context.Context, req *authv1.ValidateTokenRequest) (*authv1.ValidateTokenResponse, error) {
	userID, email, err := s.svc.Validate(ctx, req.GetAccessToken())
	if err != nil {
		return nil, apperr.ToGRPC(err)
	}
	return &authv1.ValidateTokenResponse{Valid: true, UserId: userID, Email: email}, nil
}

func mapAuth(result authuc.AuthResult) *authv1.AuthResponse {
	return &authv1.AuthResponse{
		AccessToken: result.AccessToken,
		TokenType:   result.TokenType,
		ExpiresIn:   result.ExpiresIn,
		User: &authv1.User{
			Id:    result.User.ID,
			Email: result.User.Email,
			Name:  result.User.Name,
		},
	}
}
