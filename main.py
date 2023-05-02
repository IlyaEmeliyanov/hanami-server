import uvicorn # for startint the ASGI server

def main():
    try:
        config = uvicorn.Config("wa.webapi:app", port=5500, log_level="info", reload=True)
        server = uvicorn.Server(config)
        server.run()
    except Exception as exception:
        print(f"\n[❌] Exception caught in main.py: {exception}")
    finally:
        print("\n[❗️] Process terminated")

if __name__ == "__main__":
    main()
