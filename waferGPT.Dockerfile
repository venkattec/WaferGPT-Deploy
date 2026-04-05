FROM python:3.10-slim
WORKDIR /app
# Install system dependencies for ML if needed (e.g., libgomp1)
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir requests langchain-core langchain-community langgraph opencv-python-headless
RUN pip install git+https://github.com/huggingface/transformers.git@3a3b59cb1a7c0238c8d1072e35d3879c5faff48e
RUN pip install git+https://github.com/lm-sys/FastChat.git@f34f28cedcb8906fd026f22ec3ef41435a8e24ac


# 6. Install the rest of the requirements (No-Deps to avoid rolling back our fixes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --no-deps
# 7. Copy the specific Backend and Frontend folders
COPY backend ./backend
COPY frontend ./frontend

# 8. Expose the ports you specified
EXPOSE 8555 8501

# 9. Start-up Script: Run both applications simultaneously
CMD ["sh", "-c", "cd /app/backend && python agentic_flow/flask_backend.py & cd /app/frontend && python app.py"]