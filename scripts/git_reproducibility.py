import subprocess
import datetime


def get_git_remote_url():
    remote_url = subprocess.check_output(["git", "config", "--get", "remote.origin.url"]).decode("utf-8").strip()
    # Remove the .git from the URL if present
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]

    branch_name = get_git_branch()
    full_branch_url = f"{remote_url}/tree/{branch_name}"
    return full_branch_url


def get_git_branch():
    return subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode("utf-8").strip()


def get_git_commit_sha():
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("utf-8").strip()


def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_git_author_name():
    return subprocess.check_output(["git", "log", "-1", "--pretty=format:%an"]).decode("utf-8").strip()


def get_unique_identifier():
    return (f"Branch: {get_git_remote_url()}, SHA: {get_git_commit_sha()}, "
            f"Author: {get_git_author_name()}, Timestamp: {get_current_timestamp()}")
