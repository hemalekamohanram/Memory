.PHONY: api web test seed reset

api:
	python -m uvicorn services.api.app.main:app --reload

web:
	pnpm --dir apps/web dev

test:
	python -m pytest
	pnpm --dir apps/web test

seed:
	python scripts/seed_demo.py

reset:
	python scripts/reset_demo.py
