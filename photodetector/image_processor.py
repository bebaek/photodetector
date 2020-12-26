import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processor of an image containing rectangular scanned photos."""
    def __init__(self, diagnose=False, min_area=None, trim_left_edge=None):
        self.diagnose = diagnose  # diagnose mode
        self.min_area = (
            min_area if min_area is not None and min_area > 0 else 10000)
        self.max_aspect = 4
        self.trim_left_edge = trim_left_edge

    def make_binary(self):
        im = self.source
        imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        # Trim edge if this is a trouble
        if self.trim_left_edge is not None:
            imgray[:, :self.trim_left_edge] = 255

        # Make a binary image to exclude white or black background
        ret, thresh = cv2.threshold(imgray, 220, 255, cv2.THRESH_BINARY_INV)

        # Remove noise
        kernel = np.ones((5, 5), np.uint8)
        self.closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        if self.diagnose:
            self.imgray = imgray

    def find_contours(self):
        all_contours, hierarchy = cv2.findContours(
            self.closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by size etc
        contours = []
        extracted_area = 0
        for cnt in all_contours:
            area = cv2.contourArea(cnt)
            extracted_area += area
            _, _, w, h = cv2.boundingRect(cnt)
            aspect = max(w / h, h / w)
            if area > self.min_area and aspect < self.max_aspect:
                contours.append(cnt)
        self.contours = contours

        if len(contours) > 20:
            raise RuntimeError(f'Too many contours found: {len(contours)}.')

        logger.debug(f'{len(contours)} contours found.')

        h, w = self.source.shape[:2]
        extraction_pct = extracted_area / (h * w)
        logger.info(f'Extracted area: {extraction_pct:.0%}')

    def draw_contours(self):
        self.rects = []
        self.boxes = []
        for cnt in self.contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            self.rects.append(rect)
            self.boxes.append(np.int0(box))
        im_cnt = np.copy(self.source)
        cv2.drawContours(im_cnt, self.boxes, -1, (0, 255, 0), 2)

        self.im_cnt = cv2.cvtColor(im_cnt, cv2.COLOR_BGR2RGB)

    def crop(self):
        im = self.source

        # Crop inside contours
        self.subimages = []
        if self.diagnose:
            self.box_mask = np.zeros(im.shape, np.uint8)
            self.im_masked = np.zeros(im.shape, np.uint8)
        for rect, box in zip(self.rects, self.boxes):
            # Get all the points inside the box
            mask = np.zeros(im.shape, np.uint8)
            cv2.drawContours(mask, [box], 0, (255, 255, 255), -1)
            if self.diagnose:
                self.box_mask = np.bitwise_or(self.box_mask, mask)

            masked = np.bitwise_and(mask, im)
            if self.diagnose:
                self.im_masked = np.bitwise_or(self.im_masked, masked)

            # Fix orientation to right angle
            width = int(rect[1][0])
            height = int(rect[1][1])
            src_pts = box.astype("float32")
            dst_pts = np.array([[0, height - 1],
                                [0, 0],
                                [width - 1, 0],
                                [width - 1, height - 1]], dtype="float32")
            M = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(masked, M, (width, height))

            self.subimages.append(warped)

    def extract_photos(self):
        """Run all image processing methods."""
        self.make_binary()
        self.find_contours()
        self.draw_contours()
        self.crop()

    def load(self, file):
        self.source_path = Path(file)
        self.source = cv2.imread(str(file))
        logger.info(f'Loaded image from {self.source_path}.')

    def save(self, outdir='out', prefix='', ext=None):
        if ext is None:
            ext = self.source_path.suffix

        if prefix.strip() == '':
            prefix = self.source_path.stem
        prefix = str(prefix)

        Path(outdir).mkdir(exist_ok=True)

        for i, img in enumerate(self.subimages):
            fname = '{}/{}-{}{}'.format(outdir, prefix, i + 1, ext)
            if Path(fname).exists():
                logger.warning(f'File exists. Skipped saving to {fname}.')
            else:
                cv2.imwrite(fname, img)

        logger.info(f'Saved {len(self.subimages)} images in {outdir}.')

        if self.diagnose:
            fname = '{}/{}-{}{}'.format(outdir, prefix, 'gray', ext)
            cv2.imwrite(fname, self.imgray)
            fname = '{}/{}-{}{}'.format(outdir, prefix, 'closing', ext)
            cv2.imwrite(fname, self.closing)
            fname = '{}/{}-{}{}'.format(outdir, prefix, 'boxes', ext)
            cv2.imwrite(fname, self.box_mask)

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
