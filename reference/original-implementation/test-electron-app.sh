#!/bin/bash
echo "🚀 Testing Curriculum Curator Electron App"
echo "========================================="
echo ""
echo "Starting the app with --no-sandbox flag..."
echo ""

cd electron/dist/linux-unpacked
./curriculum-curator-electron --no-sandbox &
APP_PID=$!

echo "App started with PID: $APP_PID"
echo ""
echo "Waiting 10 seconds for app to initialize..."
sleep 10

echo ""
echo "Checking if app is still running..."
if ps -p $APP_PID > /dev/null; then
    echo "✅ App is running successfully!"
    echo ""
    echo "The Electron window should be open on your desktop."
    echo "You may see some Python-related errors in the console (expected without dependencies)."
    echo ""
    echo "Press Ctrl+C to stop the app."
    wait $APP_PID
else
    echo "❌ App exited. Check the error messages above."
fi