import argparse
import logging

from .image_processor import ImageProcessor


def main():
    """Entry point."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'path', help='file or directory', nargs='+')
    args = parser.parse_args()

    ImageProcessor().run(args.path)
