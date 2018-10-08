# pybofh documentation


## Requiements

See 'requirements.txt' for requirements on building the documentation.
TODO: Include requirements in setup.py


## How to build

```
make html
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

* Generic documentation goes in `source/`
* Each module should have a matching document in
  `source/modules/bofh[.module[.submodule]].rst`.
