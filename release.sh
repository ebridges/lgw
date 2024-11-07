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

  if [ $? -ne 0 ]; then
    echo "Error running git flow release start ${VERSION}"
    exit 1
  fi

  result=`emacs pyproject.toml lgw/version.py tests/test_lgw.py`

  if [ ${result} ];
  then
    echo 'Error bumping version, aborting.'
    exit 1
  fi

  git add pyproject.toml lgw/version.py tests/test_lgw.py
  if [ $? -ne 0 ]; then
    echo "Error adding pyproject.toml, lgw/version.py and tests/test_lgw.py"
    exit 1
  fi

  git commit --gpg-sign --message 'bump version'
  if [ $? -ne 0 ]; then
    echo "Error committing"
    exit 1
  fi

  pypi_username=$(cat ~/.pypirc | grep username | awk '{ print $3 }')
  pypi_password=$(cat ~/.pypirc | grep password | awk '{ print $3 }')
  poetry publish --build --username="${pypi_username}" --password="${pypi_password}"

  git flow release finish ${VERSION}

else
    echo 'Release cancelled.'
    exit 1
fi
