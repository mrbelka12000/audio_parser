import assemblyai as aai
import config

aai.settings.api_key = config.assembly_key
config = aai.TranscriptionConfig(
    language_code="ru"
)

transcriber = aai.Transcriber(config=config)

def get_transcript(file_name):

    transcript = transcriber.transcribe(file_name)

    return transcript.text
