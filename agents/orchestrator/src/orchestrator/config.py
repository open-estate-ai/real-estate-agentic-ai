import os
from dotenv import load_dotenv

# Load environment variables 
load_dotenv()

# Global configuration variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Add other variables as needed

def validate_config():
    """
    Validates required environment variables and prints their status.
    Returns True if all required variables are set, False otherwise.
    """
    # List of required environment variables
    required = ["OPENAI_API_KEY"]
    
    all_valid = True
    
    # Check each required variable
    for name in required:
        value = os.getenv(name)
        if not value:
            print(f"ERROR: Required variable {name} is not set")
            all_valid = False
        else:
            # Show first and last 3 characters of the key for verification
            masked = f"{value[:3]}...{value[-3:]}" if len(value) > 6 else "***"
            print(f"✓ {name} is set ({masked})")
    
    return all_valid