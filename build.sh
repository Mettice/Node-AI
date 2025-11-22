#!/bin/bash

# NodeAI - Vercel Build Script

echo "🚀 Building NodeAI for Vercel..."

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies and build
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

echo "🏗️ Building frontend..."
npm run build

echo "✅ Build complete!"

