import re
from os import path
import sys
from subprocess import run

from bs4 import BeautifulSoup
import requests
import semantic_version

from utils import write_json_to_temp_file


def collect():
    run(['deps', 'hook', 'before_update'], check=True)

    wordpress_path = sys.argv[1]

    version_php_path = path.join(wordpress_path, 'wp-includes/version.php')

    with open(version_php_path, 'r') as f:
        content = f.read()
        found = re.search(r'^\$wp_version = \'(.*)\';$', content, re.MULTILINE)
        version_installed = found.groups()[0]

    releases_html = requests.get('https://wordpress.org/download/releases/', allow_redirects=True).text
    soup = BeautifulSoup(releases_html, 'html.parser')

    available_versions = []

    for tr in soup.find_all('tr'):
        # get first td that has version number
        td = tr.find('td')
        version = td.text
        available_versions.append(version)

    # filter out anything below what is installed, use a list instead of set so it keeps order
    filtered = []
    for a in available_versions:
        try:
            if semantic_version.Version.coerce(a) > semantic_version.Version.coerce(version_installed):
                if a not in filtered:
                    filtered.append(a)
        except ValueError:
            # one of them is not a valid semver, it needs to be included as an option
            if a not in filtered:
                filtered.append(a)

    schema_output = {
        'manifests': {
            wordpress_path: {
                'current': {
                    'dependencies': {
                        'WordPress': {
                            'constraint': version_installed,
                            'available': [{'name': x} for x in filtered],
                            'source': 'wordpress-core',
                        }
                    }
                }
            }
        }
    }
    run(['deps', 'collect', write_json_to_temp_file(schema_output)], check=True)
