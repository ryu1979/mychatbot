
$(document).ready(function() {
    // Initialize chat history from localStorage
    let chatHistory = JSON.parse(localStorage.getItem('chatHistory')) || [];
    let personalities = []; // Cache for personality data

    // Load initial history
    loadPersonalities();
    
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
            const rolenum = $('#personalitySelector').val();
            const result = await apiRequest('/api/chat', 'POST', { prompt, history: chatHistory, rolenum: parseInt(rolenum) });
            
            // Show the prompt
            $('#currentPrompt').show();
            $('#promptDisplay').text(`"${prompt}"`);
            
            // Show the response
            $('#chatResponse').html(result.response_html); // This is the last response
            
            // Update local history and save
            chatHistory = result.history;
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            
            // Update history display
            $('#chatHistory').html(result.history_html);
            
            // Clear the input
            $('#promptInput').val('');
        } catch (error) {
            // Error already handled in apiRequest
        }
    }

    async function clearChat() {
        // Save current chat to previous chats if it has content
        if (chatHistory.length > 2) { // system + initial model message
            const previousChats = JSON.parse(localStorage.getItem('previousChats')) || [];
            previousChats.unshift(chatHistory); // Add to the beginning
            // Keep only the last 6 chats
            if (previousChats.length > 6) {
                previousChats.pop();
            }
            localStorage.setItem('previousChats', JSON.stringify(previousChats));
            updatePreviousChatsDisplay();
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
            // Save the current chat before swapping, if it has any user interaction
            if (chatHistory.length > 2) {
                // The chat we are restoring is at `index`. We place the current chat there.
                const chatToRestore = previousChats.splice(index, 1, chatHistory)[0];
                chatHistory = chatToRestore;
            } else {
                // If current chat is empty, just load the old one and remove it from the previous list.
                chatHistory = previousChats.splice(index, 1)[0];
            }

            // Update localStorage
            localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            localStorage.setItem('previousChats', JSON.stringify(previousChats));
            updatePreviousChatsDisplay();

            // Update UI
            updateHistoryDisplay();
            $('#currentPrompt').hide();
            $('#chatResponse').empty();
            showStatus(`Restored previous chat ${chatNum}.`, 'success');
        } else {
            showStatus(`Previous chat ${chatNum} not found.`, 'error');
        }
    }

    async function initializeChat() {
        if (chatHistory.length === 0) {
            try {
                const rolenum = $('#personalitySelector').val();
                const result = await apiRequest(`/api/new_session?rolenum=${rolenum}`, 'GET');
                chatHistory = result.history;
                localStorage.setItem('chatHistory', JSON.stringify(chatHistory));
            } catch (error) {
                showStatus('Could not start a new session.', 'error');
            }
        }
        updateHistoryDisplay();
        $('#currentPrompt').hide();
        $('#chatResponse').empty();
        $('#promptInput').val('');
    }

    async function loadPersonalities() {
        try {
            const personalityList = await apiRequest('/api/personalities', 'GET');
            personalities = personalityList; // Cache the list
            const selector = $('#personalitySelector');
            selector.empty();
            personalityList.forEach(p => {
                selector.append(`<option value="${p.rolenum}">${p.name}</option>`);
            });
            // Now that personalities are loaded, initialize the chat
            await initializeChat();
            updatePreviousChatsDisplay();
            updateHistoryDisplay();
        } catch (error) {
            showStatus('Could not load personalities.', 'error');
        }
    }

    function updateHistoryDisplay() {
        const historyDiv = $('#chatHistory');
        historyDiv.empty();

        if (personalities.length === 0) {
            // Don't try to render history until personalities are loaded
            return;
        }

        let fullHistoryHtml = "";
        chatHistory.slice(2).forEach(msg => { // slice(2) to skip system and initial model message
            if (msg.role === 'user') {
                fullHistoryHtml += `<p><strong>You:</strong> ${msg.content}</p>`;
            } else if (msg.role === 'model') {
                const personality = personalities.find(p => p.rolenum === msg.rolenum) || { name: 'Bot' };
                fullHistoryHtml += `<p><strong>${personality.name}</strong> [${msg.model}]: ${msg.content}</p>`;
            }
        });
        historyDiv.html(fullHistoryHtml);
    }

    function updatePreviousChatsDisplay() {
        const container = $('#previousChatsContainer');
        container.empty();
        const previousChats = JSON.parse(localStorage.getItem('previousChats')) || [];

        if (previousChats.length > 0) {
            const list = $('<li></li>');
            previousChats.forEach((chat, index) => {
                // Find the first model response to use as a preview
                const firstModelResponse = chat.find(msg => msg.role === 'model');
                let previewText = `Chat ${index + 1}`;
                if (firstModelResponse) {
                    // Find the personality for this chat
                    const personality = personalities.find(p => p.rolenum === firstModelResponse.rolenum);
                    const personalityName = personality ? personality.name : 'Bot';
                    previewText = `${personalityName}: ${firstModelResponse.content.substring(0, 25)}...`;
                }
                
                const button = $(`<button type="button" data-previous="${index + 1}" class="button previous-btn">${previewText}</button>`);
                list.append(button);
            });
            container.append(list);
        }
    }

    async function loadHistory() {
        try {
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

    $('#previousChatsContainer').on('click', '.previous-btn', function(e) {
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