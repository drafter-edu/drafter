# Drafter V2 Infrastructure

This document describes the new V2 infrastructure components that have been implemented for Drafter.

## Overview

The V2 infrastructure builds upon the existing Drafter foundation and introduces new components for more flexible and powerful web application development. The key additions include:

1. **Site class** - For managing website metadata
2. **New ResponsePayload types** - Fragment, Update, Redirect, Download, Progress
3. **Channels** - For bidirectional communication
4. **AppBuilder** - For generating static deployable websites

## Components

### Site Class

The `Site` class represents a complete Drafter website with metadata and route management.

```python
from drafter import Site

site = Site(
    title="My Application",
    description="A great web app",
    favicon="/favicon.ico",
    language="en",
    author="Your Name",
    keywords=["web", "app", "drafter"],
)
```

### ResponsePayload Types

New payload types: Fragment, Redirect, Download, Progress, Update

See the full documentation in the file for details on each type.

## Architecture

The V2 infrastructure maintains backward compatibility with V1 while adding new capabilities for modern web development.

