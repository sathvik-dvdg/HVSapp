# app/api/v1/handoff_ws.py
@router.websocket("/ws/dictation/{encounter_id}")
async def dictation_websocket(websocket: WebSocket, encounter_id: int):
    # 1. Auth via initial WS message (NOT query params)
    await websocket.accept()
    auth_msg = await websocket.receive_json()
    user = verify_token_securely(auth_msg["token"]) # Do not hit DB!
    
    # 2. Open Deepgram Connection
    dg_socket = await connect_to_deepgram_medical_model()
    
    async def listen_to_mobile():
        while True:
            data = await websocket.receive_bytes() # Send raw bytes, avoid base64 overhead
            await dg_socket.send(data)

    async def listen_to_deepgram():
        while True:
            transcript = await dg_socket.receive()
            if transcript.is_final:
                await websocket.send_json({"text": transcript.text, "is_final": True})
                # Trigger Background Task for NLP Validation on sentence end
                asyncio.create_task(validation_engine.process_sentence(transcript.text, encounter_id))

    await asyncio.gather(listen_to_mobile(), listen_to_deepgram())