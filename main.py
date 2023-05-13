import uvicorn # for startint the ASGI server
from threading import Thread
import subprocess

# def run_server():
#     subprocess.Popen("uvicorn wa.webapi:app --port 5500")
    
def main():
    try:
        config = uvicorn.Config("wa.webapi:app", port=5500, log_level="info")
        server = uvicorn.Server(config)
        server.run()
    except Exception as exception:
        print(f"\n[❌] Exception caught in main.py: {exception}")
    finally:
        print("\n[❗️] Process terminated")

if __name__ == "__main__":
    main()
