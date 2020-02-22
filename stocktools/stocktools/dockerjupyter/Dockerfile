FROM pythonstock:latest
WORKDIR "/home/user/"
RUN venv/bin/pip3 install --no-cache-dir \
        jupyterlab \
        ipywidgets

# USER root
# RUN pacman -Syu --noconfirm && \
#     pacman -S --noconfirm npm && \
#     rm -rf /var/cache/pacman/pkg/
# USER user
# RUN export NODE_OPTIONS=--max-old-space-size=4096 && \
#     venv/bin/jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build && \
#     venv/bin/jupyter labextension install plotlywidget@1.5.1 --no-build && \
#     venv/bin/jupyter labextension install jupyterlab-plotly@1.5.1 --no-build && \
#     venv/bin/jupyter lab build && \
#     unset NODE_OPTIONS
