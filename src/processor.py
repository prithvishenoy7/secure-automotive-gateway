"""
Secure Automotive CAN Data Processor

This module processes simulated CAN bus data and securely stores it in AWS S3.

Security Features (mapped to TARA):
- Input validation (TS-003: Malicious data injection)
- No hardcoded credentials (TS-002: Credential theft)
- Encryption in transit via HTTPS (TS-004: MITM)
- Structured logging (TS-001, TS-005: Audit trail)

Author: Prithvi Shenoy
Date: 2024-06-15
"""

import csv
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import re

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from config import Config


# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CANMessageValidator:
    """
    Validates CAN messages for security and correctness
    
    Concept: Input validation is the first line of defense
    - Whitelist known good values
    - Reject suspicious patterns
    - Fail safely (log and skip, don't crash)
    """
    
    @staticmethod
    def validate_message(row: Dict[str, str]) -> Tuple[bool, Optional[str]]:
        """
        Validate a single CAN message
        
        Args:
            row: Dictionary with keys: timestamp, can_id, data, dlc, signal_name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required fields exist
        required_fields = ['timestamp', 'can_id', 'data', 'dlc']
        for field in required_fields:
            if field not in row or not row[field]:
                return False, f"Missing or empty required field: {field}"
        
        # Validate timestamp
        try:
            timestamp = float(row['timestamp'])
            if timestamp < 0:
                return False, "Timestamp cannot be negative"
            # Check for reasonable timestamp (not too far in past/future)
            current_time = datetime.now(timezone.utc).timestamp()
            if abs(current_time - timestamp) > 86400 * 365:  # 1 year
                return False, f"Timestamp suspiciously far from current time: {timestamp}"
        except (ValueError, TypeError):
            return False, f"Invalid timestamp format: {row['timestamp']}"
        
        # Validate CAN ID
        can_id = row['can_id'].lower()
        if not re.match(r'^0x[0-9a-f]+$', can_id):
            return False, f"Invalid CAN ID format: {can_id}"
        
        # Whitelist validation (optional but recommended)
        if Config.ENABLE_STRICT_VALIDATION:
            if can_id not in [vid.lower() for vid in Config.VALID_CAN_IDS]:
                return False, f"Unknown CAN ID (not in whitelist): {can_id}"
        
        # Validate data field
        data = row['data'].lower()
        if not re.match(r'^0x[0-9a-f]+$', data):
            return False, f"Invalid data format: {data}"
        
        # Check data length (8 bytes = 16 hex chars + '0x' prefix)
        if len(data) > Config.MAX_MESSAGE_SIZE:
            return False, f"Data field too long: {len(data)} (max {Config.MAX_MESSAGE_SIZE})"
        
        # Validate DLC (Data Length Code)
        try:
            dlc = int(row['dlc'])
            if dlc < Config.VALID_DLC_RANGE[0] or dlc > Config.VALID_DLC_RANGE[1]:
                return False, f"Invalid DLC value: {dlc} (must be {Config.VALID_DLC_RANGE[0]}-{Config.VALID_DLC_RANGE[1]})"
        except (ValueError, TypeError):
            return False, f"Invalid DLC format: {row['dlc']}"
        
        # Security: Check for suspicious patterns (defense in depth)
        suspicious_patterns = ['--', ';', 'drop', 'select', 'union', 'script', '<', '>']
        row_str = str(row.values()).lower()
        for pattern in suspicious_patterns:
            if pattern in row_str:
                logger.warning(f"Suspicious pattern detected: {pattern}")
                # Don't reject, but log for investigation
        
        return True, None


class CANDataProcessor:
    """
    Main processor for CAN data
    
    Architecture:
    1. Read CSV file
    2. Validate each message
    3. Process/transform data
    4. Upload to S3
    5. Log results
    """
    
    def __init__(self, bucket_name: str):
        """
        Initialize processor
        
        Concept: boto3 automatically discovers credentials from:
        1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        2. AWS credentials file (~/.aws/credentials)
        3. IAM role (when running on EC2) ← This is what we'll use in production
        
        We NEVER hardcode credentials in code!
        """
        self.bucket_name = bucket_name
        self.validator = CANMessageValidator()
        
        try:
            # Create S3 client
            # Concept: boto3 uses HTTPS by default (TS-004 mitigation)
            self.s3_client = boto3.client(
                's3',
                region_name=Config.AWS_REGION
            )
            logger.info(f"✅ S3 client initialized for bucket: {bucket_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize S3 client: {e}")
            raise
    
    def read_can_data(self, input_file: str) -> List[Dict]:
        """
        Read and validate CAN data from CSV
        
        Returns:
            List of valid CAN messages
        """
        valid_messages = []
        invalid_count = 0
        
        logger.info(f"📖 Reading CAN data from: {input_file}")
        
        try:
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for line_num, row in enumerate(reader, start=2):  # Start at 2 (header is line 1)
                    # Rate limiting check
                    if len(valid_messages) >= Config.MAX_MESSAGES_PER_BATCH:
                        logger.warning(f"⚠️  Reached max messages limit ({Config.MAX_MESSAGES_PER_BATCH})")
                        break
                    
                    # Validate message
                    is_valid, error = self.validator.validate_message(row)
                    
                    if is_valid:
                        valid_messages.append(row)
                    else:
                        invalid_count += 1
                        logger.warning(f"Line {line_num}: Invalid message - {error}")
            
            logger.info(f"✅ Read {len(valid_messages)} valid messages, {invalid_count} invalid")
            return valid_messages
            
        except FileNotFoundError:
            logger.error(f"❌ File not found: {input_file}")
            raise
        except Exception as e:
            logger.error(f"❌ Error reading file: {e}")
            raise
    
    def process_data(self, messages: List[Dict]) -> Dict:
        """
        Process CAN data - extract insights, aggregate, etc.
        
        For Week 1: Simple processing (count messages by CAN ID)
        Future: Complex analytics, anomaly detection, etc.
        
        Returns:
            Processed data dictionary
        """
        logger.info(f"⚙️  Processing {len(messages)} messages...")
        
        # Count messages by CAN ID
        message_counts = {}
        signal_data = {}
        
        for msg in messages:
            can_id = msg['can_id']
            signal_name = msg.get('signal_name', 'unknown')
            
            # Count by CAN ID
            message_counts[can_id] = message_counts.get(can_id, 0) + 1
            
            # Group by signal name
            if signal_name not in signal_data:
                signal_data[signal_name] = []
            
            signal_data[signal_name].append({
                'timestamp': msg['timestamp'],
                'can_id': can_id,
                'data': msg['data'],
            })
        
        # Create processed output
        processed = {
            'metadata': {
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'total_messages': len(messages),
                'unique_can_ids': len(message_counts),
                'processor_version': '1.0.0'
            },
            'message_counts': message_counts,
            'signals': signal_data
        }
        
        logger.info(f"✅ Processing complete: {len(message_counts)} unique CAN IDs")
        return processed
    
    def upload_to_s3(self, data: Dict) -> bool:
        """
        Upload processed data to S3
        
        Security features:
        - Uses HTTPS (boto3 default)
        - Server-side encryption (configured at bucket level)
        - IAM role authentication (no credentials in code)
        
        Returns:
            True if successful, False otherwise
        """
        # Generate unique filename with timestamp
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        filename = f"processed_can_{timestamp}.json"
        
        logger.info(f"☁️  Uploading to S3: s3://{self.bucket_name}/{filename}")
        
        try:
            # Convert to JSON
            json_data = json.dumps(data, indent=2)
            
            # Upload to S3
            # Concept: put_object uses HTTPS, server-side encryption is enabled at bucket level
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=json_data,
                ContentType='application/json',
                Metadata={
                    'processor': 'can-data-processor',
                    'version': '1.0.0'
                }
            )
            
            logger.info(f"✅ Upload successful: {filename}")
            logger.info(f"   Total size: {len(json_data)} bytes")
            logger.info(f"   Messages processed: {data['metadata']['total_messages']}")
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"❌ AWS Client Error ({error_code}): {e}")
            
            if error_code == 'NoSuchBucket':
                logger.error(f"   Bucket does not exist: {self.bucket_name}")
            elif error_code == 'AccessDenied':
                logger.error(f"   Access denied - check IAM permissions")
            
            return False
            
        except BotoCoreError as e:
            logger.error(f"❌ BotoCore Error: {e}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during upload: {e}")
            return False
    
    def run(self, input_file: str) -> bool:
        """
        Main processing pipeline
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Step 1: Read and validate
            messages = self.read_can_data(input_file)
            
            if not messages:
                logger.error("❌ No valid messages to process")
                return False
            
            # Step 2: Process
            processed_data = self.process_data(messages)
            
            # Step 3: Upload
            success = self.upload_to_s3(processed_data)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Processing failed: {e}")
            return False


