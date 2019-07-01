import re
from os import path
import sys
from subprocess import run
import json

import requests


def collect(input_path, output_path):
    wordpress_path = input_path

    version_php_path = path.join(wordpress_path, "wp-includes/version.php")

    with open(version_php_path, "r") as f:
        content = f.read()
        found = re.search(r"^\$wp_version = \'(.*)\';$", content, re.MULTILINE)
        version_installed = found.groups()[0]

    response = requests.get("https://api.wordpress.org/core/version-check/1.7/")
    response.raise_for_status()
    latest = response.json()["offers"][0]["version"]

    schema_output = {
        "manifests": {
            wordpress_path: {
                "current": {
                    "dependencies": {
                        "WordPress": {
                            "constraint": version_installed,
                            "source": "wordpress-core",
                        }
                    }
                }
            }
        }
    }

    if latest != version_installed:
        schema_output["manifests"][wordpress_path]["updated"] = {
            "dependencies": {
                "WordPress": {
                    "constraint": latest,
                    "source": "wordpress-core",
                }
            }
        }

    with open(output_path, "w+") as f:
        json.dump(schema_output, f)


if __name__ == "__main__":
    collect(sys.argv[1], sys.argv[2])
