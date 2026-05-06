FROM node:20-bookworm

# Install Python 3 and venv
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv

# Create a virtual environment to safely install Python packages
RUN python3 -m venv /opt/venv
# Ensure the virtual environment is used for all subsequent python/pip commands
ENV PATH="/opt/venv/bin:$PATH"

# Install Playwright and download Chromium with its system dependencies
RUN pip install playwright groq PyPDF2 && \
    playwright install chromium --with-deps

# Install n8n globally via npm (Node 20 already has npm pre-installed)
RUN npm install -g n8n

WORKDIR /app

EXPOSE 5678

# Start n8n
CMD ["n8n", "start"]
