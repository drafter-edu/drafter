// Drafter LLM Local Storage Helper Functions
(function() {
    'use strict';
    
    window.drafterLLM = {
        saveApiKey: function(service, apiKey) {
            if (typeof localStorage !== 'undefined') {
                localStorage.setItem('drafter_llm_' + service, apiKey);
            }
        },
        loadApiKey: function(service) {
            if (typeof localStorage !== 'undefined') {
                return localStorage.getItem('drafter_llm_' + service) || '';
            }
            return '';
        },
        clearApiKey: function(service) {
            if (typeof localStorage !== 'undefined') {
                localStorage.removeItem('drafter_llm_' + service);
            }
        },
        initializeApiKeyBoxes: function() {
            // Initialize all API key boxes on the page
            if (typeof document.querySelectorAll === 'undefined') {
                return;
            }
            var boxes = document.querySelectorAll('.drafter-api-key-box');
            for (var i = 0; i < boxes.length; i++) {
                var input = boxes[i];
                var service = input.getAttribute('data-service');
                if (service) {
                    // Load stored API key
                    var stored = window.drafterLLM.loadApiKey(service);
                    if (stored) {
                        input.value = stored;
                    }
                    // Save API key on change
                    (function(inp, svc) {
                        inp.addEventListener('change', function() {
                            window.drafterLLM.saveApiKey(svc, this.value);
                        });
                    })(input, service);
                }
            }
        }
    };

    // Initialize API key boxes when DOM is ready
    function initializeWhenReady() {
        try {
            window.drafterLLM.initializeApiKeyBoxes();
        } catch (e) {
            // Silently fail if there's an issue
            // Error is caught but not logged to avoid exposing implementation details
        }
    }

    if (typeof document !== 'undefined') {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeWhenReady);
        } else {
            // DOM is already loaded, initialize on next tick
            setTimeout(initializeWhenReady, 0);
        }
    }
})();
