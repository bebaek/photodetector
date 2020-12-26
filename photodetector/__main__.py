import argparse
import logging

from .image_processor import ImageProcessor


def main():
    """Entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='file or directory', nargs='+')
    parser.add_argument('--diagnose', help='diagnose mode',
                        action='store_true')
    parser.add_argument('--min-area', type=int, help='min area')
    parser.add_argument('--trim-left-edge', type=int, help='trim left edge')
    args = parser.parse_args()

    level = logging.DEBUG if args.diagnose else logging.INFO
    logging.basicConfig(level=level)

    ImageProcessor(
        diagnose=args.diagnose,
        min_area=args.min_area,
        trim_left_edge=args.trim_left_edge,
    ).run(args.path)
