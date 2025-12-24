import uvicorn
import asyncio

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🧠 PHENOM AI - Web Interface")
    print("="*70)
    print("\n📡 Starting web server...")
    print("🌐 Access the UI at: http://localhost:8000")
    print("📱 Login or register to get started")
    print("\n💡 Press CTRL+C to stop the server\n")
    print("="*70 + "\n")
    
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
        loop="asyncio"
    )
