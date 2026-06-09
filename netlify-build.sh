#!/bin/bash
set -e

echo "=== Installing Flutter ==="
git clone https://github.com/flutter/flutter.git --depth 1 -b stable /opt/flutter
export PATH="$PATH:/opt/flutter/bin"

flutter --version

echo "=== Enabling Web Support ==="
flutter config --enable-web

echo "=== Installing Dependencies ==="
cd flutter_app
flutter pub get

echo "=== Building Web App ==="
# API_BASE_URL is set as a Netlify environment variable
flutter build web \
  --dart-define=API_BASE_URL=${API_BASE_URL:-http://127.0.0.1:8000} \
  --release

echo "=== Build Complete ==="
