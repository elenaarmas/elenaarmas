.PHONY: build clean

CONFIG_FILE := config.json

build:
	python main.py --config $(CONFIG_FILE)
	./post-process.sh --config $(CONFIG_FILE)
	cat $(shell jq -r .build.styles_file $(CONFIG_FILE)) >> $(shell jq -r .directories.output $(CONFIG_FILE))/$(shell jq -r .build.styles_target $(CONFIG_FILE))
	./post-fix-relative-paths.sh --config $(CONFIG_FILE)

clean:
	rm -rf $(shell jq -r .directories.output $(CONFIG_FILE))/ $(shell jq -r .directories.cache $(CONFIG_FILE))/ __pycache__/
