import docker
from io import BytesIO
import json
import ast
import tarfile
import os
import tempfile
from os.path import exists

from logging import debug, info, warn, error, getLogger, DEBUG

DOCKER_SOCKET_FILE = '/var/run/docker.sock'
DEFAULT_CODE_HOME = '/home/code/'
DEFAULT_VENV_HOME = '/home/venv/'
DEFAULT_OUTPUT_DIR = '/home/build/'
DEFAULT_PACKAGES = ['gcc', 'openssl-devel', 'bzip2-devel', 'libffi-devel', 'python37-pip']

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
    addl_yum_packages=[],
):
    if not exists(DOCKER_SOCKET_FILE):
        error(f'Docker listen socket not found at {DOCKER_SOCKET_FILE}')
        raise FileNotFoundError(
            f'Docker listen socket not found at {DOCKER_SOCKET_FILE}, is Docker running?'
        )

    info('Assembling Dockerfile.')
    dockerfile = create_dockerfile(lambda_archive_filename, addl_project_files, addl_yum_packages)
    debug(dockerfile)

    tag = 'lambda-bundle:latest'

    info(f'Building docker image based on files in {context_dir}')
    with tempfile.NamedTemporaryFile() as tmp:
        docker_context_file = create_docker_context(dockerfile, context_dir, tmp.name)
        cli = docker.APIClient(base_url=f'unix://{DOCKER_SOCKET_FILE}')
        for line in cli.build(fileobj=tmp, custom_context=True, encoding='gzip', tag=tag):
            print_progress(line)

    info('Running docker image to build lambda archive.')
    client = docker.from_env()
    container = client.containers.run(tag, command=f'/bin/sh', detach=True)

    info('Extracting lambda archive from running container.')
    bits, stat = container.get_archive(f'{DEFAULT_OUTPUT_DIR}/{lambda_archive_filename}')
    location = write_file_from_tar(bits, lambda_archive_dir, lambda_archive_filename)

    container.stop()

    return location


def create_dockerfile(archive_filename, addl_project_files, addl_yum_packages):
    yum_packages = ' '.join(set(DEFAULT_PACKAGES + addl_yum_packages))
    addl_files = ''
    for files in addl_project_files:
        addl_files += 'COPY %s %s\n' % files

    dockerfile = f'''
FROM lambci/lambda:build-python3.7 AS base

RUN yum makecache fast

RUN yum clean all && \
  yum update --assumeyes && \
  yum upgrade --assumeyes

RUN yum install  --assumeyes \
  {yum_packages}

ARG wkdir={DEFAULT_CODE_HOME}
RUN mkdir -p $wkdir

ARG venv={DEFAULT_VENV_HOME}
RUN mkdir -p $venv

ARG output={DEFAULT_OUTPUT_DIR}
RUN mkdir -p $output

WORKDIR $wkdir

{addl_files}

RUN python3 -m venv $venv
RUN source $venv/bin/activate && \
    pip3 install -U pip && \
    pip3 install -r requirements.txt

RUN echo "source $venv/bin/activate" > $HOME/.profile

RUN cd $wkdir && \
    zip -9 -r \
    $output/{archive_filename} . \
    --exclude '*/bin' '*dist-info*' '*__pycache__*' \
        '*.pyc' '*easy_install.py*' '*pip/*' \
            '*setuptools/*' '*pkg_resources/*'

RUN cd $venv/lib/python3.7/site-packages && \
    zip -9 -r -u \
    $output/{archive_filename} . \
    --exclude '*/bin' '*dist-info*' '*__pycache__*' \
        '*.pyc' '*easy_install.py*' '*pip/*' \
            '*setuptools/*' '*pkg_resources/*'

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

    return context_file


def print_progress(line):
    s = line.decode('utf8')
    if s:
        for l in s.split('\r\n'):
            if l.strip():
                try:
                    dd = ast.literal_eval(l.strip())
                except:
                    warn(l)
                else:
                    if 'stream' in dd:
                        ss = dd['stream']
                        if ss:
                            debug(ss.strip())
                    if 'error' in dd:
                        ee = dd['error']
                        if ee:
                            error(ee.strip())
