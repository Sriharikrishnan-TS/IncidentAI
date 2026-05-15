package api

import "github.com/gin-gonic/gin"

func Health(c *gin.Context) {
c.JSON(200, gin.H{"status": "ok"})
}

func UploadRepo(c *gin.Context) {
// Skeleton endpoint for ingesting repository metadata for investigation pipelines.
c.JSON(202, gin.H{"message": "upload repository endpoint scaffold"})
}
