from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import asyncio
import anthropic
import base64

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Anthropic client
client = anthropic.Anthropic()

# In-memory buffer to store audio context (replace with a proper queue in production)
audio_buffer = []


class Question(BaseModel):
    text: str


@app.post("/question")
async def answer_question(question: Question):
    try:
        # Combine question with audio context
        # Use last 10 audio transcriptions as context
        context = "\n".join(audio_buffer[-10:])

        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0,
            system="You are a helpful AI assistant for a lecture buddy application. Use the provided context to answer questions about the lecture.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Context from the lecture:\n{context}\n\nQuestion: {question.text}"
                        }
                    ]
                }
            ]
        )

        return {"answer": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            # Process the audio data (e.g., transcribe it)
            # For now, we'll just add it to the buffer as base64 encoded string
            encoded_data = base64.b64encode(data).decode('utf-8')
            audio_buffer.append(encoded_data)
            if len(audio_buffer) > 100:  # Keep only last 100 entries
                audio_buffer.pop(0)
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
