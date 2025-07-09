# assistant.py

import os
import asyncio
import base64
import io
import traceback

import pyaudio
from google import genai
from google.genai import types

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-preview-native-audio-dialog"

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key= "", # Set API key here
)

CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,
        sliding_window=types.SlidingWindow(target_tokens=12800),
    ),
)

pya = pyaudio.PyAudio()


class AudioOnlyLoop:
    def __init__(self):
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None

    async def send_text(self):
        while True:
            text = await asyncio.to_thread(input, "message > ")
            if text.lower() == "q":
                break
            await self.session.send(input=text or ".", end_of_turn=True)

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        while True:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, exception_on_overflow=False)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    # async def receive_audio(self):
    #     while True:
    #         turn = self.session.receive()
    #         async for response in turn:
    #             if data := response.data:
    #                 self.audio_in_queue.put_nowait(data)
    #             if text := response.text:
    #                 print(text, end="")
    #         while not self.audio_in_queue.empty():
    #             self.audio_in_queue.get_nowait()

    async def receive_audio(self, transcription_queue):
        while True:
            turn = self.session.receive()
            async for response in turn:
                if data := response.data:
                    self.audio_in_queue.put_nowait(data)
                if text := response.text:
                    await transcription_queue.put(text)  # Push to WebSocket
                    print(text, end="")
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    # async def run(self):
    #     try:
    #         async with (
    #             client.aio.live.connect(model=MODEL, config=CONFIG) as session,
    #             asyncio.TaskGroup() as tg,
    #         ):
    #             self.session = session
    #             self.audio_in_queue = asyncio.Queue()
    #             self.out_queue = asyncio.Queue(maxsize=5)

    #             tg.create_task(self.send_text())
    #             tg.create_task(self.send_realtime())
    #             tg.create_task(self.listen_audio())
    #             tg.create_task(self.receive_audio())
    #             tg.create_task(self.play_audio())
    #     except asyncio.CancelledError:
    #         pass
    #     except ExceptionGroup as EG:
    #         self.audio_stream.close()
    #         traceback.print_exception(EG)

    # In assistant.py — update receive_audio()

    async def run(self, transcription_queue):
        try:
            async with (
                client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_text())
                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                tg.create_task(self.receive_audio(transcription_queue))
                tg.create_task(self.play_audio())
        except asyncio.CancelledError:
            pass
        # except ExceptionGroup as EG:
        #     self.audio_stream.close()
        #     traceback.print_exception(EG)

