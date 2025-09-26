
$(document).ready(function() {
    // Load initial history
    loadHistory();

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
        try {
            const result = await apiRequest('/api/chat', 'POST', { prompt, model });
            
            // Show the prompt
            $('#currentPrompt').show();
            $('#promptDisplay').text(`"${prompt}"`);
            
            // Show the response
            $('#chatResponse').html(result.response_html);
            
            // Update history
            $('#chatHistory').html(result.history_html);
            
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
            $('#currentPrompt').hide();
            $('#chatResponse').empty();
            $('#chatHistory').empty();
            $('#promptInput').val('');
            
            showStatus('Chat cleared successfully!', 'success');
        } catch (error) {
            // Error already handled in apiRequest
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
            }
        } catch (error) {
            // Error already handled in apiRequest
        }
    }

    async function loadHistory() {
        try {
            const result = await apiRequest('/api/history');
            $('#chatHistory').html(result.history_html);
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