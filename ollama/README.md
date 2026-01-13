# Ollama LLM Service

Ollama provides self-hosted large language models for the B2B Marketing Automation Platform.

## Quick Start

### 1. Start Ollama

```bash
# Start all services
docker-compose up -d

# Check Ollama is running
docker-compose ps ollama
curl http://localhost:11434/api/tags
```

### 2. Pull Models

**Linux/Mac:**
```bash
chmod +x ollama/pull-models.sh
./ollama/pull-models.sh
```

**Windows:**
```powershell
.\ollama\pull-models.ps1
```

**Manual:**
```bash
# Pull Llama 3 8B (recommended)
docker exec ollama ollama pull llama3:8b

# Pull Mistral 7B (alternative)
docker exec ollama ollama pull mistral:7b

# List models
docker exec ollama ollama list
```

### 3. Test Models

```bash
# Test Llama 3
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Write a professional LinkedIn post about AI in marketing",
  "stream": false
}'

# Test Mistral
curl http://localhost:11434/api/generate -d '{
  "model": "mistral:7b",
  "prompt": "Create a blog post outline about B2B content marketing",
  "stream": false
}'
```

## Available Models

### Recommended Models

| Model | Size | RAM Required | Use Case |
|-------|------|--------------|----------|
| **llama3:8b** | 4.7GB | 16GB | Primary model for content generation |
| **mistral:7b** | 4.1GB | 12GB | Alternative for faster responses |
| **llama3:70b** | 40GB | 64GB+ | High-quality (requires GPU server) |

### Optional Models

| Model | Size | Use Case |
|-------|------|----------|
| **codellama:7b** | 3.8GB | Code generation (if needed) |
| **phi:2** | 1.7GB | Lightweight, fast responses |
| **mixtral:8x7b** | 26GB | High quality with MoE architecture |

## Model Selection Guide

### For Development (16GB RAM)
- Use: `llama3:8b`
- Settings: `num_ctx=4096`, `num_predict=1024`

### For Production (32GB+ RAM)
- Use: `llama3:8b` or `mistral:7b`
- Settings: `num_ctx=8192`, `num_predict=2048`

### For High-Volume (64GB+ RAM, GPU)
- Use: `llama3:70b`
- Settings: `num_ctx=8192`, `num_predict=2048`

## Custom Marketing Model

Create a custom model optimized for marketing:

```bash
# Build custom model from Modelfile
docker exec ollama ollama create marketing -f /app/Modelfile.marketing

# Test custom model
curl http://localhost:11434/api/generate -d '{
  "model": "marketing",
  "prompt": "Write a LinkedIn post about AI automation"
}'
```

## API Usage

### Generate Completion

```python
import requests
import json

def generate_content(prompt: str, model: str = "llama3:8b") -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024
            }
        }
    )
    return response.json()["response"]

# Example
content = generate_content("Write a blog post about B2B marketing automation")
print(content)
```

### Chat Completion

```python
def chat_completion(messages: list, model: str = "llama3:8b") -> str:
    response = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False
        }
    )
    return response.json()["message"]["content"]

# Example
messages = [
    {"role": "system", "content": "You are a B2B marketing expert"},
    {"role": "user", "content": "How do I improve LinkedIn engagement?"}
]
result = chat_completion(messages)
print(result)
```

### Streaming Responses

```python
def stream_generate(prompt: str, model: str = "llama3:8b"):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True
        },
        stream=True
    )

    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            print(data.get("response", ""), end="", flush=True)
            if data.get("done"):
                break

# Example
stream_generate("Write a marketing email about our new product")
```

## Integration with LangChain

```python
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# Initialize Ollama LLM
llm = Ollama(
    base_url="http://ollama:11434",
    model="llama3:8b",
    temperature=0.7
)

# Create chain
template = """
Write a professional {content_type} about {topic}.

Target audience: {audience}
Tone: {tone}
Length: {length} words

{content_type}:
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["content_type", "topic", "audience", "tone", "length"]
)

chain = LLMChain(llm=llm, prompt=prompt)

# Generate content
result = chain.run(
    content_type="LinkedIn post",
    topic="AI in B2B marketing",
    audience="Marketing directors",
    tone="Professional but conversational",
    length="200"
)

print(result)
```

