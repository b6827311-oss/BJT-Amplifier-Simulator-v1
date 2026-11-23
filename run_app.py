"""One-command entry point used by run.ps1 and the portable run.bat.

Keeping this as a real file avoids quoting a ``python -c`` string in scripts
and makes the Flask app easy to launch from any working directory.
"""

from app import app

HOST = "127.0.0.1"
PORT = 5000


if __name__ == "__main__":
    print(f"BJT Amplifier Simulator -> http://{HOST}:{PORT}/simulator")
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
