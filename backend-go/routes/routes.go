package routes

import (
"incidentos/backend-go/internal/api"

"github.com/gin-gonic/gin"
)

func Register(r *gin.Engine) {
r.GET("/health", api.Health)
r.POST("/upload-repo", api.UploadRepo)
}
