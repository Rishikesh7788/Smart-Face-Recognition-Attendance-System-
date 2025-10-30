# ML Internship Project — Repository

This repository contains the project files you uploaded and is prepared for a GitHub upload.

## Included files
- .gitignore
- app.py
- attanance.py
- attendance.db
- firebase_config.py
- main.py
- requirements.txt

## Setup instructions

1. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- If your `firebase_config.py` uses sensitive keys, move them to environment variables or a `.env` file (and add `.env` to .gitignore).
- If the project expects `attendance.db`, it's included but you may want to recreate or replace it with a clean DB.

4. Run the app (example):
```bash
python app.py
# or
python main.py
```

## Notes
- Database files (`*.db`) are included for convenience. Remove them before sharing publicly if they contain sensitive data.
- Make sure to **remove API keys and secrets** from `firebase_config.py` before pushing to a public repository.

## License
This repository template includes an MIT license (see LICENSE).