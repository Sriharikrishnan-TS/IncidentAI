package main

import (
"incidentos/backend-go/routes"

"github.com/gin-gonic/gin"
)

func main() {
r := gin.Default()
routes.Register(r)
_ = r.Run(":8080")
}
