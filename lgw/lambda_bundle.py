import docker
from io import BytesIO
import json
import ast
import tarfile
import os
import tempfile
from os.path import exists

from logging import debug, info, warning, error, getLogger, DEBUG

PYTHON_VERSION = '3.12'
ARCH = '-arm64'
BASE_IMAGE = f'public.ecr.aws/shogo82148/lambda-python:build-{PYTHON_VERSION}.2024.10.18{ARCH}'
DOCKER_SOCKET_FILE = '/var/run/docker.sock'
DEFAULT_CODE_HOME = '/home/code/'
DEFAULT_VENV_HOME = '/home/venv/'
DEFAULT_OUTPUT_DIR = '/home/build/'
DEFAULT_PACKAGES = ['python-pip']
LAMBDA_BUNDLE_ZIP = 'lambda-bundle.zip'
ZIP_EXCLUDES = [
    '*/bin',
    '*dist-info*',
    '*__pycache__*',
    '*.pyc',
    '*easy_install.py*',
    '*pip/*',
    '*setuptools/*',
    '*pkg_resources/*',
]

DEFAULT_DOCKERIGNORE = [
    '**/.DS_Store',
    '.git/',
    '.gitignore',
    '.vscode/',
    '.idea/',
    '.gradle/',
    '.settings/',
    '**/*.pyc',
    '**/__pycache__/',
    '**/db.sqlite3',
    '*.sublime-project',
    '*.sublime-workspace',
    '*.retry',
    'vue-s3-dropzone/',
    '.pytest_cache/',
]


def build_lambda_archive(
    context_dir,
    lambda_archive_dir,
    lambda_archive_filename,
    addl_project_files=[],
    addl_system_packages=[],
):
    if not exists(DOCKER_SOCKET_FILE):
        error(f'Docker listen socket not found at {DOCKER_SOCKET_FILE}')
        raise FileNotFoundError(
            f'Docker listen socket not found at {DOCKER_SOCKET_FILE}, is Docker running?'
        )

    info('Assembling Dockerfile.')
    dockerfile = create_dockerfile(
        lambda_archive_filename, addl_project_files, addl_system_packages
    )
    debug(dockerfile)

    tag = 'lambda-bundle:latest'

    info(f'Building docker image based on files in {context_dir}')
    with tempfile.NamedTemporaryFile() as tmp:
        create_docker_context(dockerfile, context_dir, tmp.name)
        cli = docker.APIClient(base_url=f'unix://{DOCKER_SOCKET_FILE}')
        for line in cli.build(fileobj=tmp, custom_context=True, encoding='gzip', tag=tag):
            print_progress(line)

    info('Running docker image to build lambda archive.')
    client = docker.from_env()
    container = client.containers.run(tag, command='/bin/sh', detach=True)

    info('Extracting lambda archive from running container.')
    bits, _ = container.get_archive(f'{DEFAULT_OUTPUT_DIR}/{lambda_archive_filename}')
    location = write_file_from_tar(bits, lambda_archive_dir, lambda_archive_filename)

    container.stop()

    return location


def create_dockerfile(archive_filename, addl_project_files, addl_system_packages):
    sys_packages = ' '.join(set(DEFAULT_PACKAGES + addl_system_packages))
    zip_excludes = ' '.join(set(ZIP_EXCLUDES))
    addl_files = ''
    for files in addl_project_files:
        # addl_project_files is a list of tuples
        addl_files += 'COPY %s %s' % files

    dockerfile = f'''FROM {BASE_IMAGE} AS base
# Switch to root user to perform installations
USER root
# Set ARGs for directories
ARG wkdir={DEFAULT_CODE_HOME}
ARG venv={DEFAULT_VENV_HOME}
ARG output={DEFAULT_OUTPUT_DIR}
# Install system dependencies
RUN microdnf install -y \
    {sys_packages}
# Create working directories & change to working dir
RUN mkdir -p $wkdir $venv $output
WORKDIR $wkdir
{addl_files}
# Set up virtual environment and install dependencies
COPY requirements.txt ./
RUN python3 -m venv $venv && \
 source $venv/bin/activate && \
 pip install -U pip && \
 pip install -r requirements.txt && \
 deactivate
# Activate virtual env on login
RUN echo "source $venv/bin/activate" >> $HOME/.profile
# Package the code and dependencies into the output zip in one RUN command
RUN cd $wkdir && \
zip -9 -r $output/{archive_filename} . \
 --exclude {zip_excludes} && \
cd $venv/lib/python{PYTHON_VERSION}/site-packages && \
zip -9 -r -u $output/{archive_filename} . \
 --exclude {zip_excludes}
'''

    return dockerfile


def write_file_from_tar(data, dest, archive_filename):
    '''
    Extracts a single file named `archive_filename` from a tar
    file encoded in the stream `data` to the given location `dest`.
    Returns the new location of the extracted file.
    '''
    with tempfile.NamedTemporaryFile() as temp:
        for chunk in data:
            temp.write(chunk)
        temp.flush()
        os.fsync(temp)
        with tarfile.open(name=temp.name) as tf:

            logger = getLogger(__name__)
            if logger.isEnabledFor(DEBUG):
                for tinfo in tf.getnames():
                    debug(f'>    {tinfo}')

            tf.extract(archive_filename, path=dest)
    return f'{dest}/{archive_filename}'


def create_docker_context(dockerfile, context_directory, context_file):
    '''
    Collects the `context_directory` into a tar file
    along with the given `dockerfile`.
    Returns the filename containing the given context.
    '''

    def tar_exclude_filter(ti):
        for item in DEFAULT_DOCKERIGNORE:
            if item in ti.name:
                return None
        return ti

    with tarfile.open(context_file, 'w:gz') as tar:
        tar.add(
            context_directory,
            arcname=os.path.basename(context_directory),
            filter=tar_exclude_filter,
        )
        dockerfile_bytes = dockerfile.encode('utf8')
        info = tarfile.TarInfo(name='Dockerfile')
        info.size = len(dockerfile_bytes)
        tar.addfile(info, BytesIO(dockerfile_bytes))

        logger = getLogger(__name__)
        if logger.isEnabledFor(DEBUG):
            for tinfo in tar.getnames():
                debug(f'>    {tinfo}')


def print_progress(line):
    s = line.decode('utf8')
    if s:
        for l in s.split('\r\n'):
            if l.strip():
                try:
                    dd = ast.literal_eval(l.strip())
                except Exception:
                    warning(l)
                else:
                    if 'stream' in dd:
                        ss = dd['stream']
                        if ss:
                            debug(ss.strip())
                    if 'error' in dd:
                        ee = dd['error']
                        if ee:
                            error(ee.strip())
