const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const typing = document.getElementById("typing");

function addMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message");

    if (sender === "user") {
        messageDiv.classList.add("user-message");
        messageDiv.innerHTML = `
            <div class="bubble">
                <strong>You</strong>
                <p>${escapeHtml(message)}</p>
            </div>
            <div class="avatar">👤</div>
        `;
    } else {
        messageDiv.classList.add("bot-message");
        messageDiv.innerHTML = `
            <div class="avatar">🤖</div>
            <div class="bubble">
                <strong>FitnessAI</strong>
                <p>${escapeHtml(message)}</p>
            </div>
        `;
    }

    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const message = messageInput.value.trim();

    if (!message) return;

    addMessage(message, "user");
    messageInput.value = "";
    sendButton.disabled = true;
    typing.style.display = "block";

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({message: message})
        });

        const data = await response.json();

        addMessage(
            data.reply || "Sorry, I couldn't generate a response.",
            "bot"
        );
    } catch (error) {
        console.error(error);
        addMessage(
            "Unable to connect to the server. Please try again.",
            "bot"
        );
    } finally {
        typing.style.display = "none";
        sendButton.disabled = false;
        messageInput.focus();
    }
}

sendButton.addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

messageInput.focus();
