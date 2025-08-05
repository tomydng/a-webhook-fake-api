# Webhook API Service

FastAPI service để nhận và lưu trữ webhook requests vào MongoDB.

## Tính năng

- Nhận tất cả HTTP methods (GET, POST, PUT, DELETE, etc.)
- Lưu trữ headers, body, URL, method vào MongoDB
- Hỗ trợ JSON và text payloads
- Xử lý đặc biệt cho X-Signature và X-Timestamp headers
- API để xem logs và thống kê
- Health check endpoints

## Cài đặt và chạy

### Cách 1: Sử dụng Docker Compose (Khuyến nghị)

```bash
# Chạy cả API và MongoDB
docker-compose up -d

# Xem logs
docker-compose logs -f

# Dừng services
docker-compose down
```

### Cách 2: Chạy local

1. Cài đặt MongoDB locally hoặc sử dụng MongoDB Atlas
2. Cài đặt dependencies:

```bash
pip install -r requirements.txt
```

3. Cấu hình environment variables trong `.env`
4. Chạy API:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Webhook Endpoints
- `POST/GET/PUT/DELETE /{any_path}` - Nhận webhook requests
- Tất cả requests sẽ được lưu vào MongoDB

### Management Endpoints
- `GET /` - Health check
- `GET /health` - Detailed health check với database status
- `GET /logs?limit=10&skip=0` - Xem recent logs
- `GET /logs/count` - Đếm tổng số requests
- `DELETE /logs` - Xóa tất cả logs

## Ví dụ sử dụng

### Gửi webhook request:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=abcdef1234567890xxxxxxxxxxxxxxxx" \
  -H "X-Timestamp: 2025-07-11T14:33:05+09:00" \
  -d '{
    "start_timestamp": "2025-07-11T14:30:00+09:00",
    "end_timestamp": "2025-07-11T14:33:00+09:00",
    "version": 1,
    "lines": [
      {
        "line_id": 3,
        "line_name": "Main Entrance",
        "camera_id": 15,
        "camera_name": "1階中央入口",
        "in": 3642,
        "out": 3571,
        "in_cumulative": 23484,
        "out_cumulative": 22851
      }
    ]
  }'
```

### Xem logs:

```bash
curl http://localhost:8000/logs
```

## Cấu trúc dữ liệu lưu trong MongoDB

```json
{
  "_id": "ObjectId",
  "timestamp": "2025-08-05T10:30:00Z",
  "method": "POST",
  "url": "http://localhost:8000/webhook",
  "path": "/webhook",
  "headers": {
    "content-type": "application/json",
    "x-signature": "sha256=abcdef...",
    "x-timestamp": "2025-07-11T14:33:05+09:00"
  },
  "query_params": {},
  "body": { /* JSON payload */ },
  "client_host": "127.0.0.1",
  "user_agent": "curl/7.68.0",
  "content_type": "application/json",
  "content_length": "245",
  "x_signature": "sha256=abcdef...",
  "x_timestamp": "2025-07-11T14:33:05+09:00"
}
```

## Environment Variables

```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=webhook_db
COLLECTION_NAME=webhook_requests
HOST=0.0.0.0
PORT=8000
```

## Development

### Chạy tests (nếu có):
```bash
pytest
```

### Format code:
```bash
black main.py
isort main.py
```

## Monitoring

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Recent logs: http://localhost:8000/logs
