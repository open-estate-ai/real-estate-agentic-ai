#!/usr/bin/env python3
"""
Test Lambda handler locally.

This simulates an SQS event and tests the Lambda handler function.
"""

from lambda_handler import lambda_handler
import json
import sys
import uuid

# Add src to path
sys.path.insert(0, 'src')


def test_single_message():
    """Test with a single SQS message."""
    print("=" * 60)
    print("🧪 Test 1: Single SQS Message")
    print("=" * 60)

    event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "query": "Find 3BHK luxury apartments in Bangalore under 2 crore",
                    "user_id": "test-user-123",
                    "context": {
                        "budget": 20000000,
                        "city": "Bangalore",
                        "bedrooms": 3,
                    }
                })
            }
        ]
    }

    print(f"\n📥 Input Event:")
    print(json.dumps(event, indent=2))

    result = lambda_handler(event, None)

    print(f"\n📤 Lambda Response:")
    print(json.dumps(result, indent=2))

    response_body = json.loads(result['body'])
    assert response_body['successful'] == 1
    assert response_body['failed'] == 0

    print("\n✅ Test 1 passed!\n")


def test_multiple_messages():
    """Test with multiple SQS messages."""
    print("=" * 60)
    print("🧪 Test 2: Multiple SQS Messages (Batch)")
    print("=" * 60)

    event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "query": "Find affordable 2BHK in Noida",
                    "user_id": "user-1",
                    "context": {"budget": 5000000}
                })
            },
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "query": "Luxury penthouses in Mumbai",
                    "user_id": "user-2",
                    "context": {"budget": 100000000}
                })
            },
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "query": "Commercial office space in Gurgaon",
                    "user_id": "user-3",
                    "context": {"type": "commercial"}
                })
            }
        ]
    }

    print(f"\n📥 Input Event (3 messages):")
    print(json.dumps(event, indent=2))

    result = lambda_handler(event, None)

    print(f"\n📤 Lambda Response:")
    print(json.dumps(result, indent=2))

    response_body = json.loads(result['body'])
    print(f"\n📊 Summary:")
    print(f"  Processed: {response_body['processed']}")
    print(f"  Successful: {response_body['successful']}")
    print(f"  Failed: {response_body['failed']}")

    assert response_body['processed'] == 3

    print("\n✅ Test 2 passed!\n")


def test_invalid_message():
    """Test with invalid message (missing query)."""
    print("=" * 60)
    print("🧪 Test 3: Invalid Message (Missing Query)")
    print("=" * 60)

    event = {
        "Records": [
            {
                "messageId": f"test-{uuid.uuid4()}",
                "body": json.dumps({
                    "user_id": "user-123",
                    # Missing 'query' field
                })
            }
        ]
    }

    print(f"\n📥 Input Event:")
    print(json.dumps(event, indent=2))

    result = lambda_handler(event, None)

    print(f"\n📤 Lambda Response:")
    print(json.dumps(result, indent=2))

    response_body = json.loads(result['body'])
    assert response_body['failed'] == 1

    print("\n✅ Test 3 passed (error handled correctly)!\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 Lambda Handler Tests")
    print("=" * 60)
    print("\nMake sure:")
    print("  1. PostgreSQL is running (docker-compose up -d)")
    print("  2. Environment variables are set (.env file)")
    print("=" * 60)
    print()

    input("Press Enter to start tests...")

    try:
        test_single_message()
        test_multiple_messages()
        test_invalid_message()

        print("=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
