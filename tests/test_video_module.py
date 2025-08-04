"""
Test the modular video streaming functionality.

This test verifies that the video module integrates correctly with the existing system
and provides the expected streaming capabilities.
"""

import asyncio
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


async def test_video_module_integration():
    """Test video module integration with the existing system"""
    print("\n🎬 Testing Video Module Integration...")
    
    try:
        # Import the necessary components
        from usda_vision_system.core.config import Config
        from usda_vision_system.storage.manager import StorageManager
        from usda_vision_system.core.state_manager import StateManager
        from usda_vision_system.video.integration import create_video_module
        
        print("✅ Successfully imported video module components")
        
        # Initialize core components
        config = Config()
        state_manager = StateManager()
        storage_manager = StorageManager(config, state_manager)
        
        print("✅ Core components initialized")
        
        # Create video module
        video_module = create_video_module(
            config=config,
            storage_manager=storage_manager,
            enable_caching=True,
            enable_conversion=False  # Disable conversion for testing
        )
        
        print("✅ Video module created successfully")
        
        # Test module status
        status = video_module.get_module_status()
        print(f"📊 Video module status: {status}")
        
        # Test video service
        videos = await video_module.video_service.get_all_videos(limit=5)
        print(f"📹 Found {len(videos)} video files")
        
        for video in videos[:3]:  # Show first 3 videos
            print(f"   - {video.file_id} ({video.camera_name}) - {video.file_size_bytes} bytes")
        
        # Test streaming service
        if videos:
            video_file = videos[0]
            streaming_info = await video_module.streaming_service.get_video_info(video_file.file_id)
            if streaming_info:
                print(f"🎯 Streaming test: {streaming_info.file_id} is streamable: {streaming_info.is_streamable}")
        
        # Test API routes creation
        api_routes = video_module.get_api_routes()
        admin_routes = video_module.get_admin_routes()
        
        print(f"🛣️  API routes created: {len(api_routes.routes)} routes")
        print(f"🔧 Admin routes created: {len(admin_routes.routes)} routes")
        
        # List some of the available routes
        print("📋 Available video endpoints:")
        for route in api_routes.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods) if route.methods else 'N/A'
                print(f"   {methods} {route.path}")
        
        # Cleanup
        await video_module.cleanup()
        print("✅ Video module cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Video module test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_video_streaming_endpoints():
    """Test video streaming endpoints with a mock FastAPI app"""
    print("\n🌐 Testing Video Streaming Endpoints...")
    
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from usda_vision_system.core.config import Config
        from usda_vision_system.storage.manager import StorageManager
        from usda_vision_system.core.state_manager import StateManager
        from usda_vision_system.video.integration import create_video_module
        
        # Create test app
        app = FastAPI()
        
        # Initialize components
        config = Config()
        state_manager = StateManager()
        storage_manager = StorageManager(config, state_manager)
        
        # Create video module
        video_module = create_video_module(
            config=config,
            storage_manager=storage_manager,
            enable_caching=True,
            enable_conversion=False
        )
        
        # Add video routes to test app
        video_routes = video_module.get_api_routes()
        admin_routes = video_module.get_admin_routes()
        
        app.include_router(video_routes)
        app.include_router(admin_routes)
        
        print("✅ Test FastAPI app created with video routes")
        
        # Create test client
        client = TestClient(app)
        
        # Test video list endpoint
        response = client.get("/videos/")
        print(f"📋 GET /videos/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Found {data.get('total_count', 0)} videos")
        
        # Test video module status (if we had added it to the routes)
        # This would be available in the main API server
        
        print("✅ Video streaming endpoints test completed")
        
        # Cleanup
        await video_module.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Video streaming endpoints test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all video module tests"""
    print("🚀 Starting Video Module Tests")
    print("=" * 50)
    
    # Test 1: Module Integration
    test1_success = await test_video_module_integration()
    
    # Test 2: Streaming Endpoints
    test2_success = await test_video_streaming_endpoints()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Module Integration: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Streaming Endpoints: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if test1_success and test2_success:
        print("\n🎉 All video module tests passed!")
        print("\n📖 Next Steps:")
        print("   1. Restart the usda-vision-camera service")
        print("   2. Test video streaming in your React app")
        print("   3. Use endpoints like: GET /videos/ and GET /videos/{file_id}/stream")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return test1_success and test2_success


if __name__ == "__main__":
    asyncio.run(main())
