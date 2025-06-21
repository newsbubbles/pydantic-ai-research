#!/bin/bash

# Make scripts executable
chmod +x src/agent_test_fixed.py
chmod +x src/agent_structured_test_fixed.py
chmod +x src/mcp_servers/filesystem_mcp_fixed.py

# Create logs directory if it doesn't exist
mkdir -p logs

# Display helper information
echo "=== PydanticAI Test Runner ==="
echo "This script will run PydanticAI tests."

# Check for API keys
if [[ -z "$OPENAI_API_KEY" && -z "$OPENROUTER_API_KEY" ]]; then
    echo "Warning: No API keys found in environment variables."
    echo "Please set either OPENAI_API_KEY or OPENROUTER_API_KEY before running tests."
    echo "For example: export OPENAI_API_KEY=your-key-here"
    echo "Do you want to continue anyway? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "Exiting."
        exit 1
    fi
fi

# Menu
echo ""
echo "Please select a test to run:"
echo "1. Delta Streaming Test (Basic filesystem operations)"
echo "2. Structured Streaming Test (Directory analysis)"
echo "q. Quit"
read -r choice

case $choice in
    1)
        echo "Running Delta Streaming Test..."
        echo "Log file will be at logs/agent_test.log"
        python3 src/agent_test_fixed.py
        ;;
    2)
        echo "Running Structured Streaming Test..."
        echo "Log file will be at logs/agent_structured_test.log"
        python3 src/agent_structured_test_fixed.py
        ;;
    q|Q)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid choice."
        exit 1
        ;;
esac
