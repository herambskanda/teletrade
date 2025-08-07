"""Script to run the Streamlit dashboard."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit dashboard."""
    
    # Set the path to the streamlit app
    app_path = Path(__file__).parent / "streamlit_app" / "app.py"
    
    # Run streamlit
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    print("Starting Streamlit dashboard...")
    print(f"Dashboard will be available at: http://localhost:8501")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nStreamlit dashboard stopped.")

if __name__ == "__main__":
    main()