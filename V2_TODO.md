# Drafter V2 TODO List

This document tracks the remaining tasks and improvements for Drafter Version 2.

## High Priority Features

### Configuration & Server Management
- [ ] Custom Error Pages - Allow users to override ErrorPage rendering with custom error pages (`client_server/client_server.py:41`)
- [ ] Shareable Links - Add ability to generate shareable links to the current page state (`configuration.py:4`)
- [ ] Download/Upload State Button - Implement UI controls for downloading and uploading state as JSON (`configuration.py:5`)
- [ ] Dump Current Server Configuration - Add debug panel section to display server configuration (`debug.py:309`)
- [ ] Production Mode & Image Folder - Implement production mode deployment with proper image folder handling (`deploy.py:162`)

### Routing & URL Handling
- [ ] Route Signature Validation - Inspect and validate that routes have valid function signatures (`client_server/client_server.py:447`)
- [ ] Default Parameter Values - Enhance route functionality to support default values from function signatures (`router/routes.py:119`)
- [ ] 404 Page Enhancement - Improve 404 handling to conditionally show index link (not when already on index) (`app/missing.py:17`)
- [ ] Main File Specification - Provide more flexible ways to specify the main file for deployment (`launch.py:52`)
- [ ] Title Configuration - Allow title to be set from configuration instead of hardcoded (`launch.py:55`)

### Styling & Layout
- [ ] Indent Function - Add CSS styling function for indentation (`styling/styling.py:3`)
- [ ] Center Function - Add CSS styling function for centering content (`styling/styling.py:4`)
- [ ] Superscript/Subscript - Add styling functions for superscript and subscript text (`styling/styling.py:5`)
- [ ] Border/Margin/Padding Controls - Add comprehensive styling functions for all sides (`styling/styling.py:6`)
- [ ] Style List Handling - Review and improve approach for applying styles to lists of components (`styling/styling.py:32`)

### State Management
- [ ] State Type Change Warnings - Add warnings when state types change between route transitions (`history/state.py:22`)
- [ ] Deep Copy State - Determine if state should be deep copied in certain scenarios (`history/state.py:36`)
- [ ] State Copying Strategy - Define where and when state should be copied (`router/routes.py:306`)
- [ ] Data Loss Warnings - Warn users when route transitions might lose data (`router/routes.py:312`)
- [ ] Handle Edge Cases - Document and handle other route transition edge cases (`router/routes.py:314`)

### Components & Forms
- [ ] Form Input Name Safety - Investigate if form input names need additional sanitization (`components/forms.py:40`)
- [ ] HTML Safety Review - Review and enhance HTML escaping for user-generated content (`components/page_content.py:66`)
- [ ] State Dumping Decision - Decide on approach for dumping state information on pages (`payloads/kinds/page.py:83`)

## Medium Priority Features

### Progress & Async Operations
- [ ] Progress Payload Implementation - Complete implementation of Progress payload for long-running tasks (`payloads/kinds/progress.py:12`)
- [ ] Script Error Handling - Add proper error handling for dynamically executed scripts (`bridge/__init__.py:65`)

### History & Testing
- [ ] Image Filename Handling - Handle images without filename data (base64/tobytes representation) (`old_history.py:38`)
- [ ] Custom Type Serialization - Improve handling of dict_keys, numpy arrays, and other custom types (`old_history.py:86`)
- [ ] Recursive Image Handling - Handle images nested in lists/dictionaries/dataclasses (`old_history.py:88`)
- [ ] Import Provision - Ensure required imports are provided to students in generated test code (`old_history.py:97`)
- [ ] Structure Validation - Add validation for history structure consistency (`old_history.py:311`)
- [ ] Dictionary Type Handling - Intelligently handle various dictionary types (OrderedDict, defaultdict, etc.) (`old_history.py:334`)

### Monitoring & Debugging
- [ ] Event Tracking IDs - Add request_id, response_id, and outcome_id tracking to all events (`monitor/events/errors.py:1`)
- [ ] Event Timestamps - Add timestamp tracking to all monitoring events (`monitor/events/errors.py:2`)
- [ ] Skulpt Traceback Formatting - Enable format_traceback when Skulpt supports it (`monitor/audit.py:66`)

## Documentation & Examples
- [ ] Update API documentation for new V2 features
- [ ] Create migration guide from V1 to V2
- [ ] Add examples for new configuration options
- [ ] Document best practices for state management
- [ ] Add tutorials for custom error pages
- [ ] Create guide for production deployment

## Testing
- [ ] Add unit tests for new configuration options
- [ ] Test custom error page functionality
- [ ] Add integration tests for state management
- [ ] Test production deployment scenarios
- [ ] Add tests for new styling functions
- [ ] Test progress payload with long-running operations

## Performance & Optimization
- [ ] Profile and optimize state serialization
- [ ] Optimize history tracking for large state objects
- [ ] Improve client-server communication efficiency
- [ ] Review and optimize asset loading strategies

## Security
- [ ] Audit HTML escaping across all components
- [ ] Review input validation for form components
- [ ] Security review of state serialization
- [ ] Validate uploaded file handling

## Future Considerations
- [ ] Support for WebSocket-based real-time updates
- [ ] Plugin system for custom components
- [ ] Theme marketplace/repository
- [ ] Collaborative editing features
- [ ] Database integration helpers
- [ ] Authentication/authorization framework

## Maintenance
- [ ] Review and close/update old GitHub issues
- [ ] Update dependencies to latest stable versions
- [ ] Improve error messages throughout codebase
- [ ] Enhance type hints and mypy coverage
- [ ] Code cleanup and refactoring where needed

---

**Note**: This list is based on TODO comments found in the codebase as of November 2025. Priorities may shift based on user feedback and project goals.

For questions or to propose new features, please open an issue on GitHub.
