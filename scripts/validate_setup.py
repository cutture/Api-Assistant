#!/usr/bin/env python3
"""
Production Readiness Validation Script.

This script validates that the application is properly configured and ready to run.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is 3.11 or higher."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        return True, f"✅ Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.11+)"


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists."""
    env_file = Path(".env")
    if env_file.exists():
        return True, "✅ .env file found"
    else:
        return False, "❌ .env file not found (copy .env.example to .env)"


def check_required_env_vars() -> List[Tuple[bool, str]]:
    """Check for required environment variables."""
    from dotenv import load_dotenv
    load_dotenv()

    results = []

    # Check LLM provider
    llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    results.append((True, f"✅ LLM_PROVIDER: {llm_provider}"))

    if llm_provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
        results.append((True, f"   OLLAMA_BASE_URL: {ollama_url}"))
        results.append((True, f"   OLLAMA_MODEL: {ollama_model}"))
    elif llm_provider == "groq":
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key:
            masked_key = groq_key[:8] + "..." if len(groq_key) > 8 else "***"
            results.append((True, f"   GROQ_API_KEY: {masked_key}"))
        else:
            results.append((False, "   ❌ GROQ_API_KEY not set"))

    return results


def check_dependencies() -> List[Tuple[bool, str]]:
    """Check if required packages are installed."""
    results = []

    required_packages = [
        ("streamlit", "Streamlit"),
        ("chromadb", "ChromaDB"),
        ("sentence_transformers", "SentenceTransformers"),
        ("langchain", "LangChain"),
        ("langgraph", "LangGraph"),
        ("ollama", "Ollama"),
        ("structlog", "Structlog"),
        ("pydantic", "Pydantic"),
    ]

    for package, name in required_packages:
        try:
            __import__(package)
            results.append((True, f"✅ {name}"))
        except ImportError:
            results.append((False, f"❌ {name} not installed"))

    # Optional: Groq
    try:
        __import__("groq")
        results.append((True, f"✅ Groq (optional)"))
    except ImportError:
        results.append((True, f"⚠️  Groq not installed (optional for cloud mode)"))

    return results


def check_directories() -> List[Tuple[bool, str]]:
    """Check if required directories exist."""
    results = []

    required_dirs = [
        "src",
        "src/agents",
        "src/core",
        "src/services",
        "src/ui",
        "tests",
        "data",
    ]

    for dir_path in required_dirs:
        if Path(dir_path).exists():
            results.append((True, f"✅ {dir_path}/"))
        else:
            results.append((False, f"❌ {dir_path}/ not found"))

    # Check data directories
    Path("data/chroma_db").mkdir(parents=True, exist_ok=True)
    results.append((True, "✅ data/chroma_db/ (created if missing)"))

    return results


def check_ollama_connection() -> Tuple[bool, str]:
    """Check if Ollama is accessible (if using ollama provider)."""
    from dotenv import load_dotenv
    load_dotenv()

    llm_provider = os.getenv("LLM_PROVIDER", "ollama")

    if llm_provider != "ollama":
        return True, "⏭️  Skipped (not using Ollama)"

    try:
        import requests
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            target_model = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")

            if any(target_model in name for name in model_names):
                return True, f"✅ Ollama running with {target_model}"
            else:
                return False, f"❌ Ollama running but {target_model} not found. Available: {', '.join(model_names[:3])}"
        else:
            return False, f"❌ Ollama responded with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "❌ Cannot connect to Ollama (is `ollama serve` running?)"
    except requests.exceptions.Timeout:
        return False, "❌ Ollama connection timeout"
    except Exception as e:
        return False, f"❌ Ollama check failed: {str(e)}"


def main():
    """Run all validation checks."""
    print("=" * 70)
    print("API Integration Assistant - Production Readiness Validation")
    print("=" * 70)
    print()

    all_passed = True

    # Python version
    print("1. Python Version")
    passed, msg = check_python_version()
    print(f"   {msg}")
    if not passed:
        all_passed = False
    print()

    # Environment file
    print("2. Environment Configuration")
    passed, msg = check_env_file()
    print(f"   {msg}")
    if not passed:
        all_passed = False
        print()
        print("   To fix: cp .env.example .env")
        print()
    else:
        # Check env vars
        env_results = check_required_env_vars()
        for passed, msg in env_results:
            print(f"   {msg}")
            if not passed:
                all_passed = False
    print()

    # Dependencies
    print("3. Python Dependencies")
    dep_results = check_dependencies()
    for passed, msg in dep_results:
        print(f"   {msg}")
        if not passed:
            all_passed = False
    print()

    if not all([r[0] for r in dep_results]):
        print("   To fix: pip install -r requirements.txt")
        print()

    # Directories
    print("4. Directory Structure")
    dir_results = check_directories()
    for passed, msg in dir_results:
        print(f"   {msg}")
        if not passed:
            all_passed = False
    print()

    # Ollama connection
    print("5. LLM Provider Connection")
    passed, msg = check_ollama_connection()
    print(f"   {msg}")
    if not passed:
        all_passed = False
        print()
        print("   To fix:")
        print("   - Start Ollama: ollama serve")
        print("   - Pull model: ollama pull deepseek-coder:6.7b")
        print("   - OR switch to Groq: LLM_PROVIDER=groq in .env")
        print()

    # Summary
    print("=" * 70)
    if all_passed:
        print("✅ All checks passed! Ready to run:")
        print()
        print("   streamlit run src/main.py")
        print()
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
