FROM pythonstock:latest
WORKDIR "/home/user/"
USER root
RUN /venv/bin/pip3 install --no-cache-dir \
        jupyterlab==1.2 \
        ipywidgets==7.5
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y npm && \
    rm -rf /var/lib/apt/lists/*
RUN export NODE_OPTIONS=--max-old-space-size=4096 && \
    /venv/bin/jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build && \
    /venv/bin/jupyter labextension install plotlywidget@1.5.4 --no-build && \
    /venv/bin/jupyter labextension install jupyterlab-plotly@1.5.4 --no-build && \
    /venv/bin/jupyter lab build && \
    unset NODE_OPTIONS
USER user
