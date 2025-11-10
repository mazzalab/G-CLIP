FROM mcr.microsoft.com/devcontainers/miniconda:latest

# Install fonts for Linux
RUN apt-get update && apt-get install -y \
    wget \
    git \
    build-essential \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Configure Git to avoid CRLF issues
RUN git config --global core.autocrlf false && \
    git config --global core.eol lf && \
    git reset --hard || true

# Create environment + install deps
RUN conda create -n gclip python=3.11 -y && \
    conda install -n gclip -c conda-forge \
        pandas \
        pillow \
        pytest \
        openpyxl \
        numpy \
        pyinstaller \
        && conda clean -afy

RUN echo "conda activate gclip" >> /home/vscode/.bashrc

USER vscode
WORKDIR /workspace
