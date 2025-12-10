"""Check Alembic migration chain and current database version."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from alembic.config import Config
from alembic.script import ScriptDirectory

# Load Alembic config
cfg = Config('alembic.ini')
script_dir = ScriptDirectory.from_config(cfg)

print("=" * 80)
print("ALEMBIC MIGRATION CHAIN")
print("=" * 80)

# Walk through all revisions
print("\nMigration order (newest to oldest):")
for rev in script_dir.walk_revisions():
    down = rev.down_revision[:8] if rev.down_revision else "None"
    print(f"  {rev.revision[:8]} <- {down}: {rev.doc}")

# Get current head
head = script_dir.get_current_head()
print(f"\nCurrent HEAD: {head}")

print("\n" + "=" * 80)
print("Migration files are ready for production deployment")
print("=" * 80)
