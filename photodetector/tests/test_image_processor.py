import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import cv2
from numpy.testing import assert_array_equal

from photodetector.image_processor import ImageProcessor

DATA_PATH = Path(__file__).parent / Path('data')
IMAGE = str(DATA_PATH / Path('sample.jpg'))
BINARY = str(DATA_PATH / Path('binary_sample.png'))
N_PHOTO = 3


class TestImageProcess(unittest.TestCase):
    def test_process_single_file(self):
        ip = ImageProcessor()
        ip.load(IMAGE)

        ip.make_binary()
        binary = cv2.imread(BINARY)  # Reference image
        binary = cv2.cvtColor(binary, cv2.COLOR_BGR2GRAY)
        assert_array_equal(ip.closing, binary)

        ip.find_contours()
        self.assertEqual(len(ip.contours), N_PHOTO)

        ip.draw_contours()
        self.assertEqual(len(ip.boxes), N_PHOTO)

        ip.crop()
        self.assertEqual(len(ip.subimages), N_PHOTO)

        # Save
        with TemporaryDirectory() as tmpdir:
            ip.save(outdir=tmpdir)
            files = list(Path(tmpdir).iterdir())
            self.assertEqual(len(files), N_PHOTO)

            # Existing file warning
            with self.assertLogs(level=logging.WARNING):
                ip.save(outdir=tmpdir)

    @patch.object(ImageProcessor, 'load')
    @patch.object(ImageProcessor, 'extract_photos')
    @patch.object(ImageProcessor, 'save')
    def test_run(self, mock_save, mock_extract_photos, mock_load):
        run_path = DATA_PATH / Path('run_path')
        ip = ImageProcessor()
        ip.run(str(run_path))

        # Recursion
        sample_path = run_path / Path('nested/sample.jpg')
        mock_load.assert_called_once_with(sample_path)
