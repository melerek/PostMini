"""
Demo Script for Environment Variables

This script creates sample environments, collections, and requests
to demonstrate the environment variables feature.

Run this script to populate your database with example data:
    python demo_environments.py
"""

from src.core.database import DatabaseManager


def create_demo_data():
    """Create demo environments, collections, and requests."""
    print("Creating demo data for Environment Variables...")
    
    db = DatabaseManager()
    
    # Create environments
    print("\n1. Creating Environments...")
    
    try:
        # Development Environment
        dev_env_id = db.create_environment("Development", {
            "baseUrl": "https://jsonplaceholder.typicode.com",
            "apiKey": "dev-key-12345",
            "version": "v1",
            "timeout": "5000",
            "userId": "1"
        })
        print("   [OK] Development environment created")
        
        # Staging Environment
        staging_env_id = db.create_environment("Staging", {
            "baseUrl": "https://staging-api.example.com",
            "apiKey": "staging-key-67890",
            "version": "v2",
            "timeout": "8000",
            "userId": "2"
        })
        print("   [OK] Staging environment created")
        
        # Production Environment (with different values)
        prod_env_id = db.create_environment("Production", {
            "baseUrl": "https://api.example.com",
            "apiKey": "prod-key-secret",
            "version": "v2",
            "timeout": "10000",
            "userId": "1"
        })
        print("   [OK] Production environment created")
        
    except Exception as e:
        print(f"   [WARN] Environments may already exist: {e}")
    
    # Create collection
    print("\n2. Creating Collection...")
    
    try:
        collection_id = db.create_collection("Environment Demo - JSONPlaceholder")
        print("   [OK] Collection created")
    except Exception as e:
        print(f"   [WARN] Collection may already exist: {e}")
        # Get existing collection
        collections = db.get_all_collections()
        for col in collections:
            if "Environment Demo" in col['name']:
                collection_id = col['id']
                break
        else:
            collection_id = collections[0]['id'] if collections else None
    
    if not collection_id:
        print("   [ERROR] Could not create or find collection")
        return
    
    # Create requests with environment variables
    print("\n3. Creating Requests with Environment Variables...")
    
    try:
        # Request 1: Get user with variable
        db.create_request(
            collection_id=collection_id,
            name="Get User by ID (with variable)",
            method="GET",
            url="{{baseUrl}}/users/{{userId}}",
            headers={
                "X-API-Key": "{{apiKey}}",
                "X-API-Version": "{{version}}"
            },
            params={
                "timeout": "{{timeout}}"
            }
        )
        print("   [OK] Request 1: Get User by ID")
        
        # Request 2: Get all posts
        db.create_request(
            collection_id=collection_id,
            name="Get All Posts",
            method="GET",
            url="{{baseUrl}}/posts",
            headers={
                "Accept": "application/json",
                "X-API-Key": "{{apiKey}}"
            }
        )
        print("   [OK] Request 2: Get All Posts")
        
        # Request 3: Create post with variables in body
        db.create_request(
            collection_id=collection_id,
            name="Create Post (with variable body)",
            method="POST",
            url="{{baseUrl}}/posts",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "{{apiKey}}"
            },
            body="""{
  "title": "Demo Post from {{version}}",
  "body": "This is a test post created using environment variables. API: {{baseUrl}}",
  "userId": {{userId}}
}"""
        )
        print("   [OK] Request 3: Create Post")
        
        # Request 4: Get user's posts
        db.create_request(
            collection_id=collection_id,
            name="Get User's Posts",
            method="GET",
            url="{{baseUrl}}/users/{{userId}}/posts",
            headers={
                "X-API-Key": "{{apiKey}}"
            }
        )
        print("   [OK] Request 4: Get User's Posts")
        
        # Request 5: Bearer token example
        db.create_request(
            collection_id=collection_id,
            name="Protected Resource (Bearer Token)",
            method="GET",
            url="{{baseUrl}}/protected/resource",
            auth_type="Bearer Token",
            auth_token="{{apiKey}}"
        )
        print("   [OK] Request 5: Protected Resource")
        
    except Exception as e:
        print(f"   [WARN] Some requests may already exist: {e}")
    
    db.close()
    
    print("\n" + "="*60)
    print("[SUCCESS] Demo data created successfully!")
    print("="*60)
    print("\nHow to use:")
    print("1. Run the application: python main.py")
    print("2. Select 'Development' from the Environment dropdown")
    print("3. Open the 'Environment Demo' collection")
    print("4. Click on any request to see the variables ({{baseUrl}}, etc.)")
    print("5. Click 'Send' - variables will be replaced automatically!")
    print("6. Try switching to different environments and send again")
    print("\nTip: Open 'Manage Environments' to see all variables")
    print()


if __name__ == "__main__":
    create_demo_data()

