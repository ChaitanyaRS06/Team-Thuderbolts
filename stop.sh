#!/bin/bash

echo "🛑 Stopping UVA AI Research Assistant..."
echo ""

docker-compose down

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "To start again, run: ./start.sh"
