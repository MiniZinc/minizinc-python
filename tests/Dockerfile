FROM minizinc/minizinc:latest-alpine AS minizinc

FROM alpine:latest AS pyenv

RUN apk add --no-cache bash curl git bzip2-dev coreutils dpkg-dev dpkg \
  findutils gcc gdbm-dev libc-dev libffi-dev libnsl-dev libtirpc-dev \
  linux-headers make ncurses-dev openssl-dev pax-utils readline-dev \
  sqlite-dev tcl-dev tk tk-dev util-linux-dev xz-dev zlib-dev expat-dev

RUN curl https://pyenv.run | bash

ENV PYENV_ROOT /root/.pyenv
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"
RUN pyenv install 3.6.9; pyenv install 3.7.4; pyenv global 3.7.4 3.6.9

FROM alpine:latest

RUN apk add --no-cache expat gdbm libbz2 libcrypto1.1 libffi libssl1.1 \
  musl ncurses-libs readline sqlite-libs xz-libs zlib libstdc++

COPY --from=minizinc /usr/local/ /usr/local/
COPY --from=pyenv /root/.pyenv/versions/ /python/

ENV PATH="/python/3.7.4/bin:/python/3.6.9/bin:${PATH}"


