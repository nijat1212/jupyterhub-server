FROM jupyterhub/jupyterhub:latest
RUN /srv/venv/bin/pip install --no-cache-dir dockerspawner jupyterhub-firstuseauthenticator bcrypt jupyterhub-idle-culler
