.PHONY: default deploy package init clean

LAMBDA_NAME     ?= CloudTrail_to_Elasticsearch
DEPLOY_DIR      := $(PWD)
ARTIFACT        := lambda.zip

SRC_DIR         := $(PWD)/src
LIB_DIR         := $(PWD)/lib

# PIP_HACK allows us to run on Debian and non-Debian systems
PIP_HACK        != pip help install | grep -q '\-\-system' && echo -n "--system"

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(DEPLOY_DIR)/$(ARTIFACT)

package: init
	mkdir -p ${DEPLOY_DIR}
	rm -f ${DEPLOY_DIR}/${ARTIFACT}
	cd $(SRC_DIR) ; zip -qr ${DEPLOY_DIR}/${ARTIFACT} *
	cd $(LIB_DIR) ; zip -qr ${DEPLOY_DIR}/${ARTIFACT} *

init:
	mkdir -p ${LIB_DIR}
	pip install $(PIP_HACK) -r requirements.txt -t $(LIB_DIR) --upgrade

clean:
	rm $(DEPLOY_DIR)/$(ARTIFACT)

