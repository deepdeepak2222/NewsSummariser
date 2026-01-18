#!/bin/bash

# Start FastAPI server in background
python api.py &
API_PID=$!

# Start Streamlit app
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true

# Wait for API process
wait $API_PID

