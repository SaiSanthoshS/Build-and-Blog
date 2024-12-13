from flask import Flask, render_template, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, storage
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import sounddevice as sd
from scipy.io.wavfile import write
import smtplib
# MIMEMultipart send emails with both text content and attachments.
from email.mime.multipart import MIMEMultipart
# MIMEText for creating body of the email message.
from email.mime.text import MIMEText
# MIMEApplication attaching application-specific data (like CSV files) to email messages.
from email.mime.application import MIMEApplication
import time
import pathlib
import firebase_admin

load_dotenv()
api_key = os.getenv('API_KEY')
firebase_project_id = os.getenv('firebase_project_id')

# Initialize Flask app
app = Flask(__name__)

# Set up Firebase credentials
cred = credentials.Certificate("firebase_creds.json")
firebase_admin.initialize_app(cred, {
            'projectId': firebase_project_id,
            'storageBucket': firebase_project_id
        })
db = firestore.client()

# Load environment variables


@app.route('/')
def index():
    if not api_key:
        raise ValueError("API_KEY not found in environment variables")

    genai.configure(api_key=api_key)
    print("API key loaded and GenAI configured successfully!")

    model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

    response = model.generate_content(
        '''Assume a child is in risk, we are generating a SOS alert which is triggered by unique sentences, So I want you to think of 5 example scenarios(include them being in school, on the way to home and home only) and frame random keywords(keep it to two easy random words, avoid using colours, unrelated words would be nice) which will be easier for a child to remember.
        The response should be strictly of a dictionary. Do not include anything else in the response
        Example: ```json{{keyword: scenario, keyword: scenario}}``` strcictly stick to this format'''
    )

    print(response.text)
    json_text = response.text.split("json", 1)[1].strip()
    print(json_text)

    cleaned_response = json_text.rstrip("`")
    data = json.loads(cleaned_response)

    return render_template('index.html', data=data)

@app.route('/save', methods=['POST'])
def save():
    request_data = request.json  # Get data sent from the frontend
    child_name = request_data.get("child_name")  # Ensure child_name is provided
    if not child_name:
        return jsonify({"message": "Child name is required!"}), 400

    # Check if the child already exists in the database
    child_ref = db.collection('allchildData').document(child_name)
    if child_ref.get().exists:
        return jsonify({"message": "Child name already exists. Please choose a unique name!"}), 400

    # Prepare data to save
    keywords_data = request_data.get("sos_keywords", {})
    formatted_keywords = {
        "SOSkeywords": {
            keyword: {
                "description": data["description"],
                "contacts": data.get("contacts", [])
            }
            for keyword, data in keywords_data.items()
        }
    }

    # Save the data
    child_ref.set({
        "name": child_name,
        "age": request_data.get("age", "Unknown"),
        "contact1": request_data.get("contact1", ""),
        "contact2": request_data.get("contact2", ""),
        **formatted_keywords
    })

    return jsonify({"message": f"Data for {child_name} saved successfully!"})

@app.route('/user/<child_name>')
def user(child_name):
    # Fetch user data from Firestore
    child_ref = db.collection('allchildData').document(child_name)
    child_doc = child_ref.get()

    if not child_doc.exists:
        return jsonify({"message": f"Child {child_name} not found!"}), 404

    child_data = child_doc.to_dict()

    # Format SOS keywords with description and contacts
    sos_keywords = []
    if 'SOSkeywords' in child_data:
        for keyword, details in child_data['SOSkeywords'].items():
            sos_keywords.append({
                'keyword': keyword,
                'description': details['description'],
                'contacts': details.get('contacts', [])
            })

    return render_template('display.html', child_data=child_data, sos_keywords=sos_keywords)

@app.route('/start_recording/<child_name>', methods=['POST'])
def start_recording(child_name):
    try:
        # Set the audio recording parameters
        sd.default.device = 'MacBook Pro Microphone'  # Replace with the correct microphone name
        fs = 16000  # Sampling frequency
        seconds = 30  # Duration of recording in seconds

        print(f"Recording for child {child_name}...")
        audio_data = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is complete
        print("Recording complete.")

        # Save the audio data as a .wav file
        filename = f"output_{child_name}.wav"
        write(filename, fs, audio_data)
        print(f"Saved recording as {filename}.")

        return jsonify({"message": "Recording saved successfully!"}), 200
    except Exception as e:
        print(f"Error while recording: {e}")
        return jsonify({"message": "Error while recording audio."}), 500
    

