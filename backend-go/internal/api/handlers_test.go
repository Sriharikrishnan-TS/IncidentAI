package api

import (
"encoding/json"
"net/http"
"net/http/httptest"
"testing"

"github.com/gin-gonic/gin"
)

func TestHealth(t *testing.T) {
gin.SetMode(gin.TestMode)
w := httptest.NewRecorder()
c, _ := gin.CreateTestContext(w)
c.Request = httptest.NewRequest(http.MethodGet, "/health", nil)

Health(c)

if w.Code != http.StatusOK {
t.Fatalf("expected status %d, got %d", http.StatusOK, w.Code)
}

var body map[string]string
if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
t.Fatalf("failed to parse response: %v", err)
}
if body["status"] != "ok" {
t.Fatalf("expected status ok, got %q", body["status"])
}
}

func TestUploadRepo(t *testing.T) {
gin.SetMode(gin.TestMode)
w := httptest.NewRecorder()
c, _ := gin.CreateTestContext(w)
c.Request = httptest.NewRequest(http.MethodPost, "/upload-repo", nil)

UploadRepo(c)

if w.Code != http.StatusAccepted {
t.Fatalf("expected status %d, got %d", http.StatusAccepted, w.Code)
}

var body map[string]string
if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
t.Fatalf("failed to parse response: %v", err)
}
if body["message"] == "" {
t.Fatal("expected non-empty message")
}
}
