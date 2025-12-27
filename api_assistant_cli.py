#!/usr/bin/env python3
"""
API Assistant CLI Entry Point.

Run the API Assistant command-line interface.

Usage:
    python api_assistant_cli.py --help
    python api_assistant_cli.py parse file schema.graphql
    python api_assistant_cli.py search "user authentication"
    python api_assistant_cli.py info formats

Author: API Assistant Team
Date: 2025-12-27
"""

from src.cli import app

if __name__ == "__main__":
    app()
