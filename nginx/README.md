# Nginx Reverse Proxy

Nginx serves as the central gateway for all services in the B2B Marketing Automation Platform.

## Service Routes

| Path | Service | Port | Purpose |
|------|---------|------|---------|
| `/dashboard` | Streamlit | 8501 | Main control panel |
| `/n8n/` | n8n | 5678 | Workflow orchestration |
| `/api/` | LangChain | 8001 | AI agents & APIs |
| `/analytics/` | Matomo | 80 | Web analytics |
| `/search/` | SearXNG | 8080 | Meta-search engine |
| `/ollama/` | Ollama | 11434 | LLM service |
| `/chroma/` | Chroma | 8000 | Vector database |
| `/adminer/` | Adminer | 8080 | Database management |

## Quick Start

### 1. Start Nginx

```bash
# Start all services
docker-compose up -d

# Check Nginx is running
docker-compose ps nginx
curl http://localhost/health
```

### 2. Access Services

- **Dashboard**: http://localhost/dashboard
- **n8n**: http://localhost/n8n
- **API Docs**: http://localhost/api/docs
- **Analytics**: http://localhost/analytics
- **Search**: http://localhost/search
- **Database**: http://localhost/adminer

## Configuration

### nginx.conf Structure

```nginx
http {
    # Upstream definitions
    upstream service_name {
        server container:port;
    }

    server {
        listen 80;

        # Service routing
        location /path/ {
            proxy_pass http://service_name/;
            # Proxy headers
            # Rate limiting
            # Timeouts
        }
    }
}
```

### Rate Limiting

Configured zones:
- **api_limit**: 10 requests/second (for APIs)
- **general_limit**: 30 requests/second (for web interfaces)

Adjust in nginx.conf:
```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
```

### Timeouts

Different services have different timeouts:

| Service | Timeout | Reason |
|---------|---------|--------|
| Ollama | 600s | LLM generation can be slow |
| LangChain API | 300s | Agent workflows take time |
| SearXNG | 60s | Search aggregation |
| Default | 60s | Standard web requests |

## SSL/HTTPS Setup

### For Production

1. Obtain SSL certificate (Let's Encrypt recommended):

```bash
# Using certbot
certbot certonly --standalone -d your-domain.com

# Or use existing certificates
cp /path/to/cert.pem nginx/ssl/
cp /path/to/key.pem nginx/ssl/
```

2. Uncomment HTTPS server block in nginx.conf

3. Restart Nginx:

```bash
docker-compose restart nginx
```

### Self-Signed Certificate (Development)

```bash
# Generate self-signed certificate
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/CN=localhost"
```

## Health Checks

### Main Health Check

```bash
curl http://localhost/health
# Output: healthy
```

### Service-Specific Health Checks

```bash
# n8n
curl http://localhost/health/n8n

# Chroma
curl http://localhost/health/chroma

# Ollama
curl http://localhost/health/ollama
```

### Monitoring Script

```bash
#!/bin/bash
# check-services.sh

services=("health" "health/n8n" "health/chroma" "health/ollama")

for service in "${services[@]}"; do
    status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/$service)
    if [ $status -eq 200 ]; then
        echo "✓ $service: OK"
    else
        echo "✗ $service: FAILED (Status: $status)"
    fi
done
```

## Logs

### View Logs

```bash
# Access logs
docker exec nginx tail -f /var/log/nginx/access.log

# Error logs
docker exec nginx tail -f /var/log/nginx/error.log

# Follow all logs
docker logs nginx -f
```

### Log Format

```
$remote_addr - $remote_user [$time_local] "$request"
$status $body_bytes_sent "$http_referer"
"$http_user_agent" "$http_x_forwarded_for"
```

Example:
```
172.18.0.1 - - [13/Jan/2026:10:30:45 +0000] "GET /dashboard HTTP/1.1"
200 1234 "-" "Mozilla/5.0" "-"
```

## Performance Tuning

### Worker Processes

```nginx
# Auto-detect CPU cores
worker_processes auto;

# Or set manually
worker_processes 4;
```

### Connections

```nginx
events {
    worker_connections 1024;  # Max connections per worker
    use epoll;                # Linux-specific optimization
    multi_accept on;          # Accept multiple connections at once
}
```

### Buffer Sizes

For large requests (file uploads):

```nginx
http {
    client_body_buffer_size 128k;
    client_max_body_size 100M;  # Max upload size
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;
}
```

### Caching

Static file caching is already configured:

```nginx
location /static/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    expires 7d;
    add_header Cache-Control "public";
}
```

## Security

### Headers

Security headers are configured by default:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
```

### Rate Limiting

Protects against abuse:

```nginx
limit_req zone=api_limit burst=10 nodelay;
```

### IP Blacklisting

Block specific IPs (add to nginx.conf):

```nginx
# Block specific IP
deny 192.168.1.100;

# Block IP range
deny 192.168.1.0/24;

# Allow all others
allow all;
```

### Basic Auth (Optional)

Protect sensitive endpoints:

```bash
# Install htpasswd
apt-get install apache2-utils

# Create password file
htpasswd -c nginx/.htpasswd admin

# Add to nginx.conf
location /adminer/ {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://adminer/;
}
```

## Troubleshooting

### 502 Bad Gateway

**Cause**: Upstream service not responding

**Solution**:
```bash
# Check upstream service is running
docker-compose ps

# Check logs
docker logs nginx
docker logs [upstream_service]

# Restart upstream service
docker-compose restart [service]
```

### 504 Gateway Timeout

**Cause**: Request took too long

**Solution**:
```nginx
# Increase timeout in nginx.conf
location /api/ {
    proxy_read_timeout 300;  # 5 minutes
    proxy_connect_timeout 300;
}
```

### Connection Refused

**Cause**: Service not accessible

**Solution**:
```bash
# Check network
docker exec nginx ping langchain_service

# Verify upstream configuration
docker exec nginx nginx -T | grep upstream

# Restart Nginx
docker-compose restart nginx
```

### Configuration Syntax Error

```bash
# Test configuration
docker exec nginx nginx -t

# If error, fix nginx.conf and reload
docker-compose restart nginx
```

## Custom Domains

### Local Development

Add to `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows):

