"""
Simple Cloudinary Test Script
Run this to verify your Cloudinary configuration is working
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import datetime
import os

# Your Cloudinary Configuration
cloudinary.config(
    cloud_name="dledk0cg7",
    api_key="369151841227135",
    api_secret="xX71cDtIIvemLNu3WVi4LzZZZZM"
)

def test_cloudinary_connection():
    """Test basic Cloudinary connection and configuration"""
    print("=" * 50)
    print("CLOUDINARY CONNECTION TEST")
    print("=" * 50)
    
    try:
        # Test 1: Check configuration
        print("1. Testing Cloudinary configuration...")
        config = cloudinary.config()
        print(f"   Cloud Name: {config.cloud_name}")
        print(f"   API Key: {config.api_key}")
        print(f"   API Secret: {'*' * len(config.api_secret) if config.api_secret else 'NOT SET'}")
        print("   ✅ Configuration loaded successfully")
        
        # Test 2: Test API connectivity with ping
        print("\n2. Testing API connectivity...")
        ping_result = cloudinary.api.ping()
        print(f"   Status: {ping_result.get('status', 'unknown')}")
        print("   ✅ API connection successful")
        
        # Test 3: Upload a simple test image (text-based)
        print("\n3. Testing image upload...")
        
        # Create a simple test using Cloudinary's text overlay feature
        test_public_id = f"test_upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Upload a simple image using Cloudinary's sample image
        upload_result = cloudinary.uploader.upload(
            "C:\\Users\\shira\\OneDrive\\תמונות\\צילומי מסך\\Screenshot 2025-09-03 195529.png",  # Sample image from Cloudinary
            public_id=test_public_id,
            folder="sharebite/test",
            resource_type="image",
            timeout=30
        )
        
        print(f"   Upload successful!")
        print(f"   Public ID: {upload_result['public_id']}")
        print(f"   URL: {upload_result['secure_url']}")
        print(f"   Size: {upload_result.get('bytes', 0)} bytes")
        print(f"   Format: {upload_result.get('format', 'unknown')}")
        
        # Test 4: Generate transformation URLs
        print("\n4. Testing image transformations...")
        
        thumbnail_url = cloudinary.CloudinaryImage(upload_result['public_id']).build_url(
            width=300, height=200, crop="fill", quality="auto"
        )
        print(f"   Thumbnail URL: {thumbnail_url}")
        
        # Test 5: Clean up - delete the test image
        print("\n5. Cleaning up test image...")
        delete_result = cloudinary.uploader.destroy(upload_result['public_id'])
        if delete_result.get('result') == 'ok':
            print("   ✅ Test image deleted successfully")
        else:
            print(f"   ⚠️  Delete result: {delete_result.get('result', 'unknown')}")
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Cloudinary is working correctly.")
        print("=" * 50)
        return True
        
    except cloudinary.exceptions.Error as e:
        print(f"\n❌ Cloudinary Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

def test_local_file_upload():
    """Test uploading a local file (if you have one)"""
    print("\n" + "=" * 50)
    print("LOCAL FILE UPLOAD TEST")
    print("=" * 50)
    
    # You can replace this with the path to any image file on your computer
    test_file_path = input("Enter path to test image file (or press Enter to skip): ").strip()
    
    if not test_file_path:
        print("Skipping local file test.")
        return True
    
    if not os.path.exists(test_file_path):
        print(f"❌ File not found: {test_file_path}")
        return False
    
    try:
        print(f"Uploading file: {test_file_path}")
        
        # Get file size
        file_size = os.path.getsize(test_file_path)
        print(f"File size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
        
        # Upload the file
        test_public_id = f"local_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        upload_result = cloudinary.uploader.upload(
            test_file_path,
            public_id=test_public_id,
            folder="sharebite/test",
            resource_type="image",
            timeout=60,
            chunk_size=6000000
        )
        
        print(f"✅ Upload successful!")
        print(f"   Public ID: {upload_result['public_id']}")
        print(f"   URL: {upload_result['secure_url']}")
        print(f"   Original Size: {upload_result.get('bytes', 0)} bytes")
        print(f"   Format: {upload_result.get('format', 'unknown')}")
        print(f"   Dimensions: {upload_result.get('width', 0)} x {upload_result.get('height', 0)}")
        
        # Clean up
        print("Cleaning up test image...")
        delete_result = cloudinary.uploader.destroy(upload_result['public_id'])
        if delete_result.get('result') == 'ok':
            print("✅ Test image deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Local file upload error: {e}")
        return False

def main():
    """Run all tests"""
    print("Starting Cloudinary tests...\n")
    
    # Test 1: Basic connection
    connection_ok = test_cloudinary_connection()
    
    if not connection_ok:
        print("\n❌ Basic connection failed. Check your configuration.")
        return
    
    # Test 2: Local file upload (optional)
    test_local_file_upload()
    
    print("\n🎉 Cloudinary testing complete!")
    print("\nIf all tests passed, your Cloudinary integration should work in your main application.")

if __name__ == "__main__":
    main()