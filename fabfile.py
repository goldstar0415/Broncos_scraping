import os
import tempfile
import yaml
from colors import green

from fabric.api import get, execute, put, roles
from fabric.context_managers import cd
from fabric.decorators import task
from fabric.operations import run
from fabric.state import env
from fabric.contrib import files

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = {
    "name": "Parsers for social networks",

    "build_server": "34.212.65.19",
    "repo_url": "git@gitlab.com:ingenix/hashtag-parsing/parsing.git",
    "app_path": "~/parsing",
    "app_branch": "master",

    "docker_image": "registry.gitlab.com/ingenix/hashtag-parsing/parsing",
    "image_type": "prod",
    "image_version": "latest",

    "deploy_server": "34.209.224.107",
    "compose_path": "/opt/servers",
    "compose_block_name": "parsing-parser"
}


env.user = "deployer"
env.hosts = ["34.212.65.19"]
env.forward_agent = False

env.roledefs = {
    'build': [],
    'deploy': []
}


@task
def deploy():
    """
    Make full step-by-step deploy

    :param config: Configuration dict, loaded by slug
    :return: Nothing, if deploy passed
    :raises: Various exceptions, if something went wrong during deploy
    """
    env.roledefs['build'] = [config["build_server"]]
    env.roledefs['deploy'] = [config["deploy_server"]]
    execute(get_code, config)
    execute(build_container, config)
    execute(push_container, config)
    execute(update_compose, config)
    execute(reload_docker, config)

    if config.get('post_deploy'):
        execute(post_deploy, config)

    print(green("""
    SUCCESS
    """))
    print("""{docker_image}:{image_type}-{image_version} ready
    """.format(**config))


@roles('build')
@task
def get_code(config):
    """
    Pulls update from remote repository

    :param config: Configuration dict
    :return: Nothing, if process passed
    """
    if files.exists(config["app_path"]):
        # Update buld repo
        with cd(config["app_path"]):
            run("git checkout {}".format(config["app_branch"]))
            run("git pull origin {}".format(config["app_branch"]))
            config["image_version"] = run("git rev-parse --short {}".format(config["app_branch"]))
    else:
        raise Exception("App repo not found")


@roles('build')
@task
def build_container(config):
    """
    Builds docker image

    :param config: Configuration dict
    :return: Nothing, if process passed
    """
    if files.exists(config["app_path"]):
        # Update buld repo
        with cd(config["app_path"]):
            command = "docker build --build-arg version={image_type} -t {docker_image}:{image_type}-{image_version} ."
            run(command.format(**config))


@roles('build')
@task
def push_container(config):
    """
    Pushes docker image to gitlab

    :param config: Configuration dict
    :return: Nothing, if process passed
    """
    if files.exists(config["app_path"]):
        # Update buld repo
        with cd(config["app_path"]):
            command = "docker push {docker_image}:{image_type}-{image_version}"
            run(command.format(**config))


@roles('deploy')
@task
def update_compose(config):
    filename = os.path.join(config['compose_path'], "docker-compose.yml")
    image = "{docker_image}:{image_type}-{image_version}".format(**config)

    with tempfile.TemporaryFile() as fd:
        get(filename, fd)
        fd.seek(0)
        data = yaml.load(fd.read())
        data['services'][config['compose_block_name']]['image'] = image
        fd.seek(0)
        fd.truncate()
        fd.write(yaml.dump(data).encode('utf-8'))
        fd.flush()
        put(fd, filename)


@roles('deploy')
@task
def reload_docker(config):
    with cd(config["compose_path"]):
        run('docker-compose up -d')


@roles('deploy')
@task
def post_deploy(config):
    with cd(config["compose_path"]):
        run(config["post_deploy"])
