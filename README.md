# Medical Flutter App

A Clinical Decision Support System combining Flutter web frontend with FastAPI backend for processing medical reports.

## Features

- PDF upload and processing
- AI-powered medical report analysis
- Multi-language support (8 Indian languages)
- Text-to-speech functionality
- Modern Material 3 UI
- Real-time processing pipeline

## Setup

1. Ensure you have Flutter SDK and Python 3.13 installed
2. Install dependencies:
   - Run "Install Flutter Dependencies" task
   - Run "Install Python Dependencies" task

## Running the Application

### Option 1: Using VS Code Tasks (Recommended)

1. Open the project in VS Code
2. Press `Ctrl+Shift+P` and select "Tasks: Run Task"
3. Run "Start Backend Server" task
4. Run "Start Flutter Web App" task
5. The Flutter app will open in Chrome at http://localhost:3000
6. Backend will be running at http://127.0.0.1:8000

### Option 2: Using VS Code Debug

1. Press `F5` or go to Run & Debug panel
2. Select "Launch Both Services" configuration
3. This will start both backend and frontend in debug mode

### Option 3: Manual Commands

```bash
# Terminal 1 - Start Backend
cd backend
python main.py

# Terminal 2 - Start Frontend
cd flutter_app
flutter run -d chrome --web-port=3000
```

## Testing

- Run "Test Backend Health" task to verify backend is running
- Upload a PDF through the Flutter web app
- Check browser console and VS Code debug console for any errors

## Project Structure

```
Medical Flutter App/
├── backend/           # FastAPI backend
│   ├── main.py       # Main server file
│   ├── agents.py     # AI processing agents
│   └── requirements.txt
├── flutter_app/       # Flutter frontend
│   ├── lib/
│   │   └── main.dart # Main app file
│   └── pubspec.yaml
└── .vscode/           # VS Code configurations
    ├── tasks.json    # Build and run tasks
    ├── launch.json   # Debug configurations
    └── settings.json # Workspace settings
```

## API Endpoints

- `GET /health` - Health check
- `POST /upload/` - Upload and process PDF (fields: file, language)

## Troubleshooting

- If backend fails to start, check Python dependencies
- If Flutter fails, ensure Flutter SDK is in PATH
- For web issues, clear browser cache and try incognito mode
- Check VS Code terminal output for detailed error messages