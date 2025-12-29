# Frontend for Self-Improving Prompt Optimization API

A simple, modern web interface for interacting with the Prompt Optimization API.

## Features

- **Prompt Management**: Create and view prompts
- **Inference**: Run prompts with custom variables
- **Evaluation**: Evaluate prompts on datasets
- **Self-Improvement**: Run automated prompt improvement
- **A/B Testing**: Select versions and view metrics

## Usage

1. Make sure the API server is running on `http://localhost:8000`

2. Open `index.html` in your web browser:
   ```bash
   # Option 1: Open directly
   open index.html
   
   # Option 2: Use a simple HTTP server (recommended)
   python3 -m http.server 3000
   # Then visit http://localhost:3000
   ```

3. Start using the interface!

## API Connection

The frontend is configured to connect to `http://localhost:8000` by default. To change this, edit the `API_BASE_URL` constant in `app.js`.

## Browser Compatibility

Works in all modern browsers (Chrome, Firefox, Safari, Edge).

## Notes

- CORS must be enabled on the API server (already configured)
- The API server must be running before using the frontend
- For production, consider using a proper build tool like Vite or Create React App