def main():
    """Main entry point"""
    print("=" * 60)
    print("🚗 Secure Automotive CAN Data Processor")
    print("=" * 60)
    
    # Parse arguments
    if len(sys.argv) < 2:
        print("\n❌ Usage: python processor.py <input_csv_file> [s3_bucket_name]")
        print("\nExample:")
        print("  python processor.py data/sample_can_data.csv my-can-data-bucket")
        print("\nOr set S3_BUCKET_NAME environment variable:")
        print("  export S3_BUCKET_NAME=my-can-data-bucket")
        print("  python processor.py data/sample_can_data.csv")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Get bucket name from argument or environment
    if len(sys.argv) >= 3:
        bucket_name = sys.argv[2]
    else:
        bucket_name = Config.S3_BUCKET_NAME
    
    if not bucket_name:
        print("❌ S3 bucket name not provided")
        print("   Set S3_BUCKET_NAME environment variable or pass as argument")
        sys.exit(1)
    
    # Update config with bucket name
    Config.S3_BUCKET_NAME = bucket_name
    
    # Print configuration
    print()
    Config.print_config()
    print()
    
    # Validate configuration
    if not Config.validate():
        sys.exit(1)
    
    # Create processor and run
    try:
        processor = CANDataProcessor(bucket_name)
        success = processor.run(input_file)
        
        print()
        if success:
            print("=" * 60)
            print("✅ Processing completed successfully!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("=" * 60)
            print("❌ Processing failed - check logs above")
            print("=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()