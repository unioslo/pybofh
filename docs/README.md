# bofh documentation


## Requiements

See 'requirements.txt' for requirements on building the documentation.

It's advisable to build the documentation in a virtualenv:

```bash
python -m venv /path/to/bofh-docs
source /path/to/bofh-docs/bin/activate
pip install -r requirements.txt
```


## How to build

```bash
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
