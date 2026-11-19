.PHONY: tidy test cover race proto up down logs

tidy:
	go mod tidy

test:
	go test ./...

cover:
	go test ./internal/domain ./internal/usecase/transaction ./internal/adapter/http/gateway -coverprofile=cover.out -count=1
	go tool cover -func=cover.out

race:
	go test ./internal/usecase/transaction -race -count=1

proto:
	protoc -I api/proto \
		--go_out=api/gen --go_opt=paths=source_relative \
		--go-grpc_out=api/gen --go-grpc_opt=paths=source_relative \
		api/proto/ledger/v1/ledger.proto \
		api/proto/auth/v1/auth.proto

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f gateway ledger auth
