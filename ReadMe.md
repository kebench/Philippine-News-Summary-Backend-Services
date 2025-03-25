# Philippine New Summary Backend Services
This is a monorepo that contains the backend services needed by Philippine New Summary website.

## Services

### Crawler Cron
A docker image that contains crawler for specific news URLs for data.

> [!NOTE]
> Run this in PowerShell!

To build: 
```
docker buildx build --platform linux/amd64 --provenance=false -t crawler-cron . 
```

Before running the docker image, download the runtime interface emulator and install it in the local  machine. Please follow the instuctions on this link [this link](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions).

To run:
```
docker run --platform linux/amd64 -d -v "$HOME\.aws-lambda-rie:/aws-lambda" -p 9000:8080 `--entrypoint /aws-lambda/aws-lambda-rie `crawler-cron `    /usr/local/bin/python -m awslambdaric lambda_function.lambda_handler
```