@app.route('/trigger_sos_action', methods=['POST'])
def trigger_sos_action():
    data = request.get_json()
    keyword = data.get('keyword')
    child_name = data.get('child_name')

    # Fetch associated emails from Firestore
    db = firestore.client()
    sos_ref = db.collection('allchildData').document(child_name)
    print(sos_ref)
    sos_data = sos_ref.get().to_dict()
    print(sos_data['SOSkeywords'][keyword])

    if not sos_data or 'contacts' not in sos_data['SOSkeywords'][keyword]:
        return jsonify({"message": f"No contacts found for keyword: {keyword}"}), 404

    recipient_emails = sos_data['SOSkeywords'][keyword]['contacts']  # List of emails from Firestore

    # Email Details
    subject = f"{keyword} Alert Trigerred by {child_name}!!!!!!!!"
    body = f'''An SOS keyword '{keyword}' has been triggered by {child_name}. Please check on them.
    Please wait for sometime for the detailed report.'''
    sender_email = "sssanthosh.cse@gmail.com"
    sender_password = "ehih qlzx xfan dvoy"
    smtp_server = 'smtp.gmail.com'
    smtp_port = 465

    # Send email to all recipients
    for email in recipient_emails:
        try:
            message = MIMEMultipart()
            message['Subject'] = subject
            message['From'] = sender_email
            message['To'] = email
            body_part = MIMEText(body, 'plain')
            message.attach(body_part)

            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, message.as_string())

            print(f"Email sent to {email}")
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

    audio_filename = f"output_{child_name}.wav"
    
    # Check if the file exists, if not, wait
    while not os.path.exists(audio_filename):
        print(f"Audio file for {child_name} not available yet. Waiting...")
        time.sleep(10)  # Wait for 5 seconds before checking again
    
    # Once the audio file is available, process it
    try:
        analysis_results = analyze_audio(audio_filename)
        # Access the storage bucket
        bucket = storage.bucket()
        fileName = audio_filename
        blob = bucket.blob(f"{keyword}_{fileName}")
        blob.upload_from_filename(fileName)

        # Optional: Make the file public
        blob.make_public()
        print("Your file URL:", blob.public_url)

        os.remove(audio_filename)

    #     db = firestore.client()

    #     child_ref = db.collection('allchildData').document(child_name)

    #     print(child_ref)

    #     incident = {
    #     f"{keyword}_{child_name}": {
    #         "audio_url" : blob.public_url,
    #         "child_voice_tone" : analysis_results["tone"],
    #         "audio_transcription": analysis_results["audio"],
    #         "GenAIsummary": analysis_results["summary"]
    #     }
    # }
        
    #     child_ref.update({
    #     **incident
    # })
        
        subject = f"Detailed Report for {keyword} alert Trigerred by {child_name}"
        body = f'''Please view the detailed report:
        Audio of child recorded for 30s: {blob.public_url}
        The tone of child in Audio(Generated by Gemini): {analysis_results["tone"]},
        audio_transcription: {analysis_results["audio"]},
        Inference from the Audio (Generated by Gemini): {analysis_results["summary"]}'''

        # Send email to all recipients
        for email in recipient_emails:
            try:
                message = MIMEMultipart()
                message['Subject'] = subject
                message['From'] = sender_email
                message['To'] = email
                body_part = MIMEText(body, 'plain')
                message.attach(body_part)

                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, email, message.as_string())

                print(f"Email sent to {email}")
            except Exception as e:
                print(f"Failed to send email to {email}: {e}")
        


    except Exception as e:
        return jsonify({"message": f"Error during audio analysis: {str(e)}"}), 500

    return jsonify({
        "message": f"SOS emails sent for {child_name} with keyword: {keyword}",
        "recipients": recipient_emails,
        "audio_analysis": analysis_results
    })

def analyze_audio(filename):
    """
    Analyze the recorded audio file using Gemini for summarization.
    """
    print(f"Analyzing audio file: {filename}")

    # Create the prompt for Gemini
    prompt = '''This ouput should be of a json format. 
    ```json{{audio: Generate what is being exactly spoken - only give that as output, 
    summary: this is a very crucial audio recording - look out for background noise - tone of the voice and make sense of what is being spoken,
    tone: give one word for the tone of the voice in the audio}}```
    Remember to strictly stick to the above json format'''

    # Load the audio file into a Python Blob object containing the audio file's bytes
    audio_data = pathlib.Path(filename).read_bytes()

    # Initialize the Gemini model
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash-exp')

    # Pass the prompt and the audio to Gemini for analysis
    response = model.generate_content([
        prompt,
        {
            "mime_type": "audio/wav",
            "data": audio_data
        }
    ])

    # Output Gemini's response to the prompt
    print("Gemini's response:", response.text)
    json_text = response.text.split("json", 1)[1].strip()
    print(json_text)

    cleaned_response = json_text.rstrip("`")
    data = json.loads(cleaned_response)
    return data



if __name__ == '__main__':
    app.run(debug=True)
