.PHONY: default build upload deploy clean

BUCKET		?= must_be_provided
KEY		?= lambda_four_ways/javascript/lambda.zip
LAMBDA_NAME     ?= LambdaFourWays

ARTIFACT        := lambda.zip
LIB_DIR		:= node_modules/

default: build

deploy: build
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(ARTIFACT)

upload: build
	aws s3 cp ${ARTIFACT} s3://${BUCKET}/${KEY}

build: init
	zip -q -r ${ARTIFACT} lambda.mjs node_modules

init:
	npm install

clean:
	rm -rf ${ARTIFACT}
	rm -rf ${LIB_DIR}
