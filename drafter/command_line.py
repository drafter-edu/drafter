"""

You can run drafter in command line mode to build your site:

```
python -m drafter build <site_file.py> --output <output_directory>
```

Can control the following:
- Input filename
- Output directory (defaults to ./)
- Output filename (defaults to index.html)
- Whether to create a 404.html file (can also make it created if it does not exist)
- Specific additional files to include
- Whether to add a warning if the set_site_information is missing
- Optional external pages to provide links to in the generated site
    - E.g., the Github repository for this site, code coverage

Some work that needs to be done:
- Create the 404 file with the right data
- Create the main output file with the right data
"""
from dataclasses import dataclass
from drafter import ServerConfiguration, protect_script_tags
from drafter.files import DEPLOYED_404_TEMPLATE_HTML, TEMPLATE_SKULPT_DEPLOY
from drafter.raw_files import get_raw_files

import pathlib
import os
import argparse
from typing import Any

@dataclass
class BuildOptions:
    site_file: str
    additional_files: list[str]
    external_pages: list[str]
    output_directory: str
    output_filename: str
    create_404: str
    warn_missing_info: bool
    server_configuration: ServerConfiguration

    CREATE_404_OPTIONS = ["always", "never", "if_missing"]

SK_TEMPLATE_LINE = "Sk.builtinFiles.files[{filename!r}] = {content!r};\n"

def build_site(options: BuildOptions) -> None:
    """
    Builds a static website from the given site file.
    """
    if not os.path.exists(options.site_file):
        raise FileNotFoundError(f"Site file {options.site_file} does not exist.")

    js_lines = []

    with open(options.site_file, 'r') as f:
        site_code = f.read()
    site_code = protect_script_tags(site_code)
    js_lines.append(SK_TEMPLATE_LINE.format(filename="main.py", content=site_code))
    print("Adding site file", options.site_file)

    for filename in options.additional_files:
        if not os.path.exists(filename):
            print(f"ERROR - Additional file {filename} does not exist.")
        with open(filename, 'r') as f:
            try:
                content = f.read()
            except:
                print(f"Failed to read file {filename} - skipping.")
                continue
            content = protect_script_tags(content)
            if filename.startswith("./dist/"):
                filename = "./" + filename[len("./dist/"):]
            js_lines.append(SK_TEMPLATE_LINE.format(filename=filename, content=content))
            print("Adding additional file", filename)

    os.makedirs(options.output_directory, exist_ok=True)

    environment_variables = []
    if options.warn_missing_info:
        environment_variables.append(("DRAFTER_MUST_HAVE_SITE_INFORMATION", True))
    if options.external_pages:
        # Convert list of external pages to semicolon-separated string
        external_pages_str = ";".join(options.external_pages)
        environment_variables.append(("DRAFTER_EXTERNAL_PAGES", external_pages_str))
    environment_settings = build_environment(environment_variables)

    setup_files = list(get_raw_files('global').deploy.values())
    setup_files.append("<script>"+environment_settings+"</script>")
    setup_code = "\n".join(setup_files)


    complete_website = TEMPLATE_SKULPT_DEPLOY.format(
        cdn_skulpt=options.server_configuration.cdn_skulpt,
        cdn_skulpt_std=options.server_configuration.cdn_skulpt_std,
        cdn_skulpt_drafter=options.server_configuration.cdn_skulpt_drafter,
        website_setup=setup_code,
        website_code = "".join(js_lines),
        external_pages=options.external_pages,
    )

    output_path = os.path.join(options.output_directory, options.output_filename)
    with open(output_path, 'w') as f:
        f.write(complete_website)
    print(f"Wrote main output file to {output_path}")

    need_404 = options.create_404 == "if_missing" and not os.path.exists(os.path.join(options.output_directory, '404.html'))
    if options.create_404 == "always" or need_404:
        output_404_path = os.path.join(options.output_directory, '404.html')
        with open(output_404_path, 'w') as f:
            f.write(DEPLOYED_404_TEMPLATE_HTML)
        print(f"Wrote 404 file to {output_404_path}")


    # Need to add warning if the set_site_information is missing
    # Need to handle the additional external links getting added to the about

