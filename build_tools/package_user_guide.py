"""Place first-use documentation and editable templates beside the application."""
from pathlib import Path
import shutil


def copy_user_guide(root, destination):
    """Copy relative-link-compatible guides into a distribution directory.

    Parameters are filesystem Paths for the project root and package folder.
    Templates contain placeholder paths, never observation data. Existing guide
    files are refreshed; application binaries and user data are not modified.
    """
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('README.md', 'README.zh-CN.md', 'THIRD_PARTY.md'):
        shutil.copy2(root / name, destination / name)
    for folder in ('examples', 'docs'):
        (destination / folder).mkdir(exist_ok=True)
    for path in (root / 'examples').glob('*.json'):
        shutil.copy2(path, destination / 'examples' / path.name)
    shutil.copy2(root / 'docs/native_station_media.md',
                 destination / 'docs/native_station_media.md')
