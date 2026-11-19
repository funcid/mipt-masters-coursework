package apperr

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/mipt-masters/expense-analytics/internal/domain"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
)

type ErrorBody struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

func WriteJSON(w http.ResponseWriter, statusCode int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	_ = json.NewEncoder(w).Encode(payload)
}

func WriteError(w http.ResponseWriter, err error) {
	code, body := MapError(err)
	WriteJSON(w, code, body)
}

func MapError(err error) (int, ErrorBody) {
	if err == nil {
		return http.StatusInternalServerError, ErrorBody{Error: "internal", Message: "unknown error"}
	}

	if st, ok := status.FromError(err); ok {
		return mapGRPC(st.Code(), st.Message())
	}

	switch {
	case errors.Is(err, domain.ErrValidation):
		return http.StatusBadRequest, ErrorBody{Error: "validation_error", Message: err.Error()}
	case errors.Is(err, domain.ErrBudgetExceeded):
		return http.StatusConflict, ErrorBody{Error: "budget_exceeded", Message: err.Error()}
	case errors.Is(err, domain.ErrConflict), errors.Is(err, domain.ErrAlreadyExists):
		return http.StatusConflict, ErrorBody{Error: "conflict", Message: err.Error()}
	case errors.Is(err, domain.ErrNotFound):
		return http.StatusNotFound, ErrorBody{Error: "not_found", Message: err.Error()}
	case errors.Is(err, domain.ErrUnauthorized), errors.Is(err, domain.ErrInvalidCredentials):
		return http.StatusUnauthorized, ErrorBody{Error: "unauthorized", Message: err.Error()}
	default:
		return http.StatusInternalServerError, ErrorBody{Error: "internal", Message: err.Error()}
	}
}

func mapGRPC(code codes.Code, message string) (int, ErrorBody) {
	switch code {
	case codes.InvalidArgument:
		return http.StatusBadRequest, ErrorBody{Error: "validation_error", Message: message}
	case codes.AlreadyExists, codes.Aborted:
		return http.StatusConflict, ErrorBody{Error: "conflict", Message: message}
	case codes.FailedPrecondition:
		return http.StatusConflict, ErrorBody{Error: "budget_exceeded", Message: message}
	case codes.NotFound:
		return http.StatusNotFound, ErrorBody{Error: "not_found", Message: message}
	case codes.Unauthenticated:
		return http.StatusUnauthorized, ErrorBody{Error: "unauthorized", Message: message}
	case codes.PermissionDenied:
		return http.StatusForbidden, ErrorBody{Error: "forbidden", Message: message}
	default:
		return http.StatusInternalServerError, ErrorBody{Error: "internal", Message: message}
	}
}

func ToGRPC(err error) error {
	if err == nil {
		return nil
	}
	switch {
	case errors.Is(err, domain.ErrValidation):
		return status.Error(codes.InvalidArgument, err.Error())
	case errors.Is(err, domain.ErrBudgetExceeded):
		return status.Error(codes.FailedPrecondition, err.Error())
	case errors.Is(err, domain.ErrAlreadyExists), errors.Is(err, domain.ErrConflict):
		return status.Error(codes.AlreadyExists, err.Error())
	case errors.Is(err, domain.ErrNotFound):
		return status.Error(codes.NotFound, err.Error())
	case errors.Is(err, domain.ErrUnauthorized), errors.Is(err, domain.ErrInvalidCredentials):
		return status.Error(codes.Unauthenticated, err.Error())
	default:
		return status.Error(codes.Internal, err.Error())
	}
}
