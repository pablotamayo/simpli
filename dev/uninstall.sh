#!/usr/bin/env bash

pip uninstall simpli -y

jupyter nbextension uninstall --py --sys-prefix simpli
jupyter nbextension disable --py --sys-prefix simpli
jupyter serverextension disable --py --sys-prefix simpli

rm -rf ~/.jupyter/
