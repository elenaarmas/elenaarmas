.PHONY: build clean

build:
	python main.py
	./post-process.sh
	./inject-assets.sh
	cat styles.css >> docs/wp-includes/css/classic-themes.min.css

clean:
	rm -rf docs/ .cache/ __pycache__/