## Performance Optimization

### GPU Acceleration

If you have an NVIDIA GPU:

```yaml
# Already configured in docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

Verify GPU is being used:

```bash
docker exec ollama nvidia-smi
```

### Memory Management

For limited RAM, reduce context window:

```python
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3:8b",
        "prompt": prompt,
        "options": {
            "num_ctx": 2048,      # Reduce from 8192
            "num_predict": 512    # Reduce from 2048
        }
    }
)
```

### Model Unloading

Free up memory by unloading models:

```bash
# Models stay in memory for 5 minutes by default
# Force unload all models
docker restart ollama
```

## Monitoring

### Check Model Status

```bash
# List loaded models
curl http://localhost:11434/api/ps

# Check Ollama logs
docker logs ollama -f

# Monitor GPU usage
docker exec ollama watch -n 1 nvidia-smi
```

### Performance Metrics

```bash
# Check memory usage
docker stats ollama

# Get model info
curl http://localhost:11434/api/show -d '{
  "name": "llama3:8b"
}'
```

## Troubleshooting

### Model Not Found

```bash
# List available models
docker exec ollama ollama list

# Pull missing model
docker exec ollama ollama pull llama3:8b
```

### Out of Memory

```bash
# Check memory usage
docker stats ollama

# Options:
# 1. Use smaller model (mistral:7b instead of llama3:8b)
# 2. Reduce num_ctx parameter
# 3. Increase Docker memory limit
# 4. Use CPU-only mode (slower)
```

### Slow Inference

**For CPU-only systems:**
- Use smaller models (phi:2, mistral:7b)
- Reduce context window
- Use quantized models

**For GPU systems:**
- Verify GPU is detected: `docker exec ollama nvidia-smi`
- Check CUDA installation
- Update NVIDIA drivers

### Connection Refused

```bash
# Check Ollama is running
docker-compose ps ollama

# Restart Ollama
docker-compose restart ollama

# Check logs
docker logs ollama
```

## Model Management

### Update Models

```bash
# Check for updates
docker exec ollama ollama list

# Pull latest version
docker exec ollama ollama pull llama3:8b
```

### Remove Models

```bash
# Remove unused model
docker exec ollama ollama rm codellama:7b

# Remove all models (free up space)
docker exec ollama ollama rm $(docker exec ollama ollama list | awk 'NR>1 {print $1}')
```

### Backup Models

```bash
# Models are stored in Docker volume
# Backup ollama_data volume
docker run --rm \
  -v ollama_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/ollama_data.tar.gz -C /data .
```

## Security

### Best Practices

- ✅ Ollama is only exposed on localhost (not public internet)
- ✅ No authentication required (internal network only)
- ✅ Rate limiting handled by Redis layer
- ✅ Input validation in LangChain service
- ⚠️  For production: Add API gateway with auth

### Network Security

The Ollama service is on the `marketing_network` Docker network and only accessible:
- From other containers in the same network
- From localhost via port 11434

## Cost Comparison

### Self-Hosted (Ollama)
- **Setup**: Free
- **Inference**: Free (just electricity/hosting)
- **Scaling**: Requires your own hardware/cloud GPU instances

### OpenAI API (Alternative)
- **GPT-3.5**: $0.001-0.002 per 1K tokens
- **GPT-4**: $0.03-0.06 per 1K tokens
- **Monthly cost for 1M tokens**: $1,000-$60,000

**Recommendation**: Use Ollama for text generation, paid APIs for media generation (images/videos).

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Llama 3 Model Card](https://ai.meta.com/llama/)
- [Mistral Documentation](https://docs.mistral.ai/)
- [LangChain + Ollama Guide](https://python.langchain.com/docs/integrations/llms/ollama)