```
127.0.0.1 marketing.local
127.0.0.1 dashboard.marketing.local
127.0.0.1 api.marketing.local
```

Update nginx.conf:

```nginx
server {
    listen 80;
    server_name marketing.local;
    # ...
}

server {
    listen 80;
    server_name dashboard.marketing.local;
    location / {
        proxy_pass http://streamlit;
    }
}

server {
    listen 80;
    server_name api.marketing.local;
    location / {
        proxy_pass http://langchain;
    }
}
```

### Production Deployment

1. Point DNS A records to server IP
2. Configure domain in nginx.conf
3. Set up SSL with Let's Encrypt
4. Enable HTTPS redirect

## WebSocket Support

WebSocket connections are configured for:
- **Streamlit**: Real-time dashboard updates
- **n8n**: Live workflow execution logs

Configuration:

```nginx
location /dashboard {
    proxy_pass http://streamlit;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;  # 24 hours
}
```

## Load Balancing (Future)

For scaling to multiple instances:

```nginx
upstream langchain {
    least_conn;  # Load balancing method
    server langchain_service_1:8001;
    server langchain_service_2:8001;
    server langchain_service_3:8001;
}
```

## Monitoring

### Nginx Status Module

Enable status module:

```nginx
location /nginx_status {
    stub_status on;
    access_log off;
    allow 127.0.0.1;
    deny all;
}
```

Access:
```bash
curl http://localhost/nginx_status
```

Output:
```
Active connections: 12
server accepts handled requests
 42 42 128
Reading: 0 Writing: 3 Waiting: 9
```

### Prometheus Metrics

For production monitoring, use nginx-prometheus-exporter:

```yaml
# docker-compose.yml
nginx_exporter:
  image: nginx/nginx-prometheus-exporter:latest
  command:
    - '-nginx.scrape-uri=http://nginx:80/nginx_status'
  ports:
    - "9113:9113"
```

## Best Practices

1. **Always test configuration** before reloading:
   ```bash
   docker exec nginx nginx -t
   ```

2. **Use rate limiting** on all public endpoints

3. **Enable gzip compression** for text content

4. **Set appropriate timeouts** based on service needs

5. **Monitor logs** for errors and suspicious activity

6. **Keep Nginx updated** to latest stable version

7. **Use HTTPS in production** (Let's Encrypt is free)

8. **Implement caching** for static assets

## Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Security Best Practices](https://www.nginx.com/blog/nginx-security-best-practices/)
- [Performance Tuning](https://www.nginx.com/blog/tuning-nginx/)
