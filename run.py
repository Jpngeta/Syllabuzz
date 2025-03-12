from app import app
from app import start_app

if __name__ == '__main__':
    # Start background processes before running the app
    start_app()
    
    # Run the Flask app
    app.run(debug=True, host="0.0.0.0", port=3000)