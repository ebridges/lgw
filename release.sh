#!/bin/sh

VERSION=${1}

if [ -z "${VERSION}" ];
then
    echo "Usage: $0 [VERSION]"
    exit 1
fi

echo "Releasing version ${VERSION}."
read -n1 -rsp $'Click any key to continue or Ctrl+C to exit...\n' key

if [ "$key" = '' ]; then

  git flow release start ${VERSION}

  result=`emacs pyproject.toml lgw/version.py`

  if [ ${result} ];
  then
    echo 'Error bumping version, aborting.'
  fi

  git add pyproject.toml lgw/version.py
  git commit --gpg-sign --message 'bump version'

  dephell deps convert

  pypi_username=$(cat ~/.pypirc | grep username | awk '{ print $3 }')
  pypi_password=$(cat ~/.pypirc | grep password | awk '{ print $3 }')
  poetry publish --build --username="${pypi_username}" --password="${pypi_password}"

  git flow release finish ${VERSION}

else
    echo 'Release cancelled.'
    exit 1
fi
