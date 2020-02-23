from setuptools import find_packages, setup

from photodetector import __version__

setup(
    name='photodetector',
    version=__version__,
    python_requires='>3.6',
    packages=find_packages(),
    package_data={
        '': ['data/*.jpg'],
        '': ['data/*.png'],
    },
    install_requires=[
        'matplotlib',
        'opencv-contrib-python',
    ],
    entry_points={
        'console_scripts': [
            'photodetector = photodetector.__main__:main',
        ],
    },
)
