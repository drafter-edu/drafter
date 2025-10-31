# Monitor and Telemetry Subsystem

## Overview

The Monitor and Telemetry subsystem provides comprehensive debugging and monitoring capabilities for Drafter applications. It tracks all Request/Response/Outcome cycles, errors, warnings, and state changes, presenting them in a professional debug panel.

## Architecture

### Components

1. **Monitor** (`src/drafter/monitor.py`)
   - Lives in the ClientServer via composition
   - Tracks telemetry from various sources
   - Generates debug HTML/CSS/JS for the client

2. **Telemetry** (`src/drafter/telemetry.py`)
   - Data structures for collecting debug information

3. **Integration with ClientServer**
   - Monitor is automatically instantiated in ClientServer
   - All requests, responses, and outcomes are tracked
   - Debug information sent via "debug" channel in Response

## Debug Panel Features

### Visual Features

- **Dark Theme**: Professional VS Code-inspired interface
- **Fixed Position**: Stays at bottom of viewport
- **Collapsible Sections**: Organized information hierarchy
- **Color Coding**: Visual distinction for errors (red), warnings (yellow), info (blue)
- **Keyboard Shortcut**: Ctrl+Shift+D to toggle panel

### Screenshots

**Debug Panel:**

![Debug Panel](https://github.com/user-attachments/assets/cf31876d-f106-45d6-8430-d1c1577d5d21)

**Debug Panel Expanded:**

![Debug Panel Expanded](https://github.com/user-attachments/assets/c2cb1f77-dc35-4e6d-ae66-3f23cbee42df)

## Testing

Comprehensive test suite in `tests/test_monitor.py`. Run tests with:

```bash
python tests/test_monitor.py
```
