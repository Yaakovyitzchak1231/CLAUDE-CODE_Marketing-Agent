#!/bin/bash
# Pull required models for the B2B Marketing Automation Platform

echo "========================================="
echo "Ollama Model Setup"
echo "========================================="
echo ""

# Wait for Ollama to be ready
echo "Waiting for Ollama service to start..."
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "  Still waiting..."
    sleep 5
done
echo "✓ Ollama is ready!"
echo ""

# Pull Llama 3 8B (recommended for 16GB+ RAM)
echo "Pulling Llama 3 8B model..."
echo "  This may take several minutes (4.7GB download)"
ollama pull llama3:8b

if [ $? -eq 0 ]; then
    echo "✓ Llama 3 8B pulled successfully!"
else
    echo "✗ Failed to pull Llama 3 8B"
    exit 1
fi
echo ""

# Pull Mistral 7B (alternative, slightly smaller)
echo "Pulling Mistral 7B model (alternative)..."
echo "  This may take several minutes (4.1GB download)"
ollama pull mistral:7b

if [ $? -eq 0 ]; then
    echo "✓ Mistral 7B pulled successfully!"
else
    echo "✗ Failed to pull Mistral 7B"
fi
echo ""

# Optional: Pull specialized models
# Uncomment if needed

# # Code generation model
# echo "Pulling CodeLlama 7B (optional, for code generation)..."
# ollama pull codellama:7b
# echo ""

# # Smaller model for faster responses
# echo "Pulling Phi-2 (optional, lightweight 2.7B model)..."
# ollama pull phi:2
# echo ""

# List all available models
echo "========================================="
echo "Available Models:"
echo "========================================="
ollama list

echo ""
echo "✓ Model setup complete!"
echo ""
echo "Usage examples:"
echo "  # Test Llama 3:"
echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"llama3:8b\",\"prompt\":\"Hello\"}'"
echo ""
echo "  # Test Mistral:"
echo "  curl http://localhost:11434/api/generate -d '{\"model\":\"mistral:7b\",\"prompt\":\"Hello\"}'"
