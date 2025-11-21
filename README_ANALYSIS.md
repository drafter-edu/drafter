# README.md Analysis: Inconsistencies with Codebase

This document analyzes the README.md file and identifies inconsistencies with the actual codebase implementation. Each inconsistency is categorized as either:
- **README Outdated**: The README describes features that don't exist or have changed
- **Codebase Incomplete**: The codebase is missing features described in the README
- **Terminology Mismatch**: Different names are used in README vs. code
- **Documentation Gap**: Missing or unclear documentation

---

## Executive Summary

The README.md provides a comprehensive architectural overview of Drafter version 2.0, but there are several inconsistencies between the documented architecture and the actual implementation. Most issues fall into three categories:

1. **Naming/Terminology Mismatches**: The README uses names like "BridgeClient" but the code uses "ClientBridge"
2. **Missing/Incomplete Features**: Several features described in the README are not fully implemented
3. **CLI Command Discrepancies**: The README describes a `build` command that works differently than documented

---

## Detailed Inconsistencies

### 1. ❌ **BridgeClient vs ClientBridge** (Terminology Mismatch)

**README States:** 
> "The `BridgeClient` is responsible for populating the DOM, tracking user interactions, and sending requests from the client side"

**Actual Implementation:**
- The class is named `ClientBridge` in the Python code (`src/drafter/bridge/__init__.py`)
- The TypeScript implementation is in `js/src/bridge/client.ts`

**Category:** Terminology Mismatch  
**Impact:** Medium - Confusing for developers trying to understand the architecture  
**Resolution Needed:** Update README to use consistent naming (`ClientBridge` throughout)

---

### 2. ❌ **AppBuilder Class** (Codebase Incomplete)

**README States:**
> "If the `build` command is used from the command line script, then the `AppBuilder` will instead generate static HTML, CSS, and JS files"
> "The `AppBuilder` and `AppServer` are together both referred to as `AppBackend`."

**Actual Implementation:**
- There is an `AppBuilderConfiguration` class in `src/drafter/config/app_builder.py`, but no actual `AppBuilder` class
- There is no `AppBackend` reference in the codebase
- The build functionality is handled directly in the CLI (`src/drafter/cli.py`)
- The `AppServer` functionality exists in `src/drafter/app/app_server.py` but is implemented as functions, not a class

**Category:** Codebase Incomplete / Terminology Mismatch  
**Impact:** High - Architecture described doesn't match implementation  
**Resolution Needed:** Either:
  - Create proper `AppBuilder` class to encapsulate build logic
  - Update README to reflect that build logic is in CLI module

---

### 3. ⚠️ **Response Payload Types Implementation Status** (Codebase Incomplete)

**README States:**
> "That function is expected to return a `Page` (or eventually other valid response payload types: `Fragment`, `Update`, `Redirect`, `Download`, `Progress`)."

**Actual Implementation:**
- ✅ `Page` exists: `src/drafter/payloads/kinds/page.py`
- ✅ `Fragment` exists: `src/drafter/payloads/kinds/fragment.py`
- ✅ `Update` exists: `src/drafter/payloads/kinds/update.py`
- ✅ `Redirect` exists: `src/drafter/payloads/kinds/redirect.py`
- ✅ `Download` exists: `src/drafter/payloads/kinds/download.py`
- ✅ `Progress` exists: `src/drafter/payloads/kinds/progress.py`

**Category:** README Outdated  
**Impact:** Low - The word "eventually" suggests these were planned, but they actually all exist  
**Resolution Needed:** Update README to remove "eventually" and confirm all payload types are implemented

---

### 4. ⚠️ **Outcome Implementation** (Documentation Gap)

**README States:**
> "After the response is successfully (or unsuccessfully) processed, the `BridgeClient` sends back an `Outcome` to the `ClientServer`"

**Actual Implementation:**
- `Outcome` only exists as an event type: `OutcomeEvent` in `src/drafter/monitor/events/request.py`
- There is no standalone `Outcome` class for data transmission
- The README describes `Outcome` as a data structure for transmission, but it appears to be only a monitoring/telemetry event

