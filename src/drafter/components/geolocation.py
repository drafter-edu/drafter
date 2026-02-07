"""Geolocation components for requesting and displaying location data.

Provides the CurrentLocation component and Location dataclass for handling
browser geolocation API integration with form-based workflows.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from drafter.components.page_content import Component, ComponentArgument
from drafter.components.planning.render_plan import RenderPlan, AssetBundle
from drafter.components.utilities.validation import validate_parameter_name


LocationStatus = Literal[
    "unavailable", "prompt", "granted", "denied", "pending", "error"
]


@dataclass
class Location:
    """Geolocation data from the browser's geolocation API.

    Attributes:
        status: Current permission/availability state.
        message: Optional descriptive message about the status.
        lat: Latitude in decimal degrees (None if unavailable).
        lon: Longitude in decimal degrees (None if unavailable).
        accuracy: Position accuracy in meters (None if unavailable).
        altitude: Altitude in meters above sea level (None if unavailable).
        heading: Direction of travel in degrees (None if unavailable).
        speed: Speed in meters per second (None if unavailable).
        timestamp: Unix timestamp of position acquisition (None if unavailable).
    """

    status: LocationStatus
    message: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    timestamp: Optional[float] = None


@dataclass(repr=False)
class CurrentLocation(Component):
    """A form component that requests and displays browser geolocation.

    This component integrates with the browser's Geolocation API to request
    user permission and provide location data. It handles multiple visual states
    based on permission status and automatically populates route parameters
    after permission is granted.

    Visual states:
    - prompt: Shows "Use my location" button when permission not yet requested
    - pending: Shows spinner while waiting for permission
    - denied: Shows "Location blocked" message with help link
    - granted: Shows "Location available ✓" with optional coordinates
    - error: Shows error message if geolocation fails
    - unavailable: Shows message if geolocation API not supported

    Attributes:
        name: The form field name that will contain location data.
        show_coordinates: Whether to display lat/lon when granted (default: False).
        tag: Always 'div' for this component.
    """

    name: str
    show_coordinates: bool = False
    tag = "div"

    ARGUMENTS = [
        ComponentArgument("name"),
        ComponentArgument("show_coordinates", kind="keyword", default_value=False),
    ]

    KNOWN_ATTRS = ["data-geolocation-name", "data-show-coordinates"]

    def __init__(
        self,
        name: str,
        show_coordinates: bool = False,
        **extra_settings,
    ):
        """Initialize the CurrentLocation component.

        Args:
            name: The form field name for geolocation data.
            show_coordinates: Whether to display coordinates when available.
            **extra_settings: Additional HTML attributes.
        """
        validate_parameter_name(name, "CurrentLocation")
        self.name = name
        self.show_coordinates = show_coordinates
        self.extra_settings = extra_settings

    def get_id(self) -> str:
        """Get the identifier for this geolocation component.

        Returns:
            The element ID or the field name.
        """
        return self.extra_settings.get("id", f"drafter-geolocation-{self.name}")

    def _render_attributes(self, attributes: dict) -> str:
        """Convert attribute dictionary to HTML attribute string.

        Args:
            attributes: Dictionary of HTML attributes.

        Returns:
            String of space-separated key="value" pairs.
        """
        import html
        parts = []
        for key, value in attributes.items():
            if value is True:
                parts.append(key)
            elif value is not False and value is not None:
                escaped_value = html.escape(str(value), quote=True)
                parts.append(f'{key}="{escaped_value}"')
        return " ".join(parts)

    def plan(self, context) -> RenderPlan:
        """Create a render plan for the geolocation component.

        Returns:
            RenderPlan with HTML structure and associated JS/CSS assets.
        """
        # Get base attributes
        attributes = self.get_attributes(context)

        # Add geolocation-specific data attributes
        attributes["data-geolocation-name"] = self.name
        attributes["data-show-coordinates"] = "true" if self.show_coordinates else "false"
        attributes["id"] = self.get_id()
        attributes["class"] = attributes.get("class", "") + " drafter-geolocation"

        # Create child elements as raw HTML strings
        # This is simpler than trying to create nested Component structures
        hidden_input_id = f"{self.get_id()}-data"
        status_id = f"{self.get_id()}-status"
        
        children_html = f"""
            <input type="hidden" name="{self.name}" id="{hidden_input_id}" value="" />
            <div class="drafter-geolocation-status" id="{status_id}">
                <button type="button" class="drafter-geolocation-prompt" data-geolocation-action="request">
                    📍 Use my location
                </button>
                <p class="drafter-geolocation-help">
                    Your location helps personalize your experience. Click to allow.
                </p>
            </div>
        """

        # Bundle JavaScript for geolocation handling
        js_code = self._get_geolocation_js()
        css_code = self._get_geolocation_css()

        assets = AssetBundle(
            css={css_code},
            js={js_code},
        )

        return RenderPlan(
            kind="raw",
            raw_html=f'<div {self._render_attributes(attributes)}>{children_html}</div>',
            assets=assets,
        )

    def _get_geolocation_js(self) -> str:
        """Generate JavaScript code for geolocation functionality.

        Returns:
            JavaScript code as a string.
        """
        return """
