#!/bin/sh
# FOR LOCAL TESTING IN DOCKER: Use aws-lambda-rie to emulate Lambda runtime
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    # Local — use RIE to emulate Lambda runtime
    echo "[entrypoint] Running in LOCAL mode (using aws-lambda-rie)"
    exec /usr/local/bin/aws-lambda-rie /usr/local/bin/python -m awslambdaric "$@"
else
    echo "[entrypoint] Running in AWS LAMBDA mode"
    # AWS Lambda — use awslambdaric directly
    exec /usr/local/bin/python -m awslambdaric "$@"
fi