"""Check sample recipients in database."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from database.connection import DatabaseManager
from database.models import Recipient

db = DatabaseManager()

with db.get_session() as session:
    recipients = session.query(Recipient).limit(20).all()
    print(f"\nTotal recipients in database: {session.query(Recipient).count()}")
    print("\nSample recipients:")
    for r in recipients:
        print(f"  - {r.name} ({r.acronym}) - {r.city}, {r.state}")
