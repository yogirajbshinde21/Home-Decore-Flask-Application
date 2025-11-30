#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p static/pdfs
mkdir -p instance

# Run database migrations
python -c "
from main import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
