import logging
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Processor of an image containing rectangular scanned photos."""
    def __init__(self, outdir='out', thresh=200, min_area=50000,
                 left_trim=0, right_trim=0, top_trim=0, close=True,
                 no_suppress_overlap=True, diagnose=False):
        self.outdir = outdir
        self.thresh = thresh
        self.min_area = min_area
        self.max_aspect = 4
        self.left_trim = left_trim
        self.right_trim = right_trim
        self.top_trim = top_trim
        self.close = close
        self.no_suppress_overlap = no_suppress_overlap
        self.diagnose = diagnose  # diagnose mode

        # Abnormal images for users to check after
        self.abnormal = []

    def make_binary(self):
        im = self.source
        imgray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)

        # Trim edge as needed
        if self.left_trim:
            imgray[:, :self.left_trim] = 255
        if self.right_trim:
            imgray[:, -self.right_trim:] = 255
        if self.top_trim:
            imgray[:self.top_trim, :] = 255

        # Make a binary image to exclude white or black background
        ret, thresh = cv2.threshold(imgray, self.thresh, 255,
                                    cv2.THRESH_BINARY_INV)

        # Remove noise
        self.closing = thresh
        if self.close:
            kernel = np.ones((5, 5), np.uint8)
            self.closing = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

        if self.diagnose:
            self.imgray = imgray

    def find_contours(self, image, final=False):
        all_contours, hierarchy = cv2.findContours(
            image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by size etc
        contours = []
        extracted_area = 0
        for cnt in all_contours:
            area = cv2.contourArea(cnt)
            # FIXME: replace with final box areas
            extracted_area += area
            _, _, w, h = cv2.boundingRect(cnt)
            aspect = max(w / h, h / w)
            if area > self.min_area and aspect < self.max_aspect:
                contours.append(cnt)

        if len(contours) > 20:
            raise RuntimeError(f'Too many contours found: {len(contours)}.')

        if final:
            h, w = self.source.shape[:2]
            extraction_frac = extracted_area / (h * w)
            if extraction_frac < 0.5:
                self.abnormal.append(self.source_path)
            logger.info(
                'Found {} contours with {:.0%} area'.format(
                    len(contours), extraction_frac,
                )
            )

        return contours

    def fill_contours(self, contours):
        """Return binary image with filled contours for non-overlapping contour
        search.
        """
        rects = []
        boxes = []
        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            rects.append(rect)
            boxes.append(np.int0(box))

        im_cnt = np.zeros_like(self.closing)
        cv2.drawContours(im_cnt, boxes, -1, 255, -1)
        if self.diagnose:
            self.filled = im_cnt
        return im_cnt

    def draw_contours(self):
        self.rects = []
        self.boxes = []
        for cnt in self.contours:
            rect = cv2.minAreaRect(cnt)
            box = cv2.boxPoints(rect)
            self.rects.append(rect)
            self.boxes.append(np.int0(box))

        if self.diagnose:
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

        # Initial contours. A box may contain another
        self.contours = self.find_contours(self.closing,
                                           final=self.no_suppress_overlap)

        # Get nonoverlapping contours from initial contours
        if not self.no_suppress_overlap:
            im_cnt = self.fill_contours(self.contours)
            self.contours = self.find_contours(im_cnt, final=True)

        self.draw_contours()
        self.crop()

    def load(self, file):
        self.source_path = Path(file)
        self.source = cv2.imread(str(file))
        logger.info(f'Loaded image from {self.source_path}.')

    def save(self, prefix='', ext=None):
        if ext is None:
            ext = self.source_path.suffix

        if prefix.strip() == '':
            prefix = self.source_path.stem
        prefix = str(prefix)

        Path(self.outdir).mkdir(parents=True, exist_ok=True)

        for i, img in enumerate(self.subimages):
            fname = '{}/{}-{}{}'.format(self.outdir, prefix, i + 1, ext)
            if Path(fname).exists():
                logger.warning(f'File exists. Skipped saving to {fname}.')
            else:
                cv2.imwrite(fname, img)

        logger.info(f'Saved {len(self.subimages)} images in {self.outdir}.')

        if self.diagnose:
            fname = '{}/{}-{}{}'.format(self.outdir, prefix, 'gray', ext)
            cv2.imwrite(fname, self.imgray)
            fname = '{}/{}-{}{}'.format(self.outdir, prefix, 'closing', ext)
            cv2.imwrite(fname, self.closing)
            if not self.no_suppress_overlap:
                fname = '{}/{}-{}{}'.format(self.outdir, prefix, 'filled', ext)
                cv2.imwrite(fname, self.filled)
            fname = '{}/{}-{}{}'.format(self.outdir, prefix, 'boxes', ext)
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

        path = map(Path, path)

        for p in path:
            # Directory: recurse in
            if Path(p).is_dir():
                subpaths = sorted(list(Path(p).iterdir()))
                for subp in subpaths:
                    self.run(subp)

            # File: process
            else:
                if p.suffix.lower() not in [
                        '.jpg', '.jpeg', '.webp', '.png', 'tif', 'tiff']:
                    continue
                self.load(p)
                self.extract_photos()
                self.save()

    def report(self):
        if self.abnormal:
            files = '\n'.join(map(str, self.abnormal))
            logger.info(
                f'These files have small extraction areas (< 50%):\n{files}')
        else:
            logger.info('All files have large extraction areas.')
