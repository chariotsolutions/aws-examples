.PHONY: default build upload deploy clean

BUCKET		?= must_be_provided
KEY		?= lambda_four_ways/python/lambda.zip
LAMBDA_NAME     ?= LambdaFourWays

BUILD_DIR       := $(PWD)/build
ARTIFACT        := lambda.zip

default: package

deploy: build
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(BUILD_DIR)/$(ARTIFACT)

upload: build
	aws s3 cp ${BUILD_DIR}/${ARTIFACT} s3://${BUCKET}/${KEY}

build: init
	zip ${BUILD_DIR}/${ARTIFACT} lambda.py

init:
	mkdir -p ${BUILD_DIR}

clean:
	rm -rf ${BUILD_DIR}
