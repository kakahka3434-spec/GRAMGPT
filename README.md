# GRAMGPT

GRAMGPT is a professional, high-performance Telegram bot built with Python, [aiogram 3.x](https://docs.aiogram.dev/), and [OpenAI GPT-4](https://openai.com/). It's designed to provide a seamless AI-powered chat experience directly within Telegram.

## 🚀 Features

- **AI Chatting**: Engage in natural conversations powered by OpenAI's latest models.
- **Asynchronous Architecture**: Built on top of `asyncio` and `aiogram` for high concurrency.
- **Modern Configuration**: Uses `pydantic-settings` for robust environment variable management.
- **Modular Design**: Clean separation of concerns with routers and handlers.
- **Docker Ready**: Includes a `Dockerfile` for easy deployment.

## 🛠 Tech Stack

- **Python 3.11+**
- **aiogram 3.x**: The most advanced Telegram Bot API framework for Python.
- **OpenAI API**: For state-of-the-art language processing.
- **Pydantic Settings**: For type-safe configuration.

## ⚙️ Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/rpauts2/GRAMGPT.git
    cd GRAMGPT
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment**:
    Copy `.env.example` to `.env` and fill in your tokens:
    ```bash
    cp .env.example .env
    # Edit .env with your BOT_TOKEN and OPENAI_API_KEY
    ```

4.  **Run the bot**:
    ```bash
    python -m src.main
    ```

## 🐳 Docker Deployment

```bash
docker build -t gramgpt .
docker run --env-file .env gramgpt
```
