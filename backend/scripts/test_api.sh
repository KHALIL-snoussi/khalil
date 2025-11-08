#!/bin/bash
# Test script for Diamond Painting Generator API

set -e

API_URL="${API_URL:-http://localhost:8000}"
SAMPLE_IMAGE="${SAMPLE_IMAGE:-samples/portrait1.jpg}"

echo "=== Diamond Painting Generator API Test ==="
echo "API URL: $API_URL"
echo "Sample Image: $SAMPLE_IMAGE"
echo ""

# Check if sample image exists
if [ ! -f "$SAMPLE_IMAGE" ]; then
    echo "Error: Sample image not found: $SAMPLE_IMAGE"
    echo "Run: python scripts/generate_test_image.py"
    exit 1
fi

# Test 1: Health check
echo "1. Testing health endpoint..."
response=$(curl -s "$API_URL/health")
if echo "$response" | grep -q '"ok":true'; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    echo "Response: $response"
    exit 1
fi
echo ""

# Test 2: Preview generation
echo "2. Testing preview generation..."
payload='{
  "crop": {"x": 0, "y": 0, "w": 1000, "h": 1400},
  "rotate_deg": 0,
  "grid": {"w": 100, "h": 140},
  "styles": ["original", "vintage", "popart"],
  "options": {
    "gamma": 1.0,
    "edge_boost": 0.25,
    "dither": "fs",
    "dither_strength": 1.0
  }
}'

response=$(curl -s -X POST "$API_URL/preview" \
    -F "image=@$SAMPLE_IMAGE" \
    -F "payload=$payload")

# Extract job_id
job_id=$(echo "$response" | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$job_id" ]; then
    echo "✓ Preview generated successfully"
    echo "  Job ID: $job_id"
else
    echo "✗ Preview generation failed"
    echo "Response: $response"
    exit 1
fi

# Check if previews are present
if echo "$response" | grep -q '"previews"'; then
    echo "  ✓ Previews present in response"
else
    echo "  ✗ No previews in response"
fi

# Check if counts are present
if echo "$response" | grep -q '"counts"'; then
    echo "  ✓ Color counts present in response"
else
    echo "  ✗ No color counts in response"
fi
echo ""

# Test 3: Final pattern generation
echo "3. Testing final pattern generation..."
final_payload="{
  \"job_id\": \"$job_id\",
  \"style\": \"original\",
  \"grid\": {\"w\": 100, \"h\": 140},
  \"palette_id\": \"original_v1\",
  \"crop\": {\"x\": 0, \"y\": 0, \"w\": 1000, \"h\": 1400},
  \"rotate_deg\": 0,
  \"options\": {
    \"gamma\": 1.0,
    \"edge_boost\": 0.25,
    \"dither\": \"fs\",
    \"dither_strength\": 1.0
  }
}"

output_file="test_pattern.zip"
http_code=$(curl -s -o "$output_file" -w "%{http_code}" \
    -X POST "$API_URL/final" \
    -H "Content-Type: application/json" \
    -d "$final_payload")

if [ "$http_code" = "200" ] && [ -f "$output_file" ]; then
    file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
    if [ "$file_size" -gt 1000 ]; then
        echo "✓ Final pattern generated successfully"
        echo "  Output: $output_file"
        echo "  Size: $file_size bytes"

        # List ZIP contents
        echo "  Contents:"
        unzip -l "$output_file" | grep -E '(pattern.pdf|preview.png|counts.csv|spec.json)' | sed 's/^/    /'
    else
        echo "✗ Final pattern file too small"
        rm -f "$output_file"
        exit 1
    fi
else
    echo "✗ Final pattern generation failed (HTTP $http_code)"
    rm -f "$output_file"
    exit 1
fi
echo ""

echo "=== All tests passed! ==="
echo ""
echo "Generated file: $output_file"
echo "Extract with: unzip $output_file"
