#!/bin/bash
# Quick start script for Bitrix24 Chat Application

echo ""
echo "=========================================="
echo "🚀 Bitrix24 Chat Application"
echo "=========================================="
echo ""

# Check if .env file exists with token
if grep -q "BITRIX_REST_TOKEN" .env 2>/dev/null; then
    echo "✅ Token found in .env"
    echo "   Starting chat application..."
    echo ""
    python3 run_chat.py
else
    echo "❌ Token not found in .env"
    echo ""
    echo "To get started:"
    echo "1. Run: python3 main.py"
    echo "2. Complete the authentication"
    echo "3. Token will be saved to .env"
    echo "4. Run this script again"
    echo ""
fi
