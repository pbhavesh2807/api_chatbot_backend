from app import app

# This is for Vercel serverless deployment
# Vercel needs a variable named "app" that is an ASGI application
# The app variable is already defined in app.py, so we just import it here 