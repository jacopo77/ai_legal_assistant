#!/bin/bash
# Quick Railway health check script
# Usage: ./check_railway.sh https://your-railway-url

RAILWAY_URL=$1

if [ -z "$RAILWAY_URL" ]; then
    echo "Usage: ./check_railway.sh https://your-railway-url"
    exit 1
fi

echo "🔍 Testing Railway Backend: $RAILWAY_URL"
echo "================================================"
echo ""

# Test 1: Health check
echo "Test 1: Health Check"
echo "Endpoint: $RAILWAY_URL/healthz"
HEALTH_RESPONSE=$(curl -s "$RAILWAY_URL/healthz")
echo "Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"status":"ok"'; then
    echo "✅ Health check PASSED"
else
    echo "❌ Health check FAILED"
fi
echo ""

# Test 2: Database connection
echo "Test 2: Database Connection"
echo "Endpoint: $RAILWAY_URL/api/health/db"
DB_RESPONSE=$(curl -s "$RAILWAY_URL/api/health/db")
echo "Response: $DB_RESPONSE"

if echo "$DB_RESPONSE" | grep -q '"database":"connected"'; then
    echo "✅ Database connection PASSED"
else
    echo "❌ Database connection FAILED"
fi
echo ""

# Test 3: Chat endpoint (basic test)
echo "Test 3: Chat Endpoint"
echo "Endpoint: $RAILWAY_URL/api/chat/stream"
echo "Question: What is a contract?"
CHAT_RESPONSE=$(curl -s -X POST "$RAILWAY_URL/api/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is a contract?","country":"US"}')
  
if [ -n "$CHAT_RESPONSE" ]; then
    echo "✅ Chat endpoint RESPONDING"
    echo "Response preview: ${CHAT_RESPONSE:0:100}..."
else
    echo "❌ Chat endpoint NOT RESPONDING"
fi
echo ""

echo "================================================"
echo "✅ Railway backend validation complete!"
echo ""
echo "Next step: Deploy to Vercel"
echo "  1. Go to https://vercel.com"
echo "  2. Import your GitHub repo"
echo "  3. Set root directory to 'frontend'"
echo "  4. Add environment variable:"
echo "     NEXT_PUBLIC_BACKEND_URL=$RAILWAY_URL"
echo "  5. Deploy!"
