.. _compatibility:

Deployed Site Compatibility
===========================

When deploying Drafter sites, especially with GitHub Pages and GitHub Actions, not all Python packages
are fully supported. This is due to the limitations of the GitHub Actions environment and the packages themselves.

The following Python features are known to have compatibility issues when used in Drafter sites deployed via GitHub Actions:

- **File Writing Operations**: Files are written to LocalStorage, which has size limits and will only persist per browser.
- **Threading and Multiprocessing**: This will not work
- **Match Statements**: This will not work
- **Walrus Operator (:=)**: This will not work
- **Template String Literals (t-strings)**: This will not work
- **Async/Await**: This will not work
- **Typing with Bitwise OR (|)**: This will not work

The following packages are known to have compatibility issues when used in Drafter sites deployed via GitHub Actions:

- **MatPlotLib**: Many core plotting functions are supported, but some more advanced features may have issues.
- **Pillow**: Basic image processing functions work, but some advanced features may not be supported.
- **Urllib/Gemini**: This will not work unless you set up a proxy server; see :ref:`llms` for more details.
- **NumPy**: Most core functionality works, although there may be some limitations with certain advanced operations.

The following packages are known to be incompatible when used in Drafter sites deployed via GitHub Actions:

- **Requests**: This will not work
- **Scipy**: This will not work
- **Pandas**: This will not work
- **Tkinter**: This will not work
- **Sqlite3**: This will not work
- **OpenCV**: This will not work
- **Plotly**: This will not work
- **Seaborn**: This will not work
- **Bokeh**: This will not work
- **Statsmodels**: This will not work
- **SymPy**: This will not work
- **PyTorch**: This will not work
- **TensorFlow**: This will not work
- **Beautiful Soup**: This will not work
- **Selenium**: This will not work
- **Scrapy**: This will not work

And of course, you cannot use any other web frameworks like Flask or Django within Drafter sites.