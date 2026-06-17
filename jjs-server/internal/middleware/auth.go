package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/golang-jwt/jwt/v5"

	"jjs-server/internal/config"
)

type contextKey string

const userIDKey contextKey = "user_id"

func JWT(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			http.Error(w, `{"error":"未登录"}`, http.StatusUnauthorized)
			return
		}

		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			http.Error(w, `{"error":"invalid authorization header"}`, http.StatusUnauthorized)
			return
		}

		token, err := jwt.Parse(parts[1], func(t *jwt.Token) (interface{}, error) {
			return []byte(config.AppConfig.JWTSecret), nil
		})
		if err != nil || !token.Valid {
			http.Error(w, `{"error":"登录已过期"}`, http.StatusUnauthorized)
			return
		}

		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			http.Error(w, `{"error":"invalid token claims"}`, http.StatusUnauthorized)
			return
		}

		userID, ok := claims["sub"].(string)
		if !ok {
			http.Error(w, `{"error":"invalid token subject"}`, http.StatusUnauthorized)
			return
		}

		ctx := context.WithValue(r.Context(), userIDKey, userID)
		next.ServeHTTP(w, r.WithContext(ctx))
	})
}

func GetUserID(r *http.Request) (string, bool) {
	id, ok := r.Context().Value(userIDKey).(string)
	return id, ok
}

func OptionalJWT(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		authHeader := r.Header.Get("Authorization")
		if authHeader == "" {
			next.ServeHTTP(w, r)
			return
		}
		parts := strings.SplitN(authHeader, " ", 2)
		if len(parts) != 2 || parts[0] != "Bearer" {
			next.ServeHTTP(w, r)
			return
		}
		token, err := jwt.Parse(parts[1], func(t *jwt.Token) (interface{}, error) {
			return []byte(config.AppConfig.JWTSecret), nil
		})
		if err != nil || !token.Valid {
			next.ServeHTTP(w, r)
			return
		}
		claims, ok := token.Claims.(jwt.MapClaims)
		if !ok {
			next.ServeHTTP(w, r)
			return
		}
		if userID, ok := claims["sub"].(string); ok {
			ctx := context.WithValue(r.Context(), userIDKey, userID)
			r = r.WithContext(ctx)
		}
		next.ServeHTTP(w, r)
	})
}
