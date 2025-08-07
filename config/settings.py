"""Configuration settings for the trading bot."""

from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Configuration
    telegram_bot_token: str
    telegram_channels: List[str]
    
    # Zerodha Kite Configuration
    kite_api_key: str
    kite_api_secret: str
    kite_access_token: Optional[str] = None
    kite_user_id: str
    
    # OpenRouter Configuration
    openrouter_api_key: str
    openrouter_models: List[str] = ["anthropic/claude-3-haiku", "meta-llama/llama-3.1-8b-instruct"]
    
    # Database Configuration
    database_url: str = "postgresql://trading_user:trading_password123@localhost:5432/trading_bot"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Risk Management Settings
    max_position_size: float = 100000.0
    max_daily_loss: float = 5000.0
    max_drawdown: float = 0.15
    stop_loss_percentage: float = 0.02
    target_percentage: float = 0.05
    
    # System Settings
    log_level: str = "INFO"
    environment: str = "development"
    enable_live_trading: bool = False
    enable_paper_trading: bool = True
    
    # Alert Settings
    alert_email: Optional[str] = None
    alert_telegram_chat_id: Optional[str] = None
    
    # Trading Settings
    min_signal_confidence: float = 0.7
    max_orders_per_day: int = 20
    max_positions: int = 10
    
    # Backtesting Settings
    backtest_start_date: Optional[str] = None
    backtest_end_date: Optional[str] = None
    backtest_initial_capital: float = 100000.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment == "production"
    
    @property
    def is_live_trading_enabled(self) -> bool:
        """Check if live trading is enabled."""
        return self.enable_live_trading and self.is_production


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()