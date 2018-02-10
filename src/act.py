import os
import json
from subprocess import run
import tempfile


def act():
    # An actor will always be given a set of "input" data, so that it knows what
    # exactly it is supposed to update. That JSON data will be stored in a file
    # at /dependencies/input_data.json for you to load.
    with open('/dependencies/input_data.json', 'r') as f:
        data = json.load(f)

    # TODO `pullrequest start` could do this, take care of safe branch names, naming consistency, etc.
    branch_name = 'deps/update-job-{}'.format(os.getenv('JOB_ID'))
    run(['git', 'checkout', os.getenv('GIT_SHA')], check=True)
    run(['git', 'checkout', '-b', branch_name], check=True)

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

            repo_content = repo_wordpress_path('wp-content')
            run(f'cp -r {version_directory}/wordpress/wp-content/* {repo_content}', shell=True)

            wordpress_root = repo_wordpress_path('.')
            run(f'cp -r {version_directory}/wordpress/* {wordpress_root}', shell=True)

            run(['git', 'add', repo_wordpress_path('.')], check=True)
            run(['git', 'commit', '-m', 'Update {} from {} to {}'.format(dependency_name, installed, version_to_update_to)], check=True)

    if os.getenv('DEPENDENCIES_ENV') != 'test':
        # TODO have pullrequest do this too?
        run(['git', 'push', '--set-upstream', 'origin', branch_name], check=True)

    fp = tempfile.NamedTemporaryFile(delete=False)
    fp.write(json.dumps(data).encode('utf-8'))
    fp.close()
    run(
        [
            'pullrequest',
            '--branch', branch_name,
            '--dependencies-json', fp.name,
        ],
        check=True
    )
