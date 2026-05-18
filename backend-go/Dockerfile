FROM golang:1.22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git ca-certificates

COPY go.mod go.sum* ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /incidentos-backend .

FROM alpine:3.20

WORKDIR /app

RUN apk add --no-cache ca-certificates git wget

COPY --from=builder /incidentos-backend ./incidentos-backend

RUN mkdir -p /app/repos

EXPOSE 8080

CMD ["./incidentos-backend"]