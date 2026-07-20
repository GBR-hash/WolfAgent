# LLM Configuration
import os, logging, sys
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MODEL_NAME = "deepseek-chat"

def get_llm(temperature: float = 0.7) -> ChatDeepSeek:
    return ChatDeepSeek(
        model=MODEL_NAME,
        api_key=DEEPSEEK_API_KEY,
        temperature=temperature,
        max_tokens=1024,
    )

# ======== Logging Setup ========

def setup_logging(name: str = "wolfagent") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler ? append mode, UTF-8
    fh = logging.FileHandler("_server.log", encoding="utf-8", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    ))

    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger
