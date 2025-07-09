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

// Microphone waveform visualization
async function startMicrophoneVisualization() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 2048;
    const bufferLength = analyser.fftSize;
    const dataArray = new Uint8Array(bufferLength);

    source.connect(analyser);

    function draw() {
        requestAnimationFrame(draw);
        analyser.getByteTimeDomainData(dataArray);

        ctx.fillStyle = "#F0F4F8";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#007acc";
        ctx.beginPath();

        const sliceWidth = canvas.width * 1.0 / bufferLength;
        let x = 0;
        for (let i = 0; i < bufferLength; i++) {
            const v = dataArray[i] / 128.0;
            const y = v * canvas.height / 2;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            x += sliceWidth;
        }
        ctx.lineTo(canvas.width, canvas.height / 2);
        ctx.stroke();
    }

    draw();
}


