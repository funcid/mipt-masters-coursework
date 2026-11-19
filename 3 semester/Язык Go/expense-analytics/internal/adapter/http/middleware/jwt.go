package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/mipt-masters/expense-analytics/internal/pkg/apperr"
	"github.com/mipt-masters/expense-analytics/internal/pkg/jwtutil"
)

type ctxKey string

const UserIDKey ctxKey = "userID"
const UserEmailKey ctxKey = "userEmail"

func JWT(tokens *jwtutil.Service) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			header := r.Header.Get("Authorization")
			if header == "" || !strings.HasPrefix(header, "Bearer ") {
				apperr.WriteJSON(w, http.StatusUnauthorized, apperr.ErrorBody{
					Error: "unauthorized", Message: "missing bearer token",
				})
				return
			}
			token := strings.TrimSpace(strings.TrimPrefix(header, "Bearer "))
			userID, email, err := tokens.Parse(token)
			if err != nil {
				apperr.WriteJSON(w, http.StatusUnauthorized, apperr.ErrorBody{
					Error: "unauthorized", Message: "invalid token",
				})
				return
			}
			ctx := context.WithValue(r.Context(), UserIDKey, userID)
			ctx = context.WithValue(ctx, UserEmailKey, email)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func UserIDFromContext(ctx context.Context) string {
	v, _ := ctx.Value(UserIDKey).(string)
	return v
}
