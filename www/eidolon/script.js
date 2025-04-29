const form = document.getElementById('terminal-form');
const input = document.getElementById('terminal-input');
const windowTerminal = document.getElementById('terminal-window');

form.addEventListener('submit', function (e) {
  e.preventDefault();
  const command = input.value.trim();
  if (command) {
    addMessage(`> ${command}`);
    processCommand(command.toLowerCase());
    input.value = '';
  }
});

function addMessage(message) {
  const para = document.createElement('p');
  para.textContent = message;
  windowTerminal.appendChild(para);
  windowTerminal.scrollTop = windowTerminal.scrollHeight;
}

function processCommand(cmd) {
  switch (cmd) {
    case 'puritas':
      addMessage('⚡ PURITY IS OUR STRENGTH.');
      break;
    case 'virtus':
      addMessage('⚡ VIRTUE IS OUR SHIELD.');
      break;
    case 'help':
      addMessage('⚡ Available commands: PURITAS, VIRTUS, HELP.');
      break;
    default:
      addMessage('⚡ Unknown command. Type HELP.');
  }
}
