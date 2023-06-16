import os
import uuid
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech, BatchRecognizeFileMetadata, GcsOutputConfig
from google.api_core.client_options import ClientOptions
from google.api_core.exceptions import AlreadyExists

import firebase_admin
from firebase_admin import firestore
from firebase_admin import storage

app = firebase_admin.initialize_app()
db = firestore.client()

def transcribe(
    project_id: str,
    recognizer_id: str,
    gcs_uri: str,
    gcs_uri_output: str,
):
    options = ClientOptions(api_endpoint="us-central1-speech.googleapis.com:443")
    client = SpeechClient(client_options=options)

    request = cloud_speech.CreateRecognizerRequest(
        parent=f"projects/{project_id}/locations/us-central1",
        recognizer_id=recognizer_id,
        recognizer=cloud_speech.Recognizer(
            language_codes=["en-US"], model="chirp"
        ),
    )

    try:
        operation = client.create_recognizer(request=request)
        recognizer = operation.result()
    except AlreadyExists:
        recognizer = client.get_recognizer(
            name=f"projects/{project_id}/locations/us-central1/recognizers/{recognizer_id}"
        )

    config = cloud_speech.RecognitionConfig(auto_decoding_config={})

    gcs_output_config = GcsOutputConfig(uri=gcs_uri_output)
    recognition_output_config = cloud_speech.RecognitionOutputConfig(gcs_output_config=gcs_output_config)
    request = cloud_speech.BatchRecognizeRequest(
        recognizer=recognizer.name,
        config=config,
        files=[BatchRecognizeFileMetadata(uri=gcs_uri)],
        recognition_output_config=recognition_output_config
    )

    operation = client.batch_recognize(request=request)
    print("operation.done: ", operation.done())


def handler(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    if event['name'].startswith('audios/'):
        gcs_uri = f"gs://{event['bucket']}/{event['name']}"
        gcs_uri_output = f"gs://{event['bucket']}/output"
        project_id = os.environ.get('GCP_PROJECT')
        recognizer_id = "chirprecognizer"
        transcribe(project_id, recognizer_id, gcs_uri, gcs_uri_output)

    if event['name'].startswith('output/'):
        transcription_file = event['name']
        bucket = storage.bucket(event['bucket'])
        blob = bucket.blob(transcription_file)
        blob.make_public()

        transcription_id = f"{uuid.uuid4()}"
        transcription_doc_ref = db.collection('transcriptions').document(transcription_id)
        url = f"https://storage.googleapis.com/{event['bucket']}/{event['name']}"
        transcription_doc_ref.set({
            'name': event['name'],
            'url': url
        })