SKULPT_ENV_VAR_TEMPLATE = 'Sk.environ.set$item(new Sk.builtin.str("{name}"), {value});'
def build_environment(variables: list[tuple[str, Any]]) -> str:
    lines = []
    for key, value in variables:
        if isinstance(value, str):
            js_value = f'new Sk.builtin.str("{value}")'
        elif value == True:
            js_value = "Sk.builtin.bool.true$"
        elif value == False:
            js_value = "Sk.builtin.bool.false$"
        else:
            raise ValueError(f"Unsupported environment variable type: {type(value)} for {key}")
        lines.append(SKULPT_ENV_VAR_TEMPLATE.format(name=key, value=js_value))
    return "\n".join(lines)

class ServerConfigurationParser:
    def __init__(self, parsed_server_args):
        self._server_config_args = {}
        for server_arg in parsed_server_args.server:
            if '=' in server_arg:
                key, value = server_arg.split('=', 1)
                self._server_config_args[key] = value
            else:
                raise ValueError(f"Invalid server configuration argument: {server_arg}")

    def parse_server_arg(self, name: str, value_type: type) -> tuple[str, Any]:
        if name in self._server_config_args:
            raw_value = self._server_config_args[name]
            if value_type == bool:
                parsed_value = raw_value.lower() in ['true', '1', 'yes']
            elif value_type == list:
                parsed_value = raw_value.split(',')
            else:
                parsed_value = value_type(raw_value)
            self._server_config_args[name] = parsed_value

    def finalize(self) -> ServerConfiguration:
        return ServerConfiguration(**self._server_config_args)


def parse_args(args) -> BuildOptions:
    parser = argparse.ArgumentParser(description="Build a static website from a Drafter site file.")
    parser.add_argument("site_file", help="The Drafter site file to build the website from.")
    parser.add_argument("--additional-files", default=[], help="Additional files to include in the output.", action="append")
    parser.add_argument("--external-pages", action='append', default=[], help="External pages to link to in the generated site.")
    parser.add_argument("--output-directory", default="./", help="The directory to output the built website to.")
    parser.add_argument("--output-filename", default="index.html", help="The filename for the main output HTML file.")
    parser.add_argument("--create-404", choices=BuildOptions.CREATE_404_OPTIONS, default="if_missing",
                        help="Whether to create a 404.html file.")
    parser.add_argument("--warn-missing-info", action='store_true', help="Warn if set_site_information is missing.")
    parser.add_argument("--server", action='append', default=[],
                        help="Set server configuration options in the format key=value.")

    parsed_args = parser.parse_args(args)

    sc = ServerConfigurationParser(parsed_args)
    sc.parse_server_arg("host", str)
    sc.parse_server_arg("port", int)
    sc.parse_server_arg("debug", bool)
    sc.parse_server_arg("backend", str)
    sc.parse_server_arg("reloader", bool)
    sc.parse_server_arg("skip", bool)
    sc.parse_server_arg("title", str)
    sc.parse_server_arg("framed", bool)
    sc.parse_server_arg("skulpt", bool)
    sc.parse_server_arg("style", str)
    sc.parse_server_arg("src_image_folder", str)
    sc.parse_server_arg("save_uploaded_files", bool)
    sc.parse_server_arg("deploy_image_path", str)
    sc.parse_server_arg("cdn_skulpt", str)
    sc.parse_server_arg("cdn_skulpt_std", str)
    sc.parse_server_arg("cdn_skulpt_drafter", str)
    sc.parse_server_arg("cdn_skulpt_setup", str)

    server_configuration = sc.finalize()
    print(server_configuration)

    return BuildOptions(
        site_file=parsed_args.site_file,
        additional_files=parsed_args.additional_files,
        external_pages=parsed_args.external_pages,
        output_directory=parsed_args.output_directory,
        output_filename=parsed_args.output_filename,
        create_404=parsed_args.create_404,
        warn_missing_info=parsed_args.warn_missing_info,
        server_configuration=server_configuration
    )

def main():
    import sys
    options = parse_args(sys.argv[1:])
    build_site(options)

if __name__ == "__main__":
    main()


