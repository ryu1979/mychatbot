
$(document).ready(function() {
    // Initialize chat history from localStorage
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];

    // Load initial history
    loadHistory();

    initializeChat();
    
    // API Helper Functions
    function showStatus(message, type = 'info') {
        const statusDiv = $('#statusMessages');
        const alertClass = type === 'error' ? 'error' : (type === 'success' ? 'success' : 'info');
        statusDiv.html(`<div class="${alertClass}">${message}</div>`);
        setTimeout(() => statusDiv.empty(), 5000);
    }

    function setLoading(isLoading) {
        if (isLoading) {
            $('body').addClass('loading');
        } else {
            $('body').removeClass('loading');
        }
    }

    async function apiRequest(url, method = 'GET', data = null) {
        try {
            setLoading(true);
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error('API Error:', error);
            showStatus(`Error: ${error.message}`, 'error');
            throw error;
        } finally {
            setLoading(false);
        }
    }

    // Chat Functions
    async function sendMessage(prompt, model) {
        if (!prompt) {
            showStatus('Please enter a prompt.', 'error');
            return;
        }
        try {
            const result = await apiRequest('/api/chat', 'POST', { prompt, model });
            const result = await apiRequest('/api/chat', 'POST', { prompt, history: chatHistory });
            
            // Show the prompt
            $('#currentPrompt').show();
            $('#promptDisplay').text(`"${prompt}"`);
            
            // Show the response
            $('#chatResponse').html(result.response_html);
            $('#chatResponse').html(result.response_html); // This is the last response
            
            // Update history
            $('#chatHistory').html(result.history_html);
            // Update local history and save
            chatHistory = result.history;
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            
            // Update history display
            updateHistoryDisplay();
            
            // Clear the input
            $('#promptInput').val('');
            
            //showStatus('Message sent successfully!', 'success');
        } catch (error) {
            // Error already handled in apiRequest
        }
    }

    async function clearChat() {
        try {
            await apiRequest('/api/sessions', 'POST');
            
            // Clear the display
        // Save current chat to previous chats if it has content
        if (chatHistory.length > 2) { // system + initial model message
            const previousChats = JSON.parse(localStorage.getItem('previousChats')) || [];
            previousChats.unshift(chatHistory); // Add to the beginning
            // Keep only the last 6 chats
            if (previousChats.length > 6) {
                previousChats.pop();
            }
            localStorage.setItem('previousChats', JSON.stringify(previousChats));
        }

        // Start a new chat
        chatHistory = [];
        localStorage.removeItem('chatHistory');
        await initializeChat();
        showStatus('Chat cleared and saved. New chat started.', 'success');
    }

    async function restorePreviousChat(chatNum) {
        const previousChats = JSON.parse(localStorage.getItem('previousChats')) || [];
        const index = chatNum - 1;

        if (previousChats[index]) {
            chatHistory = previousChats[index];
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            updateHistoryDisplay();
            $('#currentPrompt').hide();
            $('#chatResponse').empty();
            $('#chatHistory').empty();
            $('#promptInput').val('');
            
            showStatus('Chat cleared successfully!', 'success');
        } catch (error) {
            // Error already handled in apiRequest
            showStatus(`Restored previous chat ${chatNum}.`, 'success');
        } else {
            showStatus(`Previous chat ${chatNum} not found.`, 'error');
        }
    }

    async function restorePreviousChat(chatNum) {
        try {
            const result = await apiRequest(`/api/sessions/${chatNum}`, 'PUT');
            
            if (result.success) {
                $('#chatHistory').html(result.history_html);
                $('#currentPrompt').hide();
                $('#chatResponse').empty();
                showStatus(result.message, 'success');
            } else {
                showStatus(result.message, 'error');
    async function initializeChat() {
        if (chatHistory.length === 0) {
            try {
                const result = await apiRequest('/api/new_session', 'GET');
                chatHistory = result.history;
                localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            } catch (error) {
                showStatus('Could not start a new session.', 'error');
            }
        } catch (error) {
            // Error already handled in apiRequest
        }
        updateHistoryDisplay();
        $('#currentPrompt').hide();
        $('#chatResponse').empty();
        $('#promptInput').val('');
    }

    function updateHistoryDisplay() {
        const historyDiv = $('#chatHistory');
        historyDiv.empty();
        
        // Skip system message and first model response for history view
        const displayableHistory = chatHistory.slice(2); 

        displayableHistory.forEach(msg => {
            let messageHtml = '';
            if (msg.role === 'user') {
                messageHtml = `<p><strong>You:</strong> ${msg.content}</p>`;
            } else if (msg.role === 'model') {
                // This assumes your backend provides the necessary details.
                // Let's build the HTML from the history object.
                // NOTE: The python code was updated to send a pre-formatted history_html.
                // We will use that instead for simplicity, but this is how you'd build it on the client.
            }
            // historyDiv.append(messageHtml);
        });

        // For now, let's just rebuild it from the full history object
        let fullHistoryHtml = "";
        chatHistory.slice(2).forEach(msg => {
            if (msg.role === 'user') {
                fullHistoryHtml += `<p><strong>You:</strong> ${msg.content}</p>`;
            } else if (msg.role === 'model') {
                // A 'name' property would be useful in the history object.
                // For now, we can't display the personality name easily.
                fullHistoryHtml += `<p><strong>Bot</strong> [${msg.model}]: ${msg.content}</p>`;
            }
        });
        historyDiv.html(fullHistoryHtml);
    }

    async function loadHistory() {
        try {
            const result = await apiRequest('/api/history');
            $('#chatHistory').html(result.history_html);
            // This function is now replaced by initializeChat and updateHistoryDisplay
            // which use localStorage.
        } catch (error) {
            // Error already handled in apiRequest
        }
    }

    // Event Handlers
    $('.model-btn').on('click', function(e) {
        e.preventDefault();
        const model = $(this).data('model');
        const prompt = $('#promptInput').val().trim();
        
        if (!prompt) {
            showStatus('Please enter a prompt first!', 'error');
            $('#promptInput').focus();
            return;
        }
        
        sendMessage(prompt, model);
    });

    $('#clearBtn').on('click', function(e) {
        e.preventDefault();
        clearChat();
    });

    $('.previous-btn').on('click', function(e) {
        e.preventDefault();
        const chatNum = $(this).data('previous');
        restorePreviousChat(chatNum);
    });

    // Allow Enter key to submit with default model (GPT)
    $('#promptInput').on('keypress', function(e) {
        if (e.which === 13) { // Enter key
            e.preventDefault();
            const prompt = $(this).val().trim();
            if (prompt) {
                sendMessage(prompt, 'gpt');
            }
        }
    });

    // Add visual feedback for button clicks
    $('.model-btn, .previous-btn, #clearBtn').on('click', function() {
        $(this).addClass('loading');
        setTimeout(() => $(this).removeClass('loading'), 2000);
    });
});