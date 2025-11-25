#!/bin/bash
# Quick Start Script - Just runs the main simulation

echo "========================================"
echo "   UavNetSim - Quick Start"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.12+ using:"
    echo "  Mac: brew install python@3.12"
    echo "  Linux: sudo apt install python3.12"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check/Install uv
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    pip3 install uv
fi

# Go to project root
cd "$(dirname "$0")/.."

# Run main simulation
echo ""
echo "Starting UavNetSim..."
echo ""
uv run main.py

read -p "Press Enter to exit..."

