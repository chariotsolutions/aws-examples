.PHONY: default deploy package test init clean

LAMBDA_NAME     ?= Example

DEPLOY_DIR      ?= /tmp/deploy
ARTIFACT        ?= example.zip

SRC_DIR         := /build/src
LIB_DIR         := /tmp/lib

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(DEPLOY_DIR)/$(ARTIFACT)

package: test
	mkdir -p ${DEPLOY_DIR}
	rm -f ${DEPLOY_DIR}/${ARTIFACT}
	cd $(SRC_DIR) ; zip -qr ${DEPLOY_DIR}/${ARTIFACT} *
	cd $(LIB_DIR) ; zip -qr ${DEPLOY_DIR}/${ARTIFACT} *

test: init 
	# run any unit tests here

init:
	mkdir -p ${LIB_DIR}
	pip install -r /build/requirements.txt -t $(LIB_DIR) --upgrade

clean:
	rm $(DEPLOY_DIR)/$(ARTIFACT)
