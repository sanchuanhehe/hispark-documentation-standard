.PHONY: install start start-core site site-core html html-core pdf pdf-core tex tex-core check check-core all-profiles clean

install:
	npm install

start:
	npm run start

start-core:
	npm run start:core

site:
	npm run build:site

site-core:
	npm run build:site:core

html:
	npm run build:html

html-core:
	npm run build:html:core

pdf:
	npm run build:pdf

pdf-core:
	npm run build:pdf:core

tex:
	npm run build:tex

tex-core:
	npm run build:tex:core

check:
	npm run check

check-core:
	npm run check:core

all-profiles:
	npm run build:all:profiles

clean:
	npx myst clean -y
