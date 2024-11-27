FROM odoo:17.0


# Install some deps
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        sudo

# Install some pip deps
COPY ./requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

# create a dev user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m -s /bin/bash $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# switch back to the odoo user
USER odoo
