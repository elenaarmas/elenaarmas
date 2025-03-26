.PHONY: build clean

build:
	python main.py
	./post-process.sh
	cat styles.css >> docs/wp-includes/css/classic-themes.min.css
	./post-fix-relative-paths.sh

clean:
	rm -rf docs/ .cache/ __pycache__/
