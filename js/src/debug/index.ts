/**
 * Debug panel integration module.
 * Provides a bridge between Skulpt and the TypeScript debug panel.
 */

import { DebugPanel, TelemetryEvent } from './panel';

// Global debug panel instance
let debugPanelInstance: DebugPanel | null = null;

/**
 * Initialize the debug panel and return the instance.
 * This should be called once when the application starts.
 */
export function initDebugPanel(containerId: string = 'drafter-debug--'): DebugPanel {
    if (!debugPanelInstance) {
        debugPanelInstance = new DebugPanel(containerId);
    }
    return debugPanelInstance;
}

/**
 * Get the current debug panel instance.
 */
export function getDebugPanel(): DebugPanel | null {
    return debugPanelInstance;
}

/**
 * Handle a telemetry event from Python/Skulpt.
 * This function can be called directly from the Skulpt bridge.
 */
export function handleTelemetryFromPython(eventData: any): void {
    if (!debugPanelInstance) {
        console.warn('[Debug Panel] Not initialized yet');
        return;
    }

    try {
        // Convert Python event data to TypeScript TelemetryEvent
        const event: TelemetryEvent = {
            event_type: eventData.event_type || 'unknown',
            correlation: eventData.correlation || {},
            source: eventData.source || 'unknown',
            id: eventData.id || -1,
            version: eventData.version || '0.0.1',
            level: eventData.level || 'info',
            timestamp: eventData.timestamp || new Date().toISOString(),
            data: eventData.data
        };

        debugPanelInstance.handleTelemetryEvent(event);
    } catch (error) {
        console.error('[Debug Panel] Error handling telemetry:', error, eventData);
    }
}

/**
 * Export to window for Skulpt access
 */
if (typeof window !== 'undefined') {
    (window as any).DrafterDebugPanel = {
        init: initDebugPanel,
        get: getDebugPanel,
        handleTelemetry: handleTelemetryFromPython
    };
}
