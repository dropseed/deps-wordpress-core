import os
import json
from subprocess import run

from utils import write_json_to_temp_file


COPY_WP_CONTENT = os.getenv('SETTING_COPY_WP_CONTENT', 'false') == 'true'


def act():
    with open('/dependencies/input_data.json', 'r') as f:
        data = json.load(f)

    run(['deps', 'branch'], check=True)

    for manifest_path, manifest_data in data.get('manifests', {}).items():
        for dependency_name, updated_dependency_data in manifest_data['updated']['dependencies'].items():
            assert dependency_name.lower() == 'wordpress', 'Only works on the "WordPress" dependency'

            installed = manifest_data['current']['dependencies'][dependency_name]['constraint']
            version_to_update_to = updated_dependency_data['constraint']

            version_directory = f'/tmp/wordpress/{version_to_update_to}'
            run(f'mkdir -p {version_directory} && curl https://wordpress.org/wordpress-{version_to_update_to}.tar.gz | tar xz -C {version_directory}/', shell=True, check=True)

            def repo_wordpress_path(p):
                return os.path.join('/repo', manifest_path, p)

            run(['rm', '-r', repo_wordpress_path('wp-includes')], check=True)
            run(['rm', '-r', repo_wordpress_path('wp-admin')], check=True)
            run(['cp', '-r', os.path.join(version_directory, 'wordpress/wp-includes'), repo_wordpress_path('wp-includes')], check=True)
            run(['cp', '-r', os.path.join(version_directory, 'wordpress/wp-admin'), repo_wordpress_path('wp-admin')], check=True)

            if COPY_WP_CONTENT:
                repo_content = repo_wordpress_path('wp-content')
                run(f'cp -r {version_directory}/wordpress/wp-content/* {repo_content}', shell=True)

            wordpress_root = repo_wordpress_path('.')
            run(f'cp {version_directory}/wordpress/* {wordpress_root}', shell=True)

            run(['deps', 'commit', '-m', 'Update {} from {} to {}'.format(dependency_name, installed, version_to_update_to), repo_wordpress_path('.')], check=True)

    run(['deps', 'pullrequest', write_json_to_temp_file(data)], check=True)
