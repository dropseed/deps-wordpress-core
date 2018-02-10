import re
from os import path
import json
import sys

from bs4 import BeautifulSoup
import requests


def collect():
    wordpress_path = sys.argv[1]

    version_php_path = path.join('/repo', wordpress_path, 'wp-includes/version.php')

    with open(version_php_path, 'r') as f:
        content = f.read()
        found = re.search(r'^\$wp_version = \'(.*)\';$', content, re.MULTILINE)
        version_installed = found.groups()[0]

    releases_html = requests.get('https://wordpress.org/download/release-archive/').text
    soup = BeautifulSoup(releases_html, 'html.parser')

    available_versions = []

    for tbody in soup.find_all('tbody'):
        for tr in tbody.find_all('tr'):
            # get first td that has version number
            td = tr.find('td')
            version = td.text
            available_versions.append(version)

    schema_output = json.dumps({
        'manifests': {
            path.relpath(path.abspath(wordpress_path), '/repo'): {
                'current': {
                    'dependencies': {
                        'WordPress': {
                            'constraint': version_installed,
                            'available': [{'name': x} for x in available_versions],
                            'source': 'wordpress-core',
                        }
                    }
                }
            }
        }
    })
    print(f'<Dependencies>{schema_output}</Dependencies>')
