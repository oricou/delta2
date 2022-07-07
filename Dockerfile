FROM python:3.9.13-slim-buster

RUN apt-get update                                              \
   && RUNLEVEL=1 DEBIAN_FRONTEND=noninteractive                 \
     apt-get install -y --no-install-recommends     \
        g++                                                     \
        git                                                     \
        vim                                                     \
        openssh-client                                          \
        imagemagick                                             \
        ffmpeg                                                  \
        libx264-dev                                             \
        libzmq3-dev                                             \
        libxml2-dev                                             \
        libxslt-dev                                             \
        zlib1g-dev                                              \
        liblapack-dev                                           \
        gfortran                                                \
        locales                                                 \
        procps                                                  \
        make                                                    \
  && apt-get autoremove                                         \
  && apt-get clean                                              \
  && echo "fr_FR.UTF-8 UTF-8" > /etc/locale.gen                 \
  && locale-gen

ENV LANG=fr_FR.UTF-8 \
    LANGUAGE=fr_FR:fr \
    LC_ALL=fr_FR.UTF-8


# Create a working directory.
RUN mkdir delta
WORKDIR delta

# Install Python dependencies.
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the rest of the codebase into the image
ADD apps.tgz .

# Finally, run gunicorn.
CMD [ "gunicorn", "--timeout=300", "--workers=5", "--threads=1", "-b 0.0.0.0:8000", "delta:server"]

