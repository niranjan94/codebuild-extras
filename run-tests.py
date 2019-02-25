import os
import subprocess
import sys
import time
import traceback
from typing import List

import yaml
from github import Github
from github.PullRequest import PullRequest


def post_to_github(results: List[dict]):
    """
    Format and post the test results to github PR as a review comment.

    :param results:
    :return:
    """

    tests_info_body = ''
    has_failed = False
    for result in results:
        if result['status'] == 'passed':
            tests_info_body += f':white_check_mark: `{result["command"]}`\n'
        else:
            has_failed = True
            tests_info_body += f':x: `{result["command"]}`\n```{result["output"]}```\n<br>'

    pr_body = 'Whoopsie. Looks like there are some issues with this PR. :space_invader:' if \
        has_failed else 'This PR is good to go ! :tada:'

    pr_body += f'\n\n<details><summary><strong>Tests</strong></summary><p>\n\n{tests_info_body}\n</p></details>'

    try:
        source_repo = '/'.join(os.getenv('CODEBUILD_SOURCE_REPO_URL')[:-4].split('/')[-2:])
        source_commit_hash = os.getenv('CODEBUILD_RESOLVED_SOURCE_VERSION')
        source_pr = int(os.getenv('CODEBUILD_WEBHOOK_PR', '0'))

        if source_pr > 0:
            g = Github(os.getenv('GITHUB_API_TOKEN', ''))
            repo = g.get_repo(source_repo)
            pr: PullRequest = repo.get_pull(source_pr)

            print(
                f'Creating review comment: '
                f'pr -> {pr.title} // '
                f'commit -> {source_commit_hash} // '
                f'has_failed -> {has_failed}'
            )

            pr.create_review(
                repo.get_commit(sha=source_commit_hash),
                pr_body,
                'REQUEST_CHANGES' if has_failed else 'APPROVE'
            )
    finally:
        if has_failed:
            print('Test(s) failed.')
            exit(1)


def run_tests():
    """
    Parse the buildspec.yml and run the tests.

    :return:
    """
    with open('buildspec.yml', 'r') as stream:
        buildspec: dict = yaml.load(stream)
        test_commands = buildspec.get('tests', [])
        if len(test_commands) == 0:
            exit(0)

        results = []

        for test_command in test_commands:
            print(f'Running `{test_command}`')
            p = subprocess.Popen(test_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output = ''
            for c in iter(p.stdout.readline, b''):
                str_line = c if type(c) is str else c.decode('UTF-8')
                sys.stdout.write(str_line)
                output += str_line

            p.communicate()
            results.append({
                'command': test_command,
                'status': 'passed' if p.returncode == 0 else 'failed',
                'output': output
            })

        post_to_github(results)


if __name__ == '__main__':
    try:
        start_time = time.time()
        run_tests()
        time_taken_in_seconds = time.time() - start_time
        print('Time taken = {0} seconds '.format(time_taken_in_seconds))
    except Exception:
        print('Error occurred while running tests')
        traceback.print_exc()
