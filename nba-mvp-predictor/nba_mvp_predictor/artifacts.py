import os
from datetime import datetime

import requests

from nba_mvp_predictor import conf, logger


def get_artifacts():
    """Obtains the artifacts from the GitHub project.

    Returns:
        dict: Dictionary of artifacts
    """
    github_repo = conf.web.github_repo
    url = f"https://api.github.com/repos/{github_repo}/actions/artifacts?per_page=100"
    auth = get_github_auth()
    artifacts = load_json_from_url(url, auth=auth)
    return artifacts


def load_json_from_url(url: str, auth=None):
    """Loads a JSON file from a URL into memory.

    Args:
        url (str): URL of the file

    Returns:
        dict: Dictionary parsed from the JSON file
    """
    response = requests.get(url, auth=auth)
    if response.status_code == 403:
        raise Exception(f"Error 403 when requesting {url} : {response.content}")
    return response.json()


def get_github_auth():
    """Obtains an authentication tuple for the GitHub API.

    Returns:
        (str, str): Tuple (username, token) to use in API calls
    """
    username = os.environ.get("GITHUB_USERNAME")
    token = os.environ.get("GITHUB_TOKEN")
    if not (username and token):
        raise ValueError("GitHub credentials not found. Make sure GITHUB_USERNAME and GITHUB_TOKEN are set.")
    return (username, token)


def get_last_artifact(artifact_name: str):
    """Obtains the last available artifact.

    Params:
        artifact_name: Name of the artifact to search for

    Returns:
        dict: Last available artifact (date:url)
    """
    artifacts = get_artifacts()
    num_artifacts = artifacts.get("total_count")
    logger.debug(f"{num_artifacts} artifacts available")
    if num_artifacts > 100:
        logger.warning("Some artifacts were not retrieved due to GitHub artifact pagination")
    artifacts = [
        a
        for a in artifacts.get("artifacts")
        if a.get("name") == artifact_name and not a.get("expired")
    ]
    logger.debug(f"{len(artifacts)} artifacts named {artifact_name}")
    results = dict()
    for artifact in artifacts:
        artifact_datetime = artifact.get("created_at")
        artifact_url = artifact.get("archive_download_url")
        artifact_datetime = datetime.strptime(artifact_datetime, "%Y-%m-%dT%H:%M:%SZ")
        results[artifact_datetime] = artifact_url
    try:
        last_result = sorted(results.items(), reverse=True)[0]
    except IndexError:
        raise IOError(f"No artifact found with name {artifact_name}")
    logger.debug(f"Last artifact : {last_result}")
    return last_result
