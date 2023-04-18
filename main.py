

from wa.webapi import Server

def main():
    server = Server()
    try:
        server.run()
    except Exception as exception:
        print(f"\n[❌] Exception caught in main.py: {exception}")
    finally:
        print("\n[❗️] Process terminated")
    

if __name__ == "__main__":
    main()
