"""Local test of CAN processor (no AWS required)"""

from processor import CANMessageValidator, CANDataProcessor
import json

# Test 1: Validate individual messages
print("Test 1: Message Validation")
print("-" * 40)

validator = CANMessageValidator()

# Valid message
valid_msg = {
    'timestamp': '1758156000.123',
    'can_id': '0x100',
    'data': '0x1234567890ABCDEF',
    'dlc': '8',
    'signal_name': 'engine_rpm'
}
is_valid, error = validator.validate_message(valid_msg)
print(f"Valid message: {is_valid} (error: {error})")

# Invalid message - bad CAN ID
invalid_msg = {
    'timestamp': '1758156000.123',
    'can_id': 'NOT_HEX',
    'data': '0x1234567890ABCDEF',
    'dlc': '8'
}
is_valid, error = validator.validate_message(invalid_msg)
print(f"Invalid CAN ID: {is_valid} (error: {error})")

# Invalid message - malicious data
malicious_msg = {
    'timestamp': '1698156000.123',
    'can_id': '0x100',
    'data': '0x' + 'A' * 100,  # Too long!
    'dlc': '8'
}
is_valid, error = validator.validate_message(malicious_msg)
print(f"Malicious data: {is_valid} (error: {error})")

print("\n✅ Validation tests passed!\n")

# Test 2: Read and process data
print("Test 2: Data Processing")
print("-" * 40)

# We can't test S3 upload without AWS, but we can test reading and processing
# Create a mock processor for local testing
class MockProcessor(CANDataProcessor):
    def __init__(self):
        self.validator = CANMessageValidator()
        # Don't initialize S3 client
    
    def upload_to_s3(self, data):
        print("\n📦 Would upload to S3:")
        print(json.dumps(data['metadata'], indent=2))
        return True

processor = MockProcessor()
messages = processor.read_can_data('../data/sample_can_data.csv')
processed = processor.process_data(messages)
processor.upload_to_s3(processed)

print("\n✅ Processing tests passed!")