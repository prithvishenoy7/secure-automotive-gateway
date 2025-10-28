"""
Configuration management for CAN Data Processor

Concept: Separate configuration from code for security and flexibility
- Environment variables for sensitive data (AWS credentials)
- Constants for application settings
- Validation to fail fast if misconfigured
"""

import os
import sys
from typing import Optional


class Config:
    """Application configuration with security best practices"""
    
    # AWS Configuration
    # Concept: These will come from EC2 instance IAM role in production
    # For local testing, use AWS CLI credentials or environment variables
    AWS_REGION: str = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME: str = os.getenv('S3_BUCKET_NAME', '')
    
    # Processing Configuration
    MAX_MESSAGE_SIZE: int = 20  # Max hex string length (8 bytes = 16 hex chars)
    VALID_DLC_RANGE: tuple = (0, 8)  # CAN DLC must be 0-8
    
    # Known CAN IDs (whitelist for validation)
    VALID_CAN_IDS: set = {
        '0x100',  # Engine RPM
        '0x200',  # Vehicle speed
        '0x300',  # Coolant temp
        '0x400',  # Throttle position
        '0x500',  # Fuel level
        '0x600',  # Brake pressure
    }
    
    # Security Configuration
    ENABLE_STRICT_VALIDATION: bool = True
    MAX_MESSAGES_PER_BATCH: int = 10000  # Prevent DoS from huge files
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration before running
        
        Concept: Fail fast - detect configuration errors before processing data
        """
        errors = []
        
        if not cls.S3_BUCKET_NAME:
            errors.append("S3_BUCKET_NAME environment variable not set")
        
        if cls.MAX_MESSAGES_PER_BATCH < 1:
            errors.append("MAX_MESSAGES_PER_BATCH must be positive")
        
        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print configuration (excluding sensitive data)"""
        print("📋 Configuration:")
        print(f"   AWS Region: {cls.AWS_REGION}")
        print(f"   S3 Bucket: {cls.S3_BUCKET_NAME}")
        print(f"   Max Messages: {cls.MAX_MESSAGES_PER_BATCH}")
        print(f"   Strict Validation: {cls.ENABLE_STRICT_VALIDATION}")
        print(f"   Log Level: {cls.LOG_LEVEL}")


# Validate configuration on import
if __name__ != "__main__":  # Don't validate during direct execution
    if not Config.validate():
        print("⚠️  Configuration validation failed - continuing anyway for development")