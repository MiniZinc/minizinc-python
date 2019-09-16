FROM minizinc/minizinc:latest AS minizinc

FROM ubuntu:latest AS pyenv

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update; \
  apt-get install -yq --no-install-recommends make build-essential libssl-dev \
  zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
  libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev \
  liblzma-dev ca-certificates git

RUN curl https://pyenv.run | bash

ENV PYENV_ROOT /root/.pyenv
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"
RUN pyenv install 3.7.4; \
    pyenv install 3.6.9; \
    pyenv install pypy3.6-7.1.1; \
    pyenv global 3.7.4 3.6.9 pypy3.6-7.1.1

FROM ubuntu:latest

COPY --from=minizinc /usr/local/ /usr/local/
COPY --from=pyenv /root/.pyenv/versions/ /python/

RUN apt-get update && \
    apt-get install -y libssl1.1 && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/python/3.7.4/bin:/python/3.6.9/bin:/python/pypy3.6-7.1.1/bin:${PATH}"


