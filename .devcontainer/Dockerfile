FROM odoo:17.0


# Install some deps
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git


# Install some pip deps
COPY ./requirements.txt /tmp/
COPY ./requirements_dev.txt /tmp/

RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements_dev.txt


# create a dev user
RUN useradd -m -d /home/vscode -s /bin/bash vscode

USER vscode
WORKDIR /home/vscode
