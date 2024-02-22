import dash
from dash import html
from dash.dependencies import Input, Output, State
from dash_recording_components import AudioRecorder
import soundfile as sf
import dash_bootstrap_components as dbc
import io
import requests
import base64
import numpy as np
import wave

app = dash.Dash(__name__)

server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Row([dbc.Card(
            dbc.CardBody([
                html.P(["Researcher's Transcriptions Tool"],
                       style={'font-family': 'cursive', 'text-decoration': 'underline',
                              'text-align': 'center', 'color': '2px solid black', 'fontSize': 10}),
                html.Br(),
                dbc.CardImg(src="/assets/logoA.png", top=True, style={"width": "100%", "height": "100%"}, )]
            ),
            style={"width": "10rem", "margin": "0 auto", "border": "2px solid green"}
        )], style={
            "margin": "20px",
            "text-align": "center"}, justify="center"),

        html.Br(style={
            "border": "1px solid purple"
        }),
        dbc.Row([
            dbc.Button("Record", id="record-button", style={"background-color": "#ccffee", "margin": "10px"}),

            dbc.Button("Stop Recording", id="stop-button", n_clicks=0,
                       style={"background-color": "#ffb3b3", "margin": "10px"}),

            dbc.Button("Play", id="play-button", style={"background-color": "#00cc44", "margin": "10px"})

        ], style={"margin": "20px", "text-align": "center", "padding": "10px"}),

        dbc.Row(id="audio-output", style={
            "margin": "10px",
            "text-align": "center",
        }, justify="center"),

        html.P(id="live-update-text", style={
            "margin": "20px",
            "border": "1px solid green",
            "text-align": "center",
        }),
        html.Br(style={
            "border": "1px solid purple"
        }),
        html.Div(id="dummy-output", style={"display": "none", "margin": "10px",
                                           "border": "1px solid green"}),
        html.Br(style={
            "border": "1px solid purple"
        }),
        AudioRecorder(id="audio-recorder")
    ], justify="center")
], style={"margin": "20px"}, className="container-fluid")

audio_samples = []


def convert_wav_flac(audio):
    data, samplerate = sf.read(audio)
    flac = sf.write('output.flac', data, samplerate)
    return flac


@app.callback(
    Output("audio-recorder", "recording"),
    Input("record-button", "n_clicks"),
    Input("stop-button", "n_clicks"),
    State("audio-recorder", "recording"),
    prevent_initial_call=True
)
def control_recording(record_clicks, stop_clicks, recording):
    return record_clicks > stop_clicks


@app.callback(
    Output("audio-output", "children"),
    Output("live-update-text", "children"),
    Input("play-button", "n_clicks"),
    prevent_initial_call=True
)
def play_audio(play_clicks):
    if play_clicks:

        if audio_samples:
            audio_array = np.array(audio_samples)

            with io.BytesIO() as wav_buffer:
                sf.write(wav_buffer, audio_array, 16000, format="WAV")
                wav_bytes = wav_buffer.getvalue()
                wav_base64 = base64.b64encode(wav_bytes).decode()
                audio_src = f"data:audio/wav;base64,{wav_base64}"

                wavFile = "output.wav"

                # Your bytearray data
                bytearray_data = bytearray(audio_array)

                # Open a .wav file in write binary mode
                with wave.open(wavFile, 'wb') as wf:
                    # Set audio parameters
                    wf.setnchannels(1)  # mono
                    wf.setsampwidth(2)  # number of bytes
                    wf.setframerate(16000)  # sample rate

                    # Write frames to .wav file
                    wf.writeframes(bytearray_data)

                convert_wav_flac(wavFile)

                flacFile = "output.flac"

                API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
                headers = {"Authorization": "Bearer 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"}

                def query(filename):
                    with open(filename, "rb") as f:
                        info = f.read()
                    response = requests.post(API_URL, headers=headers, data=info)
                    return response.json()

                sentence = query(flacFile)["text"]

                print(sentence)

                return html.Audio(src=audio_src, controls=True, autoPlay=True, style={
                    "margin": "30px", "text-align": "center",
                }), sentence
    return ""


@app.callback(
    Output("dummy-output", "children"),
    Input("audio-recorder", "audio"),
    prevent_initial_call=True
)
def update_audio(audio):
    # running list of the audio samples, aggregated on the server
    global audio_samples
    if audio is not None:
        # Update the audio samples with the new audio
        audio_samples += list(audio.values())
    return ""


if __name__ == "__main__":
    app.run_server(debug=True, port=5979)
