PYTHONPATH := ../../packages

.PHONY: run install

install:
	cd services/ingestion && pip install -r requirements.txt

run:
	cd services/ingestion && PYTHONPATH=$(PYTHONPATH) python handler.py