var coll = document.getElementsByClassName("collapsible");

for (let i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function () {
        this.classList.toggle("active");

        var content = this.nextElementSibling;

        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + "px";
        }

    });
}

const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');

function appendMessage(sender, text) {
    const p = document.createElement('p');
    p.innerHTML = `<strong>${sender}:</strong> ${text}`;
    chatMessages.appendChild(p);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendMessage() {
    const message = userInput.value.trim();
    if (message === '') return;

    //wiadomosc usera
    appendMessage('Ty', message);
    userInput.value = ''; //clean

    //api flask
    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message }),
    })
    .then(response => response.json())
    .then(data => {
        //ai response
        appendMessage('AI', data.response);
    })
    .catch(error => {
        appendMessage('AI', 'Przepraszam, wystąpił błąd komunikacji z serwerem.');
        console.error('Błąd API chatbota:', error);
    });
}

function toggleChat() {
    const chatBox = document.querySelector('.chat-box');
    const toggleButtonIcon = document.querySelector('#toggle-chat-btn i');
    const isCollapsed = chatBox.classList.contains('collapsed');

    if (isCollapsed) {
        // ROZWIJANIE
        chatBox.classList.remove('collapsed');
        chatBox.classList.add('expanded');
        toggleButtonIcon.textContent = 'keyboard_arrow_down';
        
        // Opcjonalnie: ustaw wysokość, jeśli nie chcesz polegać tylko na CSS
        chatBox.style.height = '400px'; 
    } else {
        // ZWIJANIE
        chatBox.classList.add('collapsed');
        chatBox.classList.remove('expanded');
        toggleButtonIcon.textContent = 'keyboard_arrow_up';
        
        // Resetujemy wysokość do tej z klasy .collapsed
        chatBox.style.height = '70px';
    }
}

userInput.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

function getMessage_admin(){
    fetch('/api/chat_admin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        //ai response
        appendMessage('AI', data.response);
    })
    .catch(error => {
        appendMessage('AI', 'Przepraszam, wystąpił błąd komunikacji z serwerem.');
        console.error('Błąd API chatbota:', error);
    });
}

function getData(){

}