**Category:** Documentation Gap / Possible Codebase Incomplete  
**Impact:** Medium - Unclear if Outcome is fully implemented or just partially  
**Resolution Needed:** Clarify whether Outcome is:
  - Only a telemetry event (update README)
  - Should be a data class (implement it)

---

### 5. ❌ **URL Path Support with Slashes** (Codebase Incomplete)

**README States:**
> "A `URL` is a string that represents a unique `Route` function in the `Site`. It should follow the naming conventions of a Python function (e.g., lowercase letters, numbers, underscores, no spaces or special characters). Eventually, we might support slashes for things like classes or modules (which would probably translate to periods)."

**Actual Implementation:**
- URL handling in `src/drafter/urls.py` focuses on query parameters and external URLs
- Route registration in `src/drafter/router/commands.py` uses function names directly
- No evidence of slash-based routing or module/class namespacing

**Category:** Codebase Incomplete  
**Impact:** Low - This is documented as a future feature ("Eventually, we might support")  
**Resolution Needed:** No immediate action needed, this is correctly documented as future work

---

### 6. ⚠️ **State History Tracking** (Unclear Implementation Status)

**README States:**
> "Things that have to be kept in the server:
> - State
> - Initial state (for resetting)
> - Accessed pages, args
> - History of state"

**Actual Implementation:**
- `ClientServer` class exists with state management
- There's a `history` module: `src/drafter/history/`
- There's also an `old_history.py` file suggesting migration/refactoring
- History includes: `conversion.py`, `formatting.py`, `forms.py`, `pages.py`, `serialization.py`, `state.py`, `utils.py`

**Category:** Documentation Gap  
**Impact:** Low - Implementation exists but relationship between `history` module and `old_history.py` is unclear  
**Resolution Needed:** Clarify which history implementation is current and document the migration status

---

### 7. ✅ **Debug Information Features** (Implementation Status Unclear)

**README States detailed list of debug features:**
> "The debug information present in the frame:
> - Quick link to reset the state and return to index
> - Link to the About page
> - Status information... [extensive list]"

**Actual Implementation:**
- Monitor system exists: `src/drafter/monitor/`
- Debug module exists: `src/drafter/debug.py`
- Event system exists: `src/drafter/monitor/bus.py`
- Various debug event types exist in `src/drafter/monitor/events/`

**Category:** Needs Verification  
**Impact:** Low - Components exist but need manual testing to verify all features work  
**Resolution Needed:** Manual verification of debug UI features

---

### 8. ⚠️ **Command Line Interface Discrepancies** (README Outdated)

**README States:**
> "If the `build` command is used from the command line script"

**Actual Implementation:**
The CLI has been modernized:
- Uses `typer` and `rich` for better UX
- Command is `drafter build` not just `build`
- Also has `drafter serve` command for development server
- Build has two modes: `--deploy-skulpt` (default) and `--no-deploy-skulpt` for static build

**Additional CLI features not mentioned in README:**
- `--additional-files` for including extra files
- `--external-pages` for linking to external pages
- `--create-404` for 404 page generation
- `--warn-missing-info` for validation
- CDN configuration options for Skulpt assets

**Category:** README Outdated  
**Impact:** Medium - Users need to know the actual CLI interface  
**Resolution Needed:** Update README with actual CLI commands and options

---

### 9. ⚠️ **Starlette vs Actual Server Implementation** (Documentation Gap)

**README States:**
> "If a user runs the program directly, then when it reaches `start_server`, it will start a local development server (the `AppServer`) using Starlette."

**Actual Implementation:**
- `start_server()` in `src/drafter/launch.py` checks if running in Skulpt or not
- When not in Skulpt, it calls `serve_app_once()` from `src/drafter/app/app_server.py`
- The server uses both Starlette and Uvicorn
- Server includes watchfiles for hot-reload functionality
- WebSockets support for live reload

