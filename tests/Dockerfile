FROM minizinc/minizinc:latest-alpine AS minizinc

FROM alpine:latest AS pyenv

RUN apk add --no-cache bash curl git
RUN curl https://pyenv.run | bash

FROM alpine:latest

RUN apk add --no-cache bzip2-dev coreutils dpkg-dev dpkg expat-dev \
  findutils gcc gdbm-dev libc-dev libffi-dev libnsl-dev libtirpc-dev \
  linux-headers make ncurses-dev openssl-dev pax-utils readline-dev \
  sqlite-dev tcl-dev tk tk-dev util-linux-dev xz-dev zlib-dev bash \
  libstdc++

COPY --from=minizinc /usr/local/ /usr/local/

COPY --from=pyenv /root/.pyenv /pyenv
ENV PYENV_ROOT /pyenv
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}"
RUN pyenv install 3.6.9; pyenv install 3.7.4; pyenv global 3.7.4 3.6.9
