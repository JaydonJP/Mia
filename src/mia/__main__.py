import sys
from .app import MiaApp

def main():
    print("Mia starting...")
    app = MiaApp()
    app.run()

if __name__ == "__main__":
    main()
