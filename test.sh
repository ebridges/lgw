#!/usr/local/bin/bash

export AWS_ACCESS_KEY_ID=''
export AWS_SECRET_ACCESS_KEY=''
export AWS_DEFAULT_REGION='us-east-1'

CMD=$1

echo "CMD: ${CMD}"

if [ "${CMD}" = 'lambda-deploy' ];
then
  lgw lambda-deploy \
    --verbose \
    --config-file=./test.env \
    --lambda-file=tests/lambda/app.zip
fi


if [ "${CMD}" = 'lambda-invoke' ];
then
  lgw lambda-invoke \
    --lambda-name=test_lambda
fi


if [ "${CMD}" = 'lambda-delete' ];
then
  lgw lambda-delete \
    --lambda-name=test_lambda
fi


if [ "${CMD}" = 'lgw-deploy' ];
then
  lgw lgw-deploy --config-file=./test.env
fi
