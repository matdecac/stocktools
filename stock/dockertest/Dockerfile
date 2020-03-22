FROM ubuntu:rolling
RUN apt-get update && \ 
    apt-get upgrade -y && \
    apt-get install -y gcc python3 python-pip python3-venv npm && \
    rm -rf /var/lib/apt/lists/* && \
    rm /bin/sh && ln -s /bin/bash /bin/sh && \
    useradd user --home /home/user/ --create-home --shell /bin/bash --uid 994
USER user
WORKDIR "/home/user/"
RUN mkdir -p venv && \
    python3 -m venv venv/ && \
    venv/bin/pip3 install --upgrade pip --no-cache-dir && \
    venv/bin/pip3 install --no-cache-dir \
        numpy \
        pandas \
        jupyterlab==1.2 \
        "ipywidgets==7.5" \
        plotly==4.5.1
#RUN export NODE_OPTIONS=--max-old-space-size=4096 && \
#    venv/bin/jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build && \
#    venv/bin/jupyter labextension install plotlywidget@1.5.1 --no-build && \
#    venv/bin/jupyter labextension install jupyterlab-plotly@1.5.1 --no-build && \
#    venv/bin/jupyter lab build && \
#    unset NODE_OPTIONS

