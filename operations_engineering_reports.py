"""operations-engineering-reports"""
from report_app import app

if __name__ == "__main__":
    app.run(port=app.config.get("PORT", 4567))
