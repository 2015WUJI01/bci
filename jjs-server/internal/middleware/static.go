package middleware

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"jjs-server/internal/config"
)

var mimeTypes = map[string]string{
	".html": "text/html; charset=utf-8",
	".css":  "text/css; charset=utf-8",
	".js":   "application/javascript; charset=utf-8",
	".svg":  "image/svg+xml",
	".png":  "image/png",
	".ico":  "image/x-icon",
}

func StaticFileServer(next http.Handler) http.Handler {
	frontendDir := config.AppConfig.FrontendDir
	absDir, err := filepath.Abs(frontendDir)
	if err != nil {
		return next
	}

	fs := http.FileServer(http.Dir(absDir))

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path
		cleanPath := filepath.Clean(path)

		if strings.HasPrefix(cleanPath, "/api/") {
			next.ServeHTTP(w, r)
			return
		}

		fullPath := filepath.Join(absDir, cleanPath)
		info, err := os.Stat(fullPath)
		if err == nil && !info.IsDir() {
			ext := filepath.Ext(cleanPath)
			if contentType, ok := mimeTypes[ext]; ok {
				w.Header().Set("Content-Type", contentType)
			}
			fs.ServeHTTP(w, r)
			return
		}

		indexPath := filepath.Join(absDir, "index.html")
		if _, err := os.Stat(indexPath); err == nil {
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			http.ServeFile(w, r, indexPath)
			return
		}

		next.ServeHTTP(w, r)
	})
}
