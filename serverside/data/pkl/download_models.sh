#!/bin/bash

set -e

# Resolve the directory this script lives in
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Downloading contraindication embeddings..."
wget -O "$SCRIPT_DIR/contraindication_embeddings_final.pkl" \
https://github.com/M-Tameem/baymax/releases/download/1.0/contraindication_embeddings_final.pkl

echo "Downloading ddinter embeddings..."
wget -O "$SCRIPT_DIR/ddinter_embeddings_final.pkl" \
https://github.com/M-Tameem/baymax/releases/download/1.0/ddinter_embeddings_final.pkl

echo "All models downloaded successfully into $SCRIPT_DIR"
