import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Video Stream
    stream_url: str = os.getenv("STREAM_URL", "")
    frame_limit: int = int(os.getenv("FRAME_LIMIT", "20000"))
    
    # Detection
    model_path: str = os.getenv("MODEL_PATH", "yolov8n.pt")
    confidence_threshold: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    polygon_config_path: str = os.getenv("POLYGON_CONFIG_PATH", "detection/polygon_config.json")
    
    # Output Paths
    output_video_path: str = os.getenv("OUTPUT_VIDEO_PATH", "dataset/recorded_video.mp4")
    output_frames_dir: str = os.getenv("OUTPUT_FRAMES_DIR", "dataset/frames/")
    detection_output_dir: str = os.getenv("DETECTION_OUTPUT_DIR", "output/frames_with_bbox/")
    count_log_path: str = os.getenv("COUNT_LOG_PATH", "output/count_log.json")

settings = Settings()
