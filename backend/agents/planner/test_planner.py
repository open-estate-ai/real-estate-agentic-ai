#!/usr/bin/env python3
"""
Test script for Planner Agent.

Run this after starting Tilt to test the planner agent locally.
"""

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8081"


def test_health():
    """Test health endpoint."""
    print("🏥 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 200
    assert response.json()["service"] == "planner-agent"
    print("✅ Health check passed\n")


def test_create_plan():
    """Test plan creation."""
    print("📋 Creating a plan...")

    job_id = f"test-{uuid.uuid4()}"

    request_data = {
        "job_id": job_id,
        "query": "Find 3BHK luxury apartments in Bangalore under 2 crore with good amenities",
        "user_id": "test-user-123",
        "context": {
            "budget": 20000000,
            "city": "Bangalore",
            "bedrooms": 3
        }
    }

    print(f"Request: {json.dumps(request_data, indent=2)}")

    response = requests.post(
        f"{BASE_URL}/plan",
        json=request_data,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        print("✅ Plan created successfully\n")
        return job_id
    else:
        print(f"❌ Error: {response.text}")
        return None


def test_get_job_status(job_id):
    """Test getting job status."""
    if not job_id:
        print("⏭️  Skipping job status check (no job_id)\n")
        return

    print(f"📊 Getting job status for {job_id}...")

    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Job Status: {result['status']}")
        print(f"Job Type: {result['type']}")
        print(f"Created: {result['created_at']}")
        if result.get('response_payload'):
            print(
                f"Plan Steps: {len(result['response_payload'].get('plan', {}).get('steps', []))}")
        print("✅ Job status retrieved\n")
    else:
        print(f"❌ Error: {response.text}\n")


def test_get_child_jobs(job_id):
    """Test getting child jobs."""
    if not job_id:
        print("⏭️  Skipping child jobs check (no job_id)\n")
        return

    print(f"👶 Getting child jobs for {job_id}...")

    response = requests.get(f"{BASE_URL}/jobs/{job_id}/children")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Parent Job: {result['parent_job_id']}")
        print(f"Child Count: {result['child_count']}")

        if result['children']:
            print("\nChild Jobs:")
            for child in result['children']:
                print(f"  - {child['job_id']}")
                print(f"    Type: {child['type']}")
                print(f"    Status: {child['status']}")

        print("✅ Child jobs retrieved\n")
    else:
        print(f"❌ Error: {response.text}\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Planner Agent")
    print("=" * 60)
    print()

    try:
        # Test 1: Health check
        test_health()

        # Test 2: Create plan
        job_id = test_create_plan()

        # Wait a moment for processing
        if job_id:
            time.sleep(1)

        # Test 3: Get job status
        test_get_job_status(job_id)

        # Test 4: Get child jobs
        test_get_child_jobs(job_id)

        print("=" * 60)
        print("🎉 All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("❌ Connection Error!")
        print("Make sure Tilt is running and planner-agent is available at http://localhost:8081")
        print("\nTo start Tilt:")
        print("  cd real-estate-agentic-ai")
        print("  tilt up")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
