"""
Launcher script for API Integration Assistant.
Handles Python path configuration automatically.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now run the Streamlit app
if __name__ == "__main__":
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", "src/main.py"]
    stcli.main()