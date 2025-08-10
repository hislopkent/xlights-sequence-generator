import os, datetime


def build_version():
    # Prefer CI metadata
    pr = os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    pr_num = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_REF_NAME")
    sha = (os.environ.get("GITHUB_SHA") or "")[:7]
    run = os.environ.get("GITHUB_RUN_NUMBER")
    tag = os.environ.get("GITHUB_REF_NAME") if os.environ.get("GITHUB_REF_TYPE") == "tag" else None

    if tag:
        return f"{tag}"
    if pr and pr_num:
        return f"pr-{pr_num}.{run or '0'}+{sha}"
    if run and sha:
        return f"build.{run}+{sha}"
    # Local fallback: date stamp
    return datetime.datetime.utcnow().strftime("local.%Y%m%d%H%M")
