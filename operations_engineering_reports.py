"""operations-engineering-reports"""
from report_app import run_app as app

if __name__ == "__main__":
    app.run(port=app.config.get("PORT", 4567))
