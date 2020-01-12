ARG BASE=python:latest
FROM minizinc/minizinc:latest AS minizinc

FROM ${BASE}

COPY --from=minizinc /usr/local/ /usr/local/
