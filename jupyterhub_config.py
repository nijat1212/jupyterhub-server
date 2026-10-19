import os

c = get_config()

# Сетевые параметры
c.JupyterHub.bind_url = 'http://127.0.0.1:8000'
c.JupyterHub.hub_bind_url = 'http://0.0.0.0:8081'
c.JupyterHub.hub_ip = '172.17.0.1'
c.JupyterHub.hub_port = 8081
c.JupyterHub.db_url = 'sqlite:////data/jupyterhub.sqlite'
c.JupyterHub.trusted_downstream_ips = ['127.0.0.1']

# Аутентификация
c.JupyterHub.authenticator_class = 'firstuseauthenticator.FirstUseAuthenticator'
c.Authenticator.admin_users = {'admin'}
c.Authenticator.allow_all = False

# DockerSpawner
c.JupyterHub.spawner_class = 'dockerspawner.DockerSpawner'
c.DockerSpawner.image = 'jupyter/minimal-notebook:latest'
c.DockerSpawner.name_template = 'jupyter-{username}'
c.DockerSpawner.network_name = 'jupyterhub-network'
c.DockerSpawner.remove = True
c.Spawner.default_url = '/lab'
c.Spawner.start_timeout = 300

# Лимиты ресурсов
c.Spawner.mem_limit = '512M'
c.Spawner.mem_guarantee = '256M'
c.Spawner.cpu_limit = 0.5
c.Spawner.cpu_guarantee = 0.2

# Монтирование пользовательских данных
c.DockerSpawner.volumes = {
    '/opt/jupyterhub/data/{username}': '/home/jovyan/work'
}

def create_dir_hook(spawner):
    username = spawner.user.name
    volume_path = os.path.join('/opt/jupyterhub/data', username)
    if not os.path.exists(volume_path):
        os.makedirs(volume_path, mode=0o777, exist_ok=True)
    os.chmod(volume_path, 0o777)

c.Spawner.pre_spawn_hook = create_dir_hook

c.DockerSpawner.allowed_images = {
    '📊 Data Science (Pandas, NumPy, Matplotlib, Seaborn, Excel)': 'custom-datascience-notebook:latest',
    '🐍 Чистый Python (Minimal Notebook)': 'jupyter/minimal-notebook:latest'
}

import sys

# Автоматическое усыпление неактивных серверов (через 1 час простоя)
c.JupyterHub.services = [
    {
        'name': 'idle-culler',
        'command': [
            sys.executable,
            '-m', 'jupyterhub_idle_culler',
            '--timeout=3600',
            '--cull-every=600',
        ],
    }
]

c.JupyterHub.load_roles = [
    {
        'name': 'idle-culler',
        'scopes': ['list:users', 'read:users:name', 'read:users:activity', 'servers'],
        'services': ['idle-culler'],
    }
]
