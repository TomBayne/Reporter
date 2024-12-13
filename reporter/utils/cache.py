from pathlib import Path
from datetime import datetime, timedelta
import json

def get_latest_narrative(output_dir: str, max_age_hours: float = 23.98) -> str:
    """Get the most recent narrative if within max age (23h59m)."""
    base_path = Path(output_dir)
    if not base_path.exists():
        return None

    # Get all timestamped directories
    dirs = [d for d in base_path.iterdir() if d.is_dir()]
    if not dirs:
        return None

    # Sort by directory name (timestamp format)
    latest_dir = sorted(dirs)[-1]
    
    # Check if within age limit
    try:
        dir_time = datetime.strptime(latest_dir.name, "%Y%m%d_%H%M%S")
        if datetime.now() - dir_time > timedelta(hours=max_age_hours):
            return None
    except ValueError:
        return None

    # Read the narrative file
    narrative_file = latest_dir / "narrative.md"
    if not narrative_file.exists():
        return None

    return narrative_file.read_text(encoding='utf-8')
