# bofh documentation

## Requiements

Documentation build requirements are listed in the package *dev* extras.  It's
advisable to install these requirements to a virtualenv:

```bash
python -m venv /path/to/bofh-docs
source /path/to/bofh-docs/bin/activate
cd /path/to/bofh-src
pip install -e .[doc]
```


## How to build

There is a simplified Sphinx Makefile under ``docs/``. Use this to build the
docs:

```bash
cd /path/to/bofh-src/docs/

# Build html documentation
make html

# Build manpage
make man
```


### Build PDFs on Fedora

```
dnf install \
    texlive-collection-fontsrecommended \
    texlive-collection-latexrecommended \
    texlive-collection-latexextra \
    latexmk
make latexpdf
```


## Structure

- Generic documentation goes in `source/`
- Each module should have a matching document in
  `source/modules/bofh[.module[.submodule]].rst`
