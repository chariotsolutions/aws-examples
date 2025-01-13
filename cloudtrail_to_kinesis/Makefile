.PHONY: default deploy package init clean

LAMBDA_NAME     ?= CloudTrail_Event_Processor

SRC_DIR         := $(PWD)/lambda
BUILD_DIR       := $(SRC_DIR)
DEPLOY_DIR      := $(SRC_DIR)
ARTIFACT        := lambda.zip

default: package

deploy: package
	aws lambda update-function-code --function-name $(LAMBDA_NAME) --zip-file fileb://$(DEPLOY_DIR)/$(ARTIFACT)

package: init
	rm -f ${DEPLOY_DIR}/${ARTIFACT}
	cd $(BUILD_DIR) ; zip ${DEPLOY_DIR}/${ARTIFACT} *.py

clean:
	rm -f $(DEPLOY_DIR)/$(ARTIFACT)
	rm -rf */__pycache__
