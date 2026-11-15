#!/usr/bin/env bash
# Build the curriculum-curator-api sidecar and stage Pandoc/Typst for Electron.
set -euo pipefail

ROOT="$(pwd)"
PLATFORM="${PLATFORM:-mac}"
if [ "$PLATFORM" = "win" ]; then
  EXT=".exe"
else
  EXT=""
fi

python -m pip install --disable-pip-version-check uv
uv python install 3.13
rm -rf .venv-sidecar
uv venv --python 3.13 --seed .venv-sidecar
if [ -f .venv-sidecar/bin/activate ]; then
  source .venv-sidecar/bin/activate
else
  source .venv-sidecar/Scripts/activate
fi

cd backend
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -e .
pyinstaller --onefile --console --name curriculum-curator-api \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols \
  --hidden-import uvicorn.protocols.http \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.protocols.websockets \
  --hidden-import uvicorn.protocols.websockets.auto \
  --hidden-import uvicorn.lifespan \
  --hidden-import uvicorn.lifespan.on \
  --hidden-import uvicorn.lifespan.off \
  --hidden-import multipart \
  --hidden-import email_validator \
  --hidden-import passlib.handlers.bcrypt \
  --hidden-import jose \
  --hidden-import litellm \
  --hidden-import tiktoken \
  --hidden-import tiktoken_ext \
  --hidden-import tiktoken_ext.openai_public \
  --hidden-import sqlalchemy.dialects.sqlite \
  --collect-data litellm \
  --collect-data tiktoken_ext \
  --collect-data spellchecker \
  --collect-submodules app \
  --paths . \
  run_server.py

./dist/curriculum-curator-api$EXT --port 8199 > server.log 2>&1 &
PID=$!
ready=0
for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8199/health; then
    ready=1
    break
  fi
  sleep 1
done
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
if [ "$ready" -ne 1 ]; then
  echo "Backend health check failed"
  cat server.log || true
  exit 1
fi

mkdir -p "$ROOT/desktop/backend-dist"
cp "dist/curriculum-curator-api$EXT" "$ROOT/desktop/backend-dist/"

cd "$ROOT"
mkdir -p desktop/vendor/pandoc
PANDOC_VERSION="3.6.4"
case "$PLATFORM" in
  mac)
    curl -fsSL "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-arm64-macOS.zip" -o pandoc.zip
    unzip -q pandoc.zip -d pandoc-tmp
    cp "pandoc-tmp/pandoc-${PANDOC_VERSION}-arm64/bin/pandoc" desktop/vendor/pandoc/
    ;;
  win)
    curl -fsSL "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-windows-x86_64.zip" -o pandoc.zip
    unzip -q pandoc.zip -d pandoc-tmp
    cp "pandoc-tmp/pandoc-${PANDOC_VERSION}/pandoc.exe" desktop/vendor/pandoc/
    ;;
  linux)
    curl -fsSL "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-amd64.tar.gz" -o pandoc.tar.gz
    tar xzf pandoc.tar.gz
    cp "pandoc-${PANDOC_VERSION}/bin/pandoc" desktop/vendor/pandoc/
    ;;
esac

mkdir -p desktop/vendor/typst
TYPST_VERSION="v0.13.1"
case "$PLATFORM" in
  mac)
    curl -fsSL "https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-aarch64-apple-darwin.tar.xz" -o typst.tar.xz
    tar xf typst.tar.xz
    cp typst-aarch64-apple-darwin/typst desktop/vendor/typst/
    ;;
  win)
    curl -fsSL "https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-x86_64-pc-windows-msvc.zip" -o typst.zip
    unzip -q typst.zip -d typst-tmp
    cp "typst-tmp/typst-x86_64-pc-windows-msvc/typst.exe" desktop/vendor/typst/
    ;;
  linux)
    curl -fsSL "https://github.com/typst/typst/releases/download/${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" -o typst.tar.xz
    tar xf typst.tar.xz
    cp typst-x86_64-unknown-linux-musl/typst desktop/vendor/typst/
    ;;
esac

ls -la desktop/backend-dist desktop/vendor/pandoc desktop/vendor/typst
