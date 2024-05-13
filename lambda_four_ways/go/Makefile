.PHONY: default build upload deploy clean

BUCKET          ?= must_be_provided
KEY             ?= lambda_four_ways/go/lambda.zip
LAMBDA_NAME     ?= LambdaFourWays

ARTIFACT        := lambda.zip

default: package

deploy: lambda.zip
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(ARTIFACT)

upload: lambda.zip
	aws s3 cp ${ARTIFACT} s3://${BUCKET}/${KEY}

lambda.zip: init lambda.go
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -o bootstrap -tags lambda.norpc .
	zip $(ARTIFACT) bootstrap 

init:
	go get

clean:
	;
