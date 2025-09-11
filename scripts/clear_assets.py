from pathlib import Path
import sys

# Ensure project root is on sys.path so "app" can be imported when run from anywhere
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import engine

if __name__ == "__main__":
    with engine.begin() as conn:
        conn.exec_driver_sql("DELETE FROM investment")
        conn.exec_driver_sql("DELETE FROM investmentpair")
    print("Cleared tables: investment, investmentpair")
