"""CLI for reusable native and multi-station absolute UTC configuration files."""
import argparse
from pathlib import Path
from .make_station_media import make_station_media


def main(argv=None):
    """Generate verified media, or audit all source timestamps without encoding."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--output-dir', type=Path)
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--verify-only', action='store_true')
    modes.add_argument('--quality-only', action='store_true',help='Saved-curve noise diagnostics without image decoding')
    args = parser.parse_args(argv)
    if args.quality_only:
        from .run_quality_diagnostics import run_quality_diagnostics
        return run_quality_diagnostics(args.config,args.output_dir)
    return make_station_media(args.config, args.output_dir, args.verify_only)
