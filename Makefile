init:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest -v

kill:
	@pkill -f "Google Chrome" && echo "Killed all chrome processes" || echo "No chrome processes found to kill"

# Set default message if not provided
MESSAGE ?= new-migration

# Generate a timestamped alembic migration
migration-create:
	@TIMESTAMP=$$(date +%Y%m%d%H%M) && \
	echo "🔧 Generating migration: $$TIMESTAMP - $(MESSAGE)" && \
	alembic revision --autogenerate -m "$(MESSAGE)" --rev-id "$$TIMESTAMP"

# Apply the latest migration
migration-upgrade:
	alembic upgrade head

# Downgrade to the previous migration
migration-downgrade:
	alembic downgrade -1

# Show current revision
migration-current:
	alembic current

# Show the full history of revisions
migration-history:
	alembic history

.PHONY: init test kill
