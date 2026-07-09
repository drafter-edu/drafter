This directory contains external data files that are bundled up with Drafter, for deployment purposes.

For example, the stylesheets, HTML templates, and JavaScript files that are used by the application live here.
If these files are changed, they must be rebuilt prior to release.

Essentially, the contents of this directory are serialized into strings and stored as the values
in the `files.py` module. This makes it easier to deploy the application in Skulpt, which has funky
ideas about file systems.

The `tools/rebuild_files.py` script is used to rebuild the `files.py` module. It reads the contents of
`external_data/manifest.json` and serializes that into the `raw_files.py` module as a dictionary.