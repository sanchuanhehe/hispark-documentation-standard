.PHONY: install start html pdf tex check clean

install:
	npm install

start:
	npm run start

html:
	npm run build:html

pdf:
	npm run build:pdf

tex:
	npm run build:tex

check:
	npm run check

clean:
	npx myst clean -y

