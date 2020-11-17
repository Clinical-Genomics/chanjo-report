.PHONY: help build setup report-html report-pdf
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build chanjo-report Docker Image
	docker-compose build

setup: ## Use Chanjo to set up a mysql database containing demo data
	echo "Setup chanjo database"
	docker-compose run chanjo-cli /bin/bash -c "chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test init --auto demodata && chanjo --config demodata/chanjo.yaml link demodata/hgnc.grch37p13.exons.bed"
	echo "Loading coverage from demo files"
	docker-compose run chanjo-cli chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test load -s sample1 -g test_group chanjo/init/demo-files/sample1.coverage.bed
	docker-compose run chanjo-cli chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test load -s sample2 -g test_group chanjo/init/demo-files/sample2.coverage.bed
	docker-compose run chanjo-cli chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test load -s sample3 -g test_group chanjo/init/demo-files/sample3.coverage.bed

report-html: ## Create a coverage report in HTML format
	docker-compose run -p 5000:5000 chanjo-report chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test report --render html

report-pdf: ## Create a coverage report in HTML format
	docker-compose run -p 5050:5050 chanjo-report chanjo -d mysql+pymysql://chanjoUser:chanjoPassword@mariadb/chanjo4_test report --render pdf

prune: ## Remove orphans and dangling images
	docker-compose down --remove-orphans
	docker images prune