"""Minify resources."""

import json
import os
import re
from argparse import ArgumentParser
from glob import glob

from htmlmin import minify
from rcssmin import cssmin
from rjsmin import jsmin

# pylint: disable=too-few-public-methods

PARSER = ArgumentParser()
PARSER.add_argument(
    "-c",
    "--config-file",
    required=True,
    help="The JSON config file to specify which assets to compress",
)


def _htmlmin(content):
    return minify(content, remove_comments=True, remove_empty_space=True)


class Minifier:
    """Minifier for CSS, Javascript and HTML."""

    handlers = {
        "js": jsmin,
        "css": cssmin,
        "html": _htmlmin,
        "jinja2": _htmlmin,
    }

    @classmethod
    def minify(cls, instructions):
        """Minify resources found at specified paths.

        The instructions are provided as glob keys with dict values.

        By default `file.ext` is compressed to `file.min.ext`. This can be
        disabled by providing `in_place` in the settings dict for path.
        :param instructions: Globs to instructions in a dict
        """
        tasks = {}
        for path, handler, settings in cls._find_files(instructions):
            tasks[path] = (handler, settings)

        for path, (handler, settings) in tasks.items():
            cls._execute(path, handler, **settings)

    @classmethod
    def _ext(cls, filename):
        if not os.path.isfile(filename):
            return None

        base = os.path.basename(filename)
        if "." not in base:
            return None

        return base.rsplit(".", 1)[-1]

    @classmethod
    def _find_files(cls, instructions):
        for pattern, settings in instructions.items():
            for filename in glob(pattern, recursive=True):
                ext = cls._ext(filename)

                if filename.endswith(f".min.{ext}"):
                    continue

                handler = cls.handlers.get(ext)
                if not handler:
                    continue

                yield filename, handler, settings

    @classmethod
    def _execute(cls, path, handler, in_place=False):
        with open(path) as handle:
            content = handle.read()

        if not content:
            print("NOO", path)
            return

        minified = handler(content)

        target = path
        if not in_place:
            ext = cls._ext(target)
            target = re.sub(f"\\.{ext}$", f".min.{ext}", target)

        percent = int(1000 * len(minified) / len(content)) / 10.0
        print(path)
        print(f"\t-> {target} {len(content)} -> {len(minified)} ({percent}%)")

        with open(target, "w") as handle:
            handle.write(minified)


def main():
    """Script entry-point to compress assets."""

    args = PARSER.parse_args()
    config_file = args.config_file

    print(f"Loading config from {config_file}...")

    with open(config_file) as handle:
        config = json.load(handle)

    Minifier.minify(config)


if __name__ == "__main__":
    main()
