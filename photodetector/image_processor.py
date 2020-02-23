import logging
from pathlib import Path

import cv2
import numpy as np
from numpy.linalg import norm

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processor of an image containing rectangular scanned photos."""

    def make_binary(self):
        im = self.source
        imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        # Make a binary image
        ret, thresh = cv2.threshold(imgray, 240, 255, cv2.THRESH_BINARY_INV)

        # Remove noise
        kernel = np.ones((5, 5), np.uint8)
        self.closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    def find_contours(self):
        all_contours, hierarchy = cv2.findContours(
            self.closing, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = []
        for cnt in all_contours:
            if cv2.contourArea(cnt) > 400:
                contours.append(cnt)
        self.contours = contours

    def draw_contours(self):
        boxes = []
        for cnt in self.contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            boxes.append(np.int0(box))
        im_cnt = np.copy(self.source)
        cv2.drawContours(im_cnt, boxes, -1, (0, 255, 0), 2)

        self.boxes = boxes
        self.im_cnt = cv2.cvtColor(im_cnt, cv2.COLOR_BGR2RGB)

    def crop(self):
        im = self.source

        # Crop inside contours
        self.subimages = []
        for box in self.boxes:
            # Get all the points inside the box
            mask = np.zeros(im.shape, np.uint8)
            cv2.drawContours(mask, [box], 0, (255, 255, 255), -1)
            masked = np.bitwise_and(mask, im)

            # Crop
            xmin = np.amin(box[:, 0])
            xmax = np.amax(box[:, 0])
            ymin = np.amin(box[:, 1])
            ymax = np.amax(box[:, 1])
            cropped = masked[ymin:ymax + 1, xmin:xmax + 1]

            # Untilt
            vtop = box[np.argmin(box[:, 1])]
            vleft = box[np.argmin(box[:, 0])]
            vright = box[np.argmax(box[:, 0])]
            angle = np.arctan((vright[1] - vtop[1]) / (vright[0] - vtop[0])) \
                * 180 / np.pi
            if angle > 45:
                angle = -(90 - angle)
            center = ((xmax - xmin)/2, (ymax - ymin)/2)
            mat = cv2.getRotationMatrix2D(center, angle, 1)
            cropped_size = cropped.shape[1::-1]
            untilted = cv2.warpAffine(cropped, mat, cropped_size)

            # Trim after untilt
            size = (int(norm(vright - vtop)), int(norm(vleft - vtop)))
            if angle < 0:
                size = size[::-1]
            xmin = int(cropped_size[0] / 2 - size[0] / 2) + 1  # 1 border px
            xmax = int(cropped_size[0] / 2 + size[0] / 2) - 1
            ymin = int(cropped_size[1] / 2 - size[1] / 2) + 1
            ymax = int(cropped_size[1] / 2 + size[1] / 2) - 1
            subim = untilted[ymin:ymax + 1, xmin:xmax + 1]
            self.subimages.append(subim)

    def extract_photos(self):
        """Run all image processing methods."""
        self.make_binary()
        self.find_contours()
        self.draw_contours()
        self.crop()

    def load(self, file):
        self.source_path = Path(file)
        self.source = cv2.imread(str(file))

    def save(self, outdir='out', prefix='', ext='jpg'):
        if prefix.strip() == '':
            prefix = self.source_path.stem
        prefix = str(prefix)

        Path(outdir).mkdir(exist_ok=True)

        for i, img in enumerate(self.subimages):
            fname = '{}/{}-{}.{}'.format(outdir, prefix, i + 1, ext)
            if Path(fname).exists():
                logger.warning(f'File exists. Skipped saving to {fname}.')
            else:
                cv2.imwrite(fname, img)

    def run(self, path):
        """Run all image processes and file handling.

        Parameters
        ----------
        path : str or iterable
            Directory or file name
        """
        if not isinstance(path, (list, tuple)):
            path = [path]

        for p in path:
            # Directory: recurse in
            if Path(p).is_dir():
                subpaths = Path(p).iterdir()
                for subp in subpaths:
                    self.run(subp)

            # File: process
            else:
                self.load(p)
                self.extract_photos()
                self.save()
