#!/bin/bash

echo "Starting AITradeAgent Frontend..."

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

echo "Starting Vite development server..."
npm run dev
