import os, sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fore_poster import app

if __name__ == "__main__":
    app.run()