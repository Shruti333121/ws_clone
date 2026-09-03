let socket = null;
let currentRoom = null;
let typingTimeout = null;
let typingIndicatorTimeout = null;


// =========================
// CONNECT WEBSOCKET
// =========================
function connectWebSocket(roomId) {

    // Close old socket
    if (socket) {
        socket.close();
    }

    const protocol =
        window.location.protocol === "https:"
            ? "wss"
            : "ws";

    socket = new WebSocket(
        `${protocol}://${window.location.host}/ws/${roomId}`
    );

    socket.onopen = () => {

        console.log("✅ WebSocket connected");

        document.getElementById(
            "onlineBadge"
        ).innerHTML =
            "🟢 Online";
    };

    socket.onmessage = (event) => {

        console.log(
            "📩 Message received:",
            event.data
        );

        const data =
            JSON.parse(event.data);

        handleIncoming(data);
    };

    socket.onclose = () => {

        console.log("❌ WebSocket disconnected");

        document.getElementById(
            "onlineBadge"
        ).innerHTML =
            "🔴 Offline";
    };

    socket.onerror = (error) => {

        console.log(
            "❌ WebSocket error:",
            error
        );
    };
}


// =========================
// ROUTE INCOMING WS MESSAGES
// =========================
function handleIncoming(data) {

    if (data.type === "system") {
        appendSystemMessage(data.message);
        updateOnlineBadge(data.online);
        return;
    }

    if (data.type === "typing") {
        showTypingIndicator(data.username);
        return;
    }

    // default: chat message
    appendMessage(data);
}


// =========================
// SYSTEM MESSAGE (join/leave)
// =========================
function appendSystemMessage(text) {

    const messagesContainer =
        document.getElementById("messagesContainer");

    const el = document.createElement("div");
    el.className = "system-msg";
    el.innerText = text;

    messagesContainer.appendChild(el);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}


// =========================
// ONLINE COUNT BADGE
// =========================
function updateOnlineBadge(count) {

    if (count === undefined) return;

    document.getElementById("onlineBadge").innerHTML =
        `🟢 ${count} online`;
}


// =========================
// TYPING INDICATOR (incoming)
// =========================
function showTypingIndicator(username) {

    let el = document.getElementById("typingIndicator");
    const messagesContainer =
        document.getElementById("messagesContainer");

    if (!el) {
        el = document.createElement("div");
        el.id = "typingIndicator";
        el.className = "typing-indicator";
        messagesContainer.appendChild(el);
    }

    el.innerHTML =
        `${escapeHTML(username)} is typing<span class="typing-dots"><span></span><span></span><span></span></span>`;

    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    clearTimeout(typingIndicatorTimeout);
    typingIndicatorTimeout = setTimeout(() => {
        if (el) el.remove();
    }, 2000);
}


// =========================
// TYPING INDICATOR (outgoing)
// =========================
function notifyTyping() {

    if (!socket || socket.readyState !== WebSocket.OPEN) {
        return;
    }

    if (typingTimeout) {
        return; // already told the server recently, throttle it
    }

    socket.send(JSON.stringify({ type: "typing" }));

    typingTimeout = setTimeout(() => {
        typingTimeout = null;
    }, 1500);
}


// =========================
// APPEND MESSAGE
// =========================
function appendMessage(data) {

    const messagesContainer =
        document.getElementById(
            "messagesContainer"
        );

    const wrapper =
        document.createElement("div");

    const isOwnMessage =
        data.username ===
        CURRENT_USER.username;

    wrapper.className =
        `message-wrapper ${
            isOwnMessage
                ? "sent"
                : "received"
        }`;

    const time =
        new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit"
        });

    wrapper.innerHTML = `
        ${
            !isOwnMessage
                ? `
                <div class="msg-sender-name">
                    ${escapeHTML(data.username)}
                </div>
                `
                : ""
        }

        <div class="msg-bubble">
            ${escapeHTML(data.content)}
        </div>

        <div class="msg-time">
            ${time}
        </div>
    `;

    messagesContainer.appendChild(
        wrapper
    );

    messagesContainer.scrollTop =
        messagesContainer.scrollHeight;
}


// =========================
// ESCAPE HTML
// =========================
function escapeHTML(text) {

    const div =
        document.createElement("div");

    div.innerText = text;

    return div.innerHTML;
}


// =========================
// JOIN ROOM
// =========================
function joinRoom(
    roomId,
    roomName,
    roomDesc
) {

    currentRoom = roomId;

    document.getElementById(
        "welcomeScreen"
    ).style.display = "none";

    document.getElementById(
        "chatWindow"
    ).style.display = "flex";

    document.getElementById(
        "chatRoomName"
    ).innerText = roomName;

    document.getElementById(
        "chatRoomDesc"
    ).innerText =
        roomDesc || "";

    document.getElementById(
        "messagesContainer"
    ).innerHTML = "";

    // Active room
    document
        .querySelectorAll(".room-item")
        .forEach(room => {
            room.classList.remove(
                "active"
            );
        });

    const activeRoom =
        document.getElementById(
            `room-${roomId}`
        );

    if (activeRoom) {
        activeRoom.classList.add(
            "active"
        );
    }

    // Connect socket
    connectWebSocket(roomId);

    // Load messages
    loadMessages(roomId);

    // Mobile
    if (window.innerWidth <= 700) {

        document
            .getElementById("sidebar")
            .classList.add("hidden");

        document.getElementById(
            "backBtn"
        ).style.display = "block";
    }
}


