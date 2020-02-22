FROM archlinux/base:latest
RUN pacman -Syu --noconfirm && \
    pacman -S --noconfirm gcc python3 python-pip && \
    rm -rf /var/cache/pacman/pkg/ && \
    rm /bin/sh && ln -s /bin/bash /bin/sh && \
    useradd user --home /home/user/ --create-home --shell /bin/bash --uid 994
USER user
WORKDIR "/home/user/"
RUN mkdir -p venv && \
    python3 -m venv venv/ --system-site-packages && \
    venv/bin/pip3 install --upgrade pip --no-cache-dir && \
    venv/bin/pip3 install --no-cache-dir \
        numpy \
        pandas \
        sqlalchemy \
        alembic \
        Pillow \
        plotly \
        telepot \
        yfinance \
        alpha_vantage