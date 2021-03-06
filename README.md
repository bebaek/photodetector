# Photodetector

Splits photographs in a scanned image. If you have a pile of photographs to
scan and archive, scan multiple photographs together and use photodetector
to automatically generate separate photograph files.

Based on Python, OpenCV for image segmentation, tilt correction, trim, and
recursive path traversal.


## Installation

Prerequisites: git, python3.

Download repo:

    git clone https://github.com/bebaek/photodetector.git

Install:

    pip install photodetector


## Usage

Run command line applicaton:

    photodetector PATH

`PATH` is either filename or directory name. Resulting files will be saved in
`out` directory.

Use optional parameters as needed, for example:

    photodetector --left-trim 40 --thresh 200 --outdir outgoing/ incoming/

Run `photodetector -h` to see the full list of options.

In order to use in your Python script or application, import the package and
use the main class `ImageProcessor`:

    from photodetector import ImageProcessor
    
    path = 'foo/*.jpg'

    ip = ImageProcessor()
    ip.load(path)
    ip.extract_photos()
    ip.save(outdir='foo-out')

Output images may have wrong orientations. Use the accompanying command to
interactively fix that:

    photorot SOURCE_FOLDER TARGET_FOLDER

## Uninstalling

Run the standard pip command:

    pip uninstall photodetector


## Development

Prerequisites: git, bash, python3, python3-venv.

Download repo:

    git clone https://github.com/bebaek/photodetector.git

Run setup script to create the virtual environment and install photodetector
package in the development mode:

    bash ci/setup-devenv.sh

Run unit tests as needed at the root of the repo:

    python -m unittest

Conform to PEP 8 and check the code style:

    flake8
