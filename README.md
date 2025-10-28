# Drafter

A simple Python library for making websites with a modern, full-stack architecture.

## Overview

Drafter is a student-friendly full-stack web development library that combines Python backend code with a TypeScript/JavaScript frontend, allowing users to create interactive web applications that run both as a local development server and as static deployments via Skulpt (Python-in-the-browser).

## Modern Build Architecture

Drafter uses a sophisticated modern Python application architecture with integrated frontend tooling:

### Package Management
- **[uv](https://github.com/astral-sh/uv)**: Ultra-fast Python package installer and resolver (alternative to pip/pip-tools)
- **pyproject.toml**: Modern Python packaging standard (PEP 621) with all metadata and dependencies
- **[Hatchling](https://hatch.pypa.io/)**: Modern, standards-based Python build backend
- **Custom Hatch Hook**: Integrates Node.js/TypeScript build pipeline into Python package builds

### Development Workflow
- **[just](https://github.com/casey/just)**: Command runner (modern alternative to Make) - see `Justfile` for available commands
- **[ruff](https://github.com/astral-sh/ruff)**: Fast Python linter and formatter (replaces flake8, black, isort)
- **[mypy](https://mypy-lang.org/)**: Static type checker for Python
- **[pre-commit](https://pre-commit.com/)**: Git hooks for automatic code quality checks

### Frontend Build System
- **TypeScript**: Type-safe frontend code in `js/src/`
- **[tsup](https://tsup.egoist.dev/)**: Fast TypeScript bundler (powered by esbuild)
- **Watch Mode**: Live rebuilds during development with automatic asset syncing
- **Asset Pipeline**: Compiled JS bundles copied to `src/drafter/assets/` for inclusion in Python package

### Build Integration
The build process seamlessly integrates Python and TypeScript:
1. **Development**: `npm run dev` in `js/` watches for changes and hot-reloads
2. **Package Build**: `hatch_build.py` automatically runs `npm ci && npm run build` during Python package builds
3. **Distribution**: Frontend assets are bundled into the Python wheel for easy installation

## Quick Start for Contributors

### Prerequisites
- Python 3.8+ 
- Node.js 18+ (LTS recommended)
- [uv](https://github.com/astral-sh/uv) (install via `pip install uv` or see uv docs)
- [just](https://github.com/casey/just) (optional but recommended)

### Setup Development Environment

```bash
# 1. Clone the repository
git clone https://github.com/drafter-edu/drafter.git
cd drafter

# 2. Install Python dependencies with uv
just dev-sync
# Or manually: uv sync --all-extras --cache-dir .uv_cache

# 3. Install pre-commit hooks
just install-hooks
# Or manually: uv run pre-commit install

# 4. Build frontend assets (one-time)
cd js
npm install
npm run build
cd ..
```

### Development Commands

Using `just` (recommended):
```bash
just           # Show all available commands
just format    # Format code with ruff
just lint      # Lint with ruff and mypy
just test      # Run tests with pytest
just validate  # Run format + lint + test
```

Or run tools directly:
```bash
uv run ruff format                                    # Format code
uv run ruff check --fix                               # Lint and auto-fix
uv run mypy --package drafter                         # Type check
uv run pytest                                         # Run tests
```

### Frontend Development Workflow

To work on the TypeScript/JavaScript client with live reloads:

1. In one terminal, watch and rebuild JS on changes:
```bash
cd js
npm run dev  # Watches, rebuilds, and syncs to src/drafter/assets/
```

2. In another terminal, run a Drafter example:
```bash
python examples/simplest.py
```

The dev server automatically reloads when assets change.

## Organization

If a user runs the program directly, then when it reaches `start_server`, it will start a local development server using Starlette.
This server will serve a single page that sets up Skulpt and a hot-reload connection to the server.
That page will also load the Drafter client library.
Finally, the page will also load the user's code into Skulpt and run it.
Effectively, this is running the program twice. The first time is "server side" with no real implications (other than starting the server, unit tests, print statements, etc.).
The second time is "client side" in Skulpt, where the user's code is actually run.
Images will assume to be available via the server.

If the program is then run via Skulpt, the Drafter client library will set up the page content.

If the `build` command is used, then it will instead generate static HTML, CSS, and JS files that can be deployed to any static hosting service.
The main `index.html` file will set up Skulpt and load the user's code into it, as well as load the Drafter client library to set up the page content.
It will try to precompile the library to populate as much meta information as it can, as well as an HTML preview that can be shown for SEO contexts.

We need to determine all of the dependencies of the project. The user should be able to provide an explicit list, but otherwise we assume that adjacent files will be possible to include.

## Drafter Client Library

This sets up the initial page structure and runs the user's code in Skulpt to generate the landing page.
The actual `start_server` is what sets up the page content.

Internal links and buttons will call the Skulpt functions to get the new content.

## Advanced Topics

### Custom Skulpt Builds

If you maintain a local Skulpt build, set the `SKULPT_DIR` environment variable to automatically use your custom build:

```bash
# In a .env file or export in shell
export SKULPT_DIR=/path/to/your/skulpt/dist
```

The build process will copy `skulpt.js`, `skulpt-stdlib.js`, and `skulpt.js.map` from your custom build directory.

### Building for Distribution

```bash
# Build a wheel for distribution
python -m build

# Or with uv
uv build
```

The build process automatically:
1. Runs `npm ci` or `npm install` in the `js/` directory
2. Executes `npm run build` to compile TypeScript
3. Copies compiled assets to `src/drafter/assets/`
4. Packages everything into a Python wheel

### Project Structure

```
drafter/
├── src/drafter/          # Python package source
│   ├── components/       # UI component definitions
│   ├── assets/          # Compiled JS/CSS (generated)
│   ├── bridge/          # Python-Skulpt bridge code
│   ├── scaffolding/     # Project templates
│   └── *.py            # Core library modules
├── js/                  # TypeScript/JS frontend
│   ├── src/            # TS source files
│   ├── scripts/        # Build automation scripts
│   └── dist/           # Compiled output (generated)
├── tests/              # Python test suite
├── examples/           # Example Drafter applications
├── docsrc/            # Sphinx documentation source
├── pyproject.toml     # Python package configuration
├── uv.lock           # Locked dependency versions
├── Justfile          # Task runner commands
└── hatch_build.py    # Custom build hook
```

## Future Improvements and Modernization Opportunities

The following areas have been identified for further modernization:

### High Priority
1. **Migrate CI/CD to uv**: Update GitHub Actions workflows to use `uv` instead of `pip` for faster installs
2. **Type Stubs for Skulpt**: Create or improve TypeScript definitions for better IDE support
3. **Automated Release Pipeline**: Implement automated version bumping and PyPI releases
4. **Documentation Modernization**: Migrate Sphinx docs to use modern theme and possibly explore MkDocs Material

### Medium Priority
5. **Dependency Updates**: Regularly update locked dependencies via `uv lock --upgrade`
6. **Test Coverage**: Expand test coverage, especially for the TypeScript client code
7. **ESLint/Prettier**: Add JavaScript linting to complement TypeScript checking
8. **Docker Development Environment**: Provide Dockerfile for consistent dev environments

### Low Priority / Future Exploration
9. **Monorepo Tooling**: Consider workspace-based approach if the project splits into multiple packages
10. **Performance Profiling**: Add benchmarks for build times and runtime performance
11. **Progressive Web App**: Explore PWA features for deployed applications
12. **WebAssembly**: Investigate WASM as an alternative to Skulpt for better performance

### Tooling Already Modernized ✓
- ✓ Modern Python packaging (pyproject.toml, PEP 621)
- ✓ Fast dependency management (uv)
- ✓ Integrated build system (Hatchling + custom hooks)
- ✓ Modern linting/formatting (ruff, mypy, pre-commit)
- ✓ Task runner (just)
- ✓ TypeScript with modern bundler (tsup/esbuild)
- ✓ Lockfile for reproducible builds (uv.lock)

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style (run `just format` and `just lint`)
4. Add tests for new functionality
5. Ensure all tests pass (`just test`)
6. Submit a pull request

The pre-commit hooks will automatically format and lint your code before each commit.

## License

MIT License - see LICENSE.txt for details.
