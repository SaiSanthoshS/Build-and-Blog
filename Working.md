# SOS Alert System - README

## Overview
This project is a Flask-based application designed to assist in emergency situations by:
- Generating SOS alerts using keywords associated with predefined scenarios.
- Recording audio as part of the alert process.
- Sending SOS emails to emergency contacts.
- Analyzing recorded audio for tone and transcription using AI models.
- Storing and managing child-specific emergency data in Firebase.

## Features
1. **Dynamic SOS Keywords:** Generates SOS keywords using AI to ensure children can easily remember them.
2. **Audio Recording:** Captures audio recordings during emergencies.
3. **Email Alerts:** Sends detailed SOS alerts with analysis reports to predefined contacts.
4. **Audio Analysis:** Uses an AI model to transcribe, summarize, and analyze tone from recorded audio.
5. **Data Storage:** Stores child-specific data and SOS keywords in Firebase Firestore.

## Requirements
### Software
- Python 3.9+
- Flask
- Firebase Admin SDK
- Google Generative AI (Gemini model)
- SoundDevice
- SciPy
- Email libraries (smtplib, email.mime)

### Hardware
- A microphone-enabled system for audio recording.

### API Keys & Credentials
- Firebase credentials (`firebase_creds.json`).
- Google Generative AI API Key.
- Email account credentials (for sending alerts).

### Environment Variables
Create a `.env` file with the following variables:
```
API_KEY=your_genai_api_key
firebase_project_id=your_firebase_project_id
sender_mail=your_email@example.com
sender_pwd=your_email_password
```

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Add your Firebase credentials file (`firebase_creds.json`) to the project root.

4. Set up environment variables in the `.env` file.

## Usage

### Running the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Access the application in your browser at `http://127.0.0.1:5000/`.

### Endpoints
#### Home
- **`/`**: Displays the generated SOS keywords and their associated scenarios.

#### Save Child Data
- **`POST /save`**
  - Saves child-specific data along with SOS keywords.
  - **Request Body:**
    ```json
    {
      "child_name": "John",
      "age": "10",
      "contact1": "parent@example.com",
      "contact2": "guardian@example.com",
      "sos_keywords": {
        "keyword1": {
          "description": "scenario",
          "contacts": ["contact1@example.com"]
        }
      }
    }
    ```

#### Fetch Child Data
- **`GET /user/<child_name>`**
  - Retrieves stored data for a specific child.

#### Start Recording
- **`POST /start_recording/<child_name>`**
  - Records a 30-second audio clip associated with a child's SOS alert.

#### Trigger SOS Action
- **`POST /trigger_sos_action`**
  - Triggers an SOS alert by sending emails to emergency contacts and attaching analyzed audio data.
  - **Request Body:**
    ```json
    {
      "child_name": "John",
      "keyword": "keyword1"
    }
    ```

### Audio Analysis
- **`analyze_audio(filename)`**:
  - Analyzes recorded audio for transcription, tone, and a summarized inference.

## Firebase Configuration
Ensure Firebase is set up with:
- A Firestore database.
- Storage for saving and retrieving audio files.

## AI Integration
Uses Google Generative AI's Gemini model for:
- Generating SOS keywords.
- Analyzing audio files.

## Deployment
To deploy this application, consider hosting platforms like Heroku, AWS, or Google Cloud. Ensure you configure environment variables and Firebase settings on the deployment platform.

## Limitations
1. Requires an active internet connection for AI and email services.
2. Dependent on accurate configuration of environment variables and Firebase credentials.

## Future Enhancements
- Add mobile notifications for SOS alerts.
- Implement real-time transcription of audio recordings.
- Extend to include multiple languages for SOS keywords and alerts.

## Contact
For queries or contributions, please contact:
- **Email:** [sssanthosh.cse@example.com]
- **Linkedin:** [https://www.linkedin.com/in/sai-santhosh-s/]