**Category:** Documentation Gap  
**Impact:** Low - Core statement is accurate but missing details  
**Resolution Needed:** Add more detail about Uvicorn, WebSockets, and hot-reload

---

### 10. ❌ **Missing pyproject.toml Dependencies** (Codebase Issue)

**README Describes:**
Development workflow with JS watching and Python server

**Actual Implementation:**
The `pyproject.toml` is missing several dependencies that are actually used:
- `typer` - Used in CLI but not listed in dependencies
- `rich` - Used in CLI but not listed in dependencies
- `starlette` - Used in app_server but not listed
- `uvicorn` - Used in app_server but not listed

These are only in the optional `dev` dependencies for some (typer), or completely missing.

**Category:** Codebase Issue  
**Impact:** High - Package installation incomplete, users will get import errors  
**Resolution Needed:** Add missing dependencies to `pyproject.toml` in the main dependencies list

---

### 11. ⚠️ **Site Class and Configuration** (Documentation Gap)

**README States:**
> "From the student developer's perspective, they are building a `Site`, which can have multiple `Route`s. A `Site` also has metadata like title, description, favicon, language, etc."

**Actual Implementation:**
- `Site` class exists: `src/drafter/site/site.py`
- Configuration is handled through `ClientServer.configuration`
- Functions exist like `set_website_title()`, `set_website_framed()`, `set_website_style()`
- Site information is set via `set_site_information(author, description, sources, planning, links)`

**Category:** Documentation Gap  
**Impact:** Low - Implementation exists but the relationship between Site and configuration could be clearer  
**Resolution Needed:** Clarify that configuration is set through helper functions, not directly on Site

---

### 12. ✅ **EventBus and Telemetry** (Correctly Implemented)

**README States:**
> "The `EventBus` is a pub/sub system that allows different parts of the application to communicate with each other without being tightly coupled."

**Actual Implementation:**
- `EventBus` exists: `src/drafter/monitor/bus.py`
- Telemetry system: `src/drafter/monitor/telemetry.py`
- Monitor class: `src/drafter/monitor/monitor.py`
- Various event types in `src/drafter/monitor/events/`

**Category:** ✅ Correctly Implemented  
**Impact:** None  
**Resolution Needed:** None

---

### 13. ⚠️ **Testing Infrastructure** (Incomplete)

**README States:**
Testing features should be available through debug information

**Actual Implementation:**
- `testing.py` exists with Bakery integration
- Very limited test files: only `tests/components/test_forms.py`
- No pytest in the main dependencies (only in dev dependencies)
- Examples have inline tests using `assert_equal` from Bakery

**Category:** Codebase Incomplete  
**Impact:** Medium - Limited test coverage  
**Resolution Needed:** Either:
  - Add more tests
  - Document that testing is primarily done through Bakery assertions in user code

---

### 14. ⚠️ **File Handling (open/read)** (Unclear Status)

**README States:**
> "How is `open` and `read` handled? We need to determine all of the local file dependencies of the project. The user should be able to provide an explicit list, but otherwise we assume that adjacent files will be possible to include."

**Actual Implementation:**
- `files.py` module exists with extensive file handling: `src/drafter/files.py`
- Raw files support: `src/drafter/raw_files.py` (435KB file!)
- CLI supports `--additional-files` flag
- Examples show image loading (e.g., `examples/simple_image.py`, `examples/handle_image_upload.py`)

**Category:** Documentation Gap  
**Impact:** Low - Implementation exists but README question suggests it might not be complete  
**Resolution Needed:** Update README to describe how file handling actually works

---

### 15. ⚠️ **Production Mode and Image Folder** (Not Implemented)

**README States:**
Via the `deploy_site()` function documentation

**Actual Implementation:**
```python
def deploy_site(image_folder="images", server: Optional[ClientServer] = None):
    """
    Deploys the website with the given image folder. This will set the production
    flag to True and turn off debug information, too.
    """
    hide_debug_information(server=server)
    # TODO: Implement production mode and image folder in V2
    pass
```

