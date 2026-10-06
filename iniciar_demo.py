from pathlib import Path
import os, runpy, sys
root = Path(__file__).resolve().parent
os.chdir(root)
sys.path.insert(0, str(root / "src"))
runpy.run_path(str(root / "src" / "main.py"), run_name="__main__")
