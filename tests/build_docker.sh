#!/bin/bash

BASES=("python:latest" "python:3.7" "python:3.6" "pypy:latest")
EXTS=("latest" "py37" "py36" "pypy")

green=`tput setaf 2`
reset=`tput sgr0`

for i in {0..3}
do
  echo "${green}Build with base ${BASES[$i]} and create registry.gitlab.com/minizinc/minizinc-python:${EXTS[$i]}${reset}"
  docker build --build-arg BASE=${BASES[$i]} -t registry.gitlab.com/minizinc/minizinc-python:${EXTS[$i]} .
  docker push registry.gitlab.com/minizinc/minizinc-python:${EXTS[$i]}
done
