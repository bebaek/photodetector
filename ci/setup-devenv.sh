#!/bin/bash
# Set up development env.

echo Start: set up Python environment.

devenv=photodetector

# Packages for development
pkgs=(flake8 ipython matplotlib opencv-contrib-python)

# Create virtual environment. python3-venv is required.
# Use _venv/. Spacemacs cannot even handle the presence of .venv/.
echo Creating virtual environment...
python3 -m venv --clear ~/_venv/photodetector
. ~/_venv/photodetector/bin/activate

# Installing wheel first helps install certain packages (e.g., backcall)
echo Installing wheel by pip first...
pip3 install wheel

# Install support packages
echo Installing required pip packages...
if [ ${#pkgs[@]} -ne 0 ]; then
    pip3 install ${pkgs[@]}
fi

# Install dev package
echo Installing $devenv...
pip install -e .

echo End: set up Python environment.
