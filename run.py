from app import create_app
from datetime import datetime

app = create_app()

@app.context_processor
def inject_globals():
    return dict(now=datetime.utcnow, enumerate=enumerate)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
