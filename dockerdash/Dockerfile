FROM pythonstock:latest
USER root
RUN source /venv/bin/activate && pip3 install --no-cache-dir \
        dash \
        dash-bootstrap-components \
        gunicorn
USER user