**Category:** Codebase Incomplete  
**Impact:** Medium - Function exists but doesn't do what its docstring says  
**Resolution Needed:** Either:
  - Implement production mode and image folder handling
  - Update docstring to match current behavior
  - Remove the function if not needed

---

### 16. ⚠️ **DOM Structure Details** (Cannot Fully Verify)

**README States detailed DOM structure:**
> "The DOM structure of the site is as follows:
> - There's a top-level div tag with id `drafter-root--` that contains the entire site.
> - There's a div tag with id `drafter-site--` that contains the entire site.
> - Inside that is a `drafter-frame--` div..."

**Actual Implementation:**
- Structure is likely generated by TypeScript client: `js/src/bridge/client.ts`
- Assets exist: `src/drafter/assets/js/` with CSS files
- Cannot fully verify without running and inspecting the browser

**Category:** Needs Manual Verification  
**Impact:** Low - Implementation likely correct but needs browser inspection  
**Resolution Needed:** Manual testing to verify DOM structure matches documentation

---

## Summary of Issues by Category

### Critical Issues (High Impact)
1. **Missing Dependencies in pyproject.toml** - Package won't install correctly
2. **AppBuilder Class Architecture** - Documented class doesn't exist

### Important Issues (Medium Impact)
3. **Terminology Mismatch (BridgeClient vs ClientBridge)** - Confusing for developers
4. **CLI Documentation Outdated** - Users won't know correct commands
5. **Outcome Implementation Unclear** - Core architectural component needs clarification
6. **Limited Test Coverage** - Quality assurance concern

### Minor Issues (Low Impact)
7. **Response Payload Types** - Word "eventually" is outdated
8. **State History** - Old vs new implementation unclear
9. **Site Configuration** - Documentation gap
10. **File Handling** - Works but not fully documented
11. **deploy_site() Function** - Has TODO, doesn't match docstring

### Future Work (Documented as Planned)
12. **URL Path Support with Slashes** - Correctly documented as future feature

---

## Recommended Actions

### Immediate (Required for V2.0 Release)
1. ✅ **Fix pyproject.toml dependencies**
   - Add typer, rich, starlette, uvicorn to main dependencies
   
2. ✅ **Update terminology throughout README**
   - Change all instances of "BridgeClient" to "ClientBridge"
   - Clarify AppBuilder/AppServer vs actual implementation
   
3. ✅ **Update CLI documentation**
   - Document `drafter build` and `drafter serve` commands
   - Include all command-line options

### High Priority
4. ⚠️ **Clarify Outcome implementation**
   - Document whether it's only a telemetry event or should be a data class
   - Implement data class if needed

5. ⚠️ **Resolve deploy_site() function**
   - Either implement the TODO or update/remove the function

6. ⚠️ **Document history module status**
   - Clarify relationship between `history/` and `old_history.py`
   - Mark deprecated code or explain migration

### Medium Priority
7. 📝 **Expand documentation**
   - Add file handling documentation
   - Document build process details (Skulpt vs static)
   - Clarify Site vs Configuration relationship

8. 🧪 **Testing**
   - Add more tests or document testing strategy
   - Clarify role of Bakery vs pytest

### Low Priority
9. ✨ **Manual verification**
   - Test debug UI features
   - Verify DOM structure in browser
   - Check all response payload types work correctly

---

## Conclusion

The Drafter 2.0 codebase is substantially implemented and functional. The main inconsistencies are:

1. **Documentation lags behind implementation** - Some features are implemented but the README uses outdated terminology or describes future features that now exist
2. **Missing infrastructure** - Dependencies missing from pyproject.toml
3. **Architectural terminology** - Names in README don't match code (BridgeClient vs ClientBridge, AppBuilder vs CLI functions)
4. **Incomplete features** - A few functions like `deploy_site()` have TODOs

Most issues are **README being outdated** rather than codebase being incomplete. The core architecture described in the README is implemented, but the documentation needs updating to match the actual implementation.
