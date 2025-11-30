/**
 * Drafter Storage Module for Skulpt
 * 
 * This module provides localStorage bindings for the Drafter storage API
 * when running in the browser via Skulpt.
 */

// Add localStorage support to Skulpt console
if (typeof Sk !== 'undefined' && Sk.console && Sk.console.drafter) {
    // Storage functions that can be called from Python via Skulpt
    Sk.console.drafter.localStorage = {
        /**
         * Save data to browser localStorage
         * @param {string} key - Storage key
         * @param {string} data - Serialized data to save
         */
        setItem: function(key, data) {
            try {
                if (typeof localStorage !== 'undefined') {
                    localStorage.setItem(key, data);
                    return true;
                } else {
                    console.warn('localStorage not available');
                    return false;
                }
            } catch (e) {
                console.error('Error saving to localStorage:', e);
                return false;
            }
        },
        
        /**
         * Load data from browser localStorage
         * @param {string} key - Storage key
         * @returns {string|null} - Stored data or null if not found
         */
        getItem: function(key) {
            try {
                if (typeof localStorage !== 'undefined') {
                    return localStorage.getItem(key);
                } else {
                    console.warn('localStorage not available');
                    return null;
                }
            } catch (e) {
                console.error('Error loading from localStorage:', e);
                return null;
            }
        },
        
        /**
         * Remove data from browser localStorage
         * @param {string} key - Storage key
         */
        removeItem: function(key) {
            try {
                if (typeof localStorage !== 'undefined') {
                    localStorage.removeItem(key);
                    return true;
                } else {
                    console.warn('localStorage not available');
                    return false;
                }
            } catch (e) {
                console.error('Error removing from localStorage:', e);
                return false;
            }
        },
        
        /**
         * Check if a key exists in localStorage
         * @param {string} key - Storage key
         * @returns {boolean} - True if key exists
         */
        hasItem: function(key) {
            try {
                if (typeof localStorage !== 'undefined') {
                    return localStorage.getItem(key) !== null;
                } else {
                    return false;
                }
            } catch (e) {
                console.error('Error checking localStorage:', e);
                return false;
            }
        },
        
        /**
         * Get all keys with a given prefix
         * @param {string} prefix - Key prefix to search for
         * @returns {Array} - Array of matching keys
         */
        getKeys: function(prefix) {
            try {
                if (typeof localStorage !== 'undefined') {
                    const keys = [];
                    for (let i = 0; i < localStorage.length; i++) {
                        const key = localStorage.key(i);
                        if (key && key.startsWith(prefix)) {
                            keys.push(key);
                        }
                    }
                    return keys;
                } else {
                    return [];
                }
            } catch (e) {
                console.error('Error getting keys from localStorage:', e);
                return [];
            }
        },
        
        /**
         * Clear all items with a given prefix
         * @param {string} prefix - Key prefix to clear
         */
        clearPrefix: function(prefix) {
            try {
                if (typeof localStorage !== 'undefined') {
                    const keys = this.getKeys(prefix);
                    keys.forEach(key => localStorage.removeItem(key));
                    return true;
                } else {
                    return false;
                }
            } catch (e) {
                console.error('Error clearing localStorage:', e);
                return false;
            }
        }
    };
}
