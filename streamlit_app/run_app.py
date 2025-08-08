"""
Streamlit app runner with proper path setup.
This ensures the imports work correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

# Now import and run the main app
if __name__ == "__main__":
    from streamlit_app.app import main
    main()