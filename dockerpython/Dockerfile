FROM ubuntu:rolling
RUN apt-get update && \ 
    apt-get upgrade -y && \
    apt-get install -y gcc python3 python-pip python3-venv && \
    rm -rf /var/lib/apt/lists/* && \
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
        alpha_vantage \
        yahoo_fin \
        requests_html
