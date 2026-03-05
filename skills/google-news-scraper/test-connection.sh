#!/bin/bash

# Test Google News API connection

API_KEY="app-ur6S2QXl17jGZrmqr4ssVy3r"
BASE_URL="https://newsapi.org/v2"

echo "🔍 Testing Google News API connection..."
echo "API Key: $API_KEY"
echo ""

# Test basic endpoint
echo "Testing top-headlines endpoint..."
response=$(curl -s "${BASE_URL}/top-headlines?apiKey=${API_KEY}&country=us&pageSize=1")
echo "Response: $response"
echo ""

# Check if it's an error
if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
    status=$(echo "$response" | jq -r '.status')
    if [ "$status" = "error" ]; then
        message=$(echo "$response" | jq -r '.message')
        echo "❌ API Error: $message"
        
        # Try alternative endpoints
        echo ""
        echo "🔄 Trying alternative approach..."
        
        # Test with different parameters
        echo "Testing with different parameters..."
        response2=$(curl -s "${BASE_URL}/top-headlines?apiKey=${API_KEY}&pageSize=1")
        echo "Response: $response2"
        
        # Test sources endpoint
        echo ""
        echo "Testing sources endpoint..."
        response3=$(curl -s "${BASE_URL}/sources?apiKey=${API_KEY}")
        echo "Response: $response3"
        
    else
        echo "✅ API is working!"
        echo "$response" | jq .
    fi
else
    echo "⚠️  Unexpected response format"
fi