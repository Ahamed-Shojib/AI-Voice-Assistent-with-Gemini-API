function updateStatus(message) {
        document.getElementById("statusText").textContent = `Status: ${message}`;
        }

        let ws;
        const canvas = document.getElementById("waveform");
        const ctx = canvas.getContext("2d");
        const transcriptionEl = document.getElementById("transcription");

        async function startAssistant() {
            const res = await fetch("/start", { method: "POST" });
            startWebSocket();
            startMicrophoneVisualization();
            const data = await res.json();
            //alert(data.status);
            updateStatus("Starting...");
            // ...existing code
            updateStatus("Listening...");
        }

        async function stopAssistant() {
            const res = await fetch("/stop", { method: "POST" });
            const data = await res.json();
            //alert(data.status);
            updateStatus("Stopping...");
            // ...existing code
            updateStatus("Stopped");
            if (ws) ws.close();
        }

        function startWebSocket() {
            ws = new WebSocket("ws://" + location.host + "/ws/transcription");
            ws.onmessage = (event) => {
                transcriptionEl.textContent += event.data + " ";
            };
            ws.onclose = () => {
                console.log("WebSocket closed");
            };
        }

        
