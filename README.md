# compas_occt

Windows, Mac, Linux Nanobind wrapper for OCCT

![Screenshot 2025-05-23 184722](https://github.com/user-attachments/assets/1cc9662e-5de9-4f58-97f7-13ce489eed1a)


## Installation

Stable releases can be installed from PyPI.

```bash
pip install compas_occt
```

To install the latest version for development, do:

```bash
git clone https://github.com//compas_occt.git
cd compas_occt
pip install -e ".[dev]"
```

If you are a software developer, and this is your own package, then it is usually much more efficient to install the build dependencies in your environment once and use the following command that avoids a costly creation of a new virtual environment at every compilation:

```bash
pip install --no-build-isolation -ve .
cibuildwheel --output-dir wheelhouse .
```

## Documentation

For further "getting started" instructions, a tutorial, examples, and an API reference,
please check out the online documentation here: [compas_occt docs](https://.github.io/compas_occt)

## Issue Tracker

If you find a bug or if you have a problem with running the code, please file an issue on the [Issue Tracker](https://github.com//compas_occt/issues).
