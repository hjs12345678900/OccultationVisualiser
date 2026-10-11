"""CLI for reusable native and multi-station absolute UTC configuration files."""
import argparse
from pathlib import Path
from .make_station_media import make_station_media


def main(argv=None):
    """Generate verified media, or audit all source timestamps without encoding."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--output-dir', type=Path)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args(argv)
    return make_station_media(args.config, args.output_dir, args.verify_only)