// =========================
// CLOSE ROOM
// =========================
function closeRoom() {

    document.getElementById(
        "chatWindow"
    ).style.display = "none";

    document.getElementById(
        "welcomeScreen"
    ).style.display = "flex";

    document
        .getElementById("sidebar")
        .classList.remove("hidden");

    document.getElementById(
        "backBtn"
    ).style.display = "none";

    currentRoom = null;

    if (socket) {
        socket.close();
    }
}


// =========================
// LOAD OLD MESSAGES
// =========================
async function loadMessages(roomId) {

    try {

        const response =
            await fetch(
                `/api/rooms/${roomId}/messages`
            );

        const messages =
            await response.json();

        const container =
            document.getElementById(
                "messagesContainer"
            );

        container.innerHTML = "";

        if (messages.length === 0) {

            container.innerHTML = `
                <div class="system-msg">
                    No messages yet.
                    Start the conversation 👋
                </div>
            `;

            return;
        }

        messages.forEach(msg => {
            appendMessage(msg);
        });

    } catch (err) {

        console.log(
            "❌ Failed loading messages:",
            err
        );
    }
}


// =========================
// SEND MESSAGE
// =========================
function sendMessage() {

    const input =
        document.getElementById(
            "messageInput"
        );

    const message =
        input.value.trim();

    // EMPTY MESSAGE CHECK
    if (!message) {
        return;
    }

    // SOCKET EXISTS?
    if (!socket) {

        alert(
            "WebSocket not connected"
        );

        return;
    }

    // SOCKET OPEN?
    if (
        socket.readyState !==
        WebSocket.OPEN
    ) {

        console.log(
            "Socket state:",
            socket.readyState
        );

        alert(
            "Connection closed"
        );

        return;
    }

    // MESSAGE OBJECT
    const messageData = {

        type: "message",

        username:
            CURRENT_USER.username,

        content:
            message
    };

    console.log(
        "📤 Sending:",
        messageData
    );

    // SEND JSON
    socket.send(
        JSON.stringify(
            messageData
        )
    );

    // CLEAR INPUT
    input.value = "";

    // FOCUS AGAIN
    input.focus();
}


// =========================
// ENTER KEY
// =========================
function handleKey(event) {

    if (event.key === "Enter") {
        sendMessage();
        return;
    }

    notifyTyping();
}


// =========================
// LOGOUT
// =========================
async function handleLogout() {

    await fetch("/logout", {
        method: "POST"
    });

    window.location.href =
        "/login";
}


// =========================
// FILTER ROOMS
// =========================
function filterRooms() {

    const query =
        document
            .getElementById(
                "roomSearch"
            )
            .value
            .toLowerCase();

    const rooms =
        document.querySelectorAll(
            ".room-item"
        );

    rooms.forEach(room => {

        const text =
            room.innerText.toLowerCase();

        room.style.display =
            text.includes(query)
                ? "flex"
                : "none";
    });
}


// =========================
// MODAL FUNCTIONS
// =========================
function showNewRoomModal() {

    document
        .getElementById(
            "modalOverlay"
        )
        .classList.add("show");
}


function hideNewRoomModal() {

    document
        .getElementById(
            "modalOverlay"
        )
        .classList.remove("show");

    document.getElementById(
        "newRoomName"
    ).value = "";

    document.getElementById(
        "newRoomDesc"
    ).value = "";

    document.getElementById(
        "modal-error"
    ).style.display = "none";
}


function hideModal(event) {

    if (
        event.target.id ===
        "modalOverlay"
    ) {
        hideNewRoomModal();
    }
}


// =========================
// CREATE ROOM
// =========================
async function createRoom() {

    const name =
        document.getElementById(
            "newRoomName"
        ).value.trim();

    const description =
        document.getElementById(
            "newRoomDesc"
        ).value.trim();

    const error =
        document.getElementById(
            "modal-error"
        );

    error.style.display = "none";

    if (!name) {

        error.innerText =
            "Room name is required";

        error.style.display =
            "block";

        return;
    }

    try {

        const response =
            await fetch(
                "/api/rooms",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        name,
                        description
                    })
                }
            );

        if (!response.ok) {

            throw new Error(
                "Failed creating room"
            );
        }

        hideNewRoomModal();

        location.reload();

    } catch (err) {

        console.log(err);

        error.innerText =
            "Failed creating room";

        error.style.display =
            "block";
    }
}