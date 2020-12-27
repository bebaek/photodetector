"""
Rotate images by 90 degs interactively.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np

BOLD = '\033[1m'
ENDC = '\033[0m'

ENTER = 13
ESC = 27


def photorot(source, target):
    """Interactively rotate and save photos.
    """
    source = Path(source)
    target = Path(target)

    # FIXME: generalize
    im_paths = sorted(list(source.glob('*.webp')))

    print(f'{BOLD}Photo rotator{ENDC}')
    print('Keys: [Space] rotate, [Enter] save and next, [ESC] exit')
    print()
    print(f'Found {len(im_paths)} images.')
    if len(im_paths) < 1:
        return

    if target.exists():
        inp = input(
            f'Target folder "{target}" exists. OK to overwrite? (y/[N]) ')
        if inp.lower().strip() != 'y':
            print('Quitting...')
            return

    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('image', 800, 800)

    # Show pics and get user input
    for i, im_path in enumerate(im_paths, start=1):
        print(f'{i:4}:', im_path)

        im = cv2.imread(str(im_path))
        cv2.imshow('image', im)
        while True:
            key = cv2.waitKey(0)
            if key == ord(' '):
                im = np.rot90(im, 1)
                cv2.imshow('image', im)

            if key in (ord('n'), ENTER):
                target.mkdir(parents=True, exist_ok=True)
                out_path = target / im_path.name
                cv2.imwrite(str(out_path), im)
                break

            if key in (ord('q'), ESC):
                print('Quitting...')
                cv2.destroyAllWindows()
                return

    cv2.destroyAllWindows()
    print('Done.')


def main():
    """Entrypoint.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='source directory')
    parser.add_argument('target', help='target directory')
    args = parser.parse_args()

    photorot(args.source, args.target)


if __name__ == '__main__':
    main()
