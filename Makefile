SUBSET ?=
PY ?= python3

.PHONY: up down label clean-data fetch-train train train-v2 package eval eval-teacher test lint load-test image

up:            ## build and deploy everything from a fresh clone
	scripts/up.sh

down:          ## delete the cluster
	k3d cluster delete cloudproj

image:
	docker build -f service/Dockerfile -t parser-service:local .

label:         ## Task 1: sharded teacher labelling in the cluster
	scripts/label.sh

clean-data:    ## Task 1: clean shard outputs -> datasets/v1/train.jsonl (+ .sha256)
	scripts/with_s3.sh $(PY) worker/clean.py

train:         ## Task 2: make train [SUBSET=50]
	$(PY) training/train.py --config training/config.yaml $(if $(SUBSET),--subset $(SUBSET),)

train-v2:
	$(PY) training/train.py --config training/config_v2.yaml

package:       ## make package V=v1  -> dist/model-v1.tar.gz + models/v1/model.sha256
	$(PY) scripts/package_model.py artifacts/$(V) $(V)

eval:          ## score the untrained and trained students on validation.jsonl
	$(PY) eval/run_student.py EleutherAI/pythia-70m data/validation.jsonl results/untrained_predictions.jsonl
	$(PY) tools/score.py results/untrained_predictions.jsonl data/validation.jsonl --out results/untrained_validation.json
	$(PY) eval/run_student.py artifacts/v1 data/validation.jsonl results/student_predictions.jsonl
	$(PY) tools/score.py results/student_predictions.jsonl data/validation.jsonl --out results/student_validation.json

eval-teacher:  ## needs Ollama running with phi3.5
	$(PY) eval/run_teacher.py data/validation.jsonl results/teacher_predictions.jsonl
	$(PY) tools/score.py results/teacher_predictions.jsonl data/validation.jsonl --out results/teacher_validation.json

test:
	$(PY) -m pytest -q

lint:
	ruff check .

load-test:
	mkdir -p results
	locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m \
	  --host http://localhost:8080 --csv results/loadtest

fetch-train:   ## copy datasets/v1/train.jsonl (+ .sha256) from object storage into data/
	scripts/with_s3.sh $(PY) scripts/s3_tool.py get-file datasets v1/train.jsonl data/train.jsonl
	scripts/with_s3.sh $(PY) scripts/s3_tool.py get-file datasets v1/train.sha256 data/train.sha256
	scripts/with_s3.sh $(PY) scripts/s3_tool.py get-file datasets v1/counts.json results/clean_counts.json
	cd data && sha256sum -c train.sha256