(function() {
    'use strict';

    // Initialize all geolocation components on the page
    function initGeolocation() {
        const containers = document.querySelectorAll('.drafter-geolocation');
        
        containers.forEach(container => {
            const name = container.dataset.geolocationName;
            const showCoords = container.dataset.showCoordinates === 'true';
            const statusDiv = container.querySelector('.drafter-geolocation-status');
            const dataInput = container.querySelector('input[type="hidden"]');
            
            // Check if geolocation is supported
            if (!navigator.geolocation) {
                updateStatus(statusDiv, 'unavailable', 'Geolocation is not supported by your browser', null, showCoords);
                return;
            }

            // Check for existing permission
            if (navigator.permissions) {
                navigator.permissions.query({ name: 'geolocation' }).then(result => {
                    if (result.state === 'granted') {
                        // Already granted, get position immediately
                        requestPosition(statusDiv, dataInput, showCoords);
                    } else if (result.state === 'denied') {
                        updateStatus(statusDiv, 'denied', 'Location access denied', null, showCoords);
                    }
                    // If 'prompt', leave the initial button visible
                }).catch(err => {
                    console.warn('Permissions API not fully supported:', err);
                });
            }

            // Handle button click
            const button = container.querySelector('[data-geolocation-action="request"]');
            if (button) {
                button.addEventListener('click', () => {
                    updateStatus(statusDiv, 'pending', 'Requesting permission...', null, showCoords);
                    requestPosition(statusDiv, dataInput, showCoords);
                });
            }
        });
    }

    function requestPosition(statusDiv, dataInput, showCoords) {
        navigator.geolocation.getCurrentPosition(
            position => handleSuccess(position, statusDiv, dataInput, showCoords),
            error => handleError(error, statusDiv, dataInput, showCoords),
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    function handleSuccess(position, statusDiv, dataInput, showCoords) {
        const coords = position.coords;
        const locationData = {
            status: 'granted',
            message: 'Location available',
            lat: coords.latitude,
            lon: coords.longitude,
            accuracy: coords.accuracy,
            altitude: coords.altitude,
            heading: coords.heading,
            speed: coords.speed,
            timestamp: position.timestamp
        };

        // Store in hidden input as JSON
        dataInput.value = JSON.stringify(locationData);

        updateStatus(statusDiv, 'granted', 'Location available ✓', locationData, showCoords);
    }

    function handleError(error, statusDiv, dataInput, showCoords) {
        let status = 'error';
        let message = 'Could not retrieve location';

        switch (error.code) {
            case error.PERMISSION_DENIED:
                status = 'denied';
                message = 'Location access denied';
                break;
            case error.POSITION_UNAVAILABLE:
                status = 'error';
                message = 'Location information unavailable';
                break;
            case error.TIMEOUT:
                status = 'error';
                message = 'Location request timed out';
                break;
        }

        const locationData = {
            status: status,
            message: message
        };

        dataInput.value = JSON.stringify(locationData);
        updateStatus(statusDiv, status, message, null, showCoords);
    }

    function updateStatus(statusDiv, status, message, locationData, showCoords) {
        let html = '';

        switch (status) {
            case 'pending':
                html = `
                    <div class="drafter-geolocation-pending">
                        <div class="drafter-geolocation-spinner"></div>
                        <p>${message}</p>
                    </div>
                `;
                break;

            case 'denied':
                html = `
                    <div class="drafter-geolocation-denied">
                        <p class="drafter-geolocation-error-icon">⚠️</p>
                        <p class="drafter-geolocation-error-message">${message}</p>
                        <p class="drafter-geolocation-help-link">
                            <a href="javascript:void(0)" onclick="alert('To enable location access:\\n\\n1. Click the lock or info icon in your browser\\'s address bar\\n2. Find Location permissions\\n3. Change to \\'Allow\\'\\n4. Refresh this page')">
                                How to enable location access
                            </a>
                        </p>
                    </div>
                `;
                break;

            case 'granted':
                let coordsHtml = '';
                if (showCoords && locationData) {
                    coordsHtml = `
                        <p class="drafter-geolocation-coords">
                            ${locationData.lat.toFixed(6)}, ${locationData.lon.toFixed(6)}
                            ${locationData.accuracy ? ` (±${Math.round(locationData.accuracy)}m)` : ''}
                        </p>
                    `;
                }
                html = `
                    <div class="drafter-geolocation-granted">
                        <p class="drafter-geolocation-success-icon">✓</p>
                        <p class="drafter-geolocation-success-message">${message}</p>
                        ${coordsHtml}
                    </div>
                `;
                break;

            case 'unavailable':
                html = `
                    <div class="drafter-geolocation-unavailable">
                        <p class="drafter-geolocation-error-icon">ℹ️</p>
                        <p>${message}</p>
                    </div>
                `;
                break;

            case 'error':
                html = `
                    <div class="drafter-geolocation-error">
                        <p class="drafter-geolocation-error-icon">⚠️</p>
                        <p class="drafter-geolocation-error-message">${message}</p>
                    </div>
                `;
                break;
        }

        statusDiv.innerHTML = html;
    }

    // Initialize on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initGeolocation);
    } else {
        initGeolocation();
    }

    // Re-initialize when content is dynamically updated (for Fragment updates)
    window.addEventListener('drafter:content-updated', initGeolocation);
})();
"""

    def _get_geolocation_css(self) -> str:
        """Generate CSS styling for geolocation component.

        Returns:
            CSS code as a string.
        """
        return """
.drafter-geolocation {
    margin: 1rem 0;
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    background: #f9f9f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.drafter-geolocation-status {
    text-align: center;
}

.drafter-geolocation-prompt {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 600;
    color: #fff;
    background: #007bff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s;
}

.drafter-geolocation-prompt:hover {
    background: #0056b3;
}

.drafter-geolocation-help {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: #666;
}

.drafter-geolocation-pending {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.drafter-geolocation-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid #f3f3f3;
    border-top: 3px solid #007bff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.drafter-geolocation-granted,
.drafter-geolocation-denied,
.drafter-geolocation-unavailable,
.drafter-geolocation-error {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.drafter-geolocation-success-icon {
    font-size: 2rem;
    color: #28a745;
    margin: 0;
}

.drafter-geolocation-success-message {
    font-weight: 600;
    color: #28a745;
    margin: 0;
}

.drafter-geolocation-error-icon {
    font-size: 2rem;
    margin: 0;
}

.drafter-geolocation-error-message {
    font-weight: 600;
    color: #dc3545;
    margin: 0;
}

.drafter-geolocation-coords {
    font-family: monospace;
    font-size: 0.875rem;
    color: #333;
    margin: 0;
}

.drafter-geolocation-help-link {
    margin: 0.5rem 0 0 0;
}

.drafter-geolocation-help-link a {
    color: #007bff;
    text-decoration: none;
    font-size: 0.875rem;
}

.drafter-geolocation-help-link a:hover {
    text-decoration: underline;
}
"""
