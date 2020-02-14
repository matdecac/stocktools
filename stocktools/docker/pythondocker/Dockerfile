FROM archlinux:latest
RUN pacman -Syu --noconfirm && pacman -S npm python python-pip gcc --noconfirm && rm -rf /usr/local/var/cache/pacman
RUN useradd user --home /home/user/ --create-home --shell /bin/bash --uid 994
USER user
WORKDIR "/home/user/"
COPY requirements.txt requirements.txt
RUN mkdir -p venv
RUN python3 -m venv venv/ --system-site-packages
RUN source venv/bin/activate
RUN source venv/bin/activate && pip3 install -r requirements.txt --no-cache-dir
# Avoid "JavaScript heap out of memory" errors during extension installation
RUN source venv/bin/activate && export NODE_OPTIONS=--max-old-space-size=4096
# Jupyter widgets extension
RUN source venv/bin/activate && jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.1 --no-build
# FigureWidget support
RUN source venv/bin/activate && jupyter labextension install plotlywidget@1.5.0 --no-build
# and jupyterlab renderer support
RUN source venv/bin/activate && jupyter labextension install jupyterlab-plotly@1.5.0 --no-build
# Build extensions (must be done to activate extensions since --no-build is used above)
#RUN source venv/bin/activate && jupyter lab build
# Unset NODE_OPTIONS environment variable
RUN source venv/bin/activate && unset NODE_OPTIONS
