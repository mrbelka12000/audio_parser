.PHONY: build run

build:
	@pip install -r requirements.txt
	@python3 pyinstall.py
	sudo mv dist/AudioParser /usr/local/bin/

run:
	@python3 main.py
