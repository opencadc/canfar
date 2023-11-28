# CANFAR Science Platform User Containers

This repository ([science-containers.git](https://github.com/opencadc/science-containers.git)) includes build recipes for containers to be launched on the CANFAR science-platform. 
Please feel free to contribute.

## CANFAR-maintained Containers
Curently the repository contains basic build system to build a hierarchy of default containers supported by CANFAR:

``` py
	                    Ubuntu LTS
	                    	|
		            base (headless)
	                    	|
		_____________________ _ _ _ _ _ _ _
		|                                  | 
astroml (headless)			Desktop Application (desktop-app)
		|
astroml-notebook (notebook) 
astroml-vscode   (contributed)
astroml-desktop  (desktop-app)
```

- The `base` is a `headless` container are built from a vanilla Ubuntu LTS, with extra operating system installed (compilers, development libraries), and conda install.
- The `astroml` is another `headless` container and is built with a large set of astronomy, machine learning, deep learning, visualisations and data science libraries. 
- The `astroml-*` add visualisation and interactivity software. They can be launched as a `notebook` session, a `contributed` VSCode session, or a terminal through a `desktop` session.
- The `Desktop Application` containers do not typically derive from `astroml` and sometimes not from `base` containers, as they are legacy and may rely on now unsupported OS.

There are CUDA-enabled versions of the containers, which include NVIDIA software and CUDA-powered libraries. They are built and named as `*-gpu`, i.e. `astroml-gpu`, `astroml-gpu-notebook`.

## CANFAR User Customised Container
If you want to build your own containers, documentation can be found in the [docs directory](docs).
This directory also contains the building of the [CANFAR usage documentation](https://canfar-scienceportal.readthedocs.io/en/latest/) in the readthedocs style.

## TODO

# Laundry list for possible actions

- write a Makefile allowing: `make build astroml`
- install jupyterlab extensions in home directory rather than /opt/conda
- configure jupyterlab containers to automatically creating directories  somewhere less intrusive than just `$HOME`:
 `migrated astropy matplotlib yarn lab pip fontconfig serverconfig jedi numba`
- launcher in jupyterlab has too many launching and confusing icons
- make a button on jupyterlab that will create a new environment automatically and create an icon
- build npm apps on container directories to avoid populating million of useless files
- environments in home directory with pip by default
- add other alternative notebooks such as querybook, cocalc, nteract_on_jupyter

![CANFAR](https://www.canfar.net/css/images/logo.png){ height="200" }
