import argparse
import logging

from .image_processor import ImageProcessor


def main():
    """Entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='file or directory', nargs='+')
    parser.add_argument('--outdir', help='output directory')
    parser.add_argument('--min-area', type=int, help='min area')
    parser.add_argument('--trim-left-edge', type=int, help='trim left edge')
    parser.add_argument('--diagnose', help='diagnose mode',
                        action='store_true')
    args = parser.parse_args()

    level = logging.DEBUG if args.diagnose else logging.INFO
    logging.basicConfig(level=level)

    processor = ImageProcessor(
        outdir=args.outdir,
        min_area=args.min_area,
        trim_left_edge=args.trim_left_edge,
        diagnose=args.diagnose,
    )
    processor.run(args.path)
    processor.report()
