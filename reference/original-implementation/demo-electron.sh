#!/bin/bash
echo "🎪 Starting Curriculum Curator Electron Demo"
echo "=========================================="

# Start demo server in background
echo "🚀 Starting demo API server..."
python demo-server.py &
API_PID=$!

# Wait for API to start
sleep 2

# Start React in background
echo "⚛️  Starting React frontend..."
cd web
npm start &
REACT_PID=$!

# Wait for React to start
echo "⏳ Waiting for React to compile..."
sleep 10

# Start Electron
echo "🖥️  Starting Electron app..."
cd ../electron
npx electron main-demo.js --no-sandbox

# Cleanup when Electron closes
echo "🧹 Cleaning up..."
kill $API_PID $REACT_PID 2>/dev/null

echo "✅ Demo completed!"