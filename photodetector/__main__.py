import argparse
import logging

from .image_processor import ImageProcessor


def main():
    """Entry point."""
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='file or directory', nargs='+')
    parser.add_argument('--outdir', help='output directory')
    parser.add_argument('--threshold', type=int, default=220,
                        help='threshold in grayscale')
    parser.add_argument('--min-area', type=int, default=50000, help='min area')
    parser.add_argument('--left-trim', type=int, default=0,
                        help='left edge thickness to trim')
    parser.add_argument('--no-close', help='do not close speckles',
                        action='store_true')
    parser.add_argument('--no-suppress-overlap',
                        help='do not suppress overlapping contours',
                        action='store_true')
    parser.add_argument('--diagnose', help='diagnose mode',
                        action='store_true')
    args = parser.parse_args()

    level = logging.DEBUG if args.diagnose else logging.INFO
    logging.basicConfig(level=level)

    processor = ImageProcessor(
        outdir=args.outdir,
        thresh=args.threshold,
        min_area=args.min_area,
        left_trim=args.left_trim,
        close=not args.no_close,
        no_suppress_overlap=args.no_suppress_overlap,
        diagnose=args.diagnose,
    )
    processor.run(args.path)
    processor.report()
