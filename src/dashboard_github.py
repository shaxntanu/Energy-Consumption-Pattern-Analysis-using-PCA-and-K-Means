"""The repository's star count, when GitHub is willing to say.

The star button shows a real number or no number at all. This module has the one
job of asking GitHub for it, and of being honest when the answer does not arrive:
there is no fabricated count, no placeholder, and no last-known value kept around
to fill the gap.

The answer legitimately may not come. The repository may be private, in which case
an unauthenticated request gets a 404. The machine running the app may have no
network. GitHub rate-limits anonymous callers to sixty requests an hour per
address, which the cache here keeps this well inside. In every one of those cases
the caller gets ``None`` and the button renders without a count.

No credential is read or sent. An authenticated request would report stars for a
private repository, but it would need a token in the deployment environment, and a
public dashboard is the wrong place to want one.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

import streamlit as st

_API = "https://api.github.com/repos/{path}"

# GitHub rejects requests with no User-Agent, and asks that it identify the
# caller. The Accept header pins the API version rather than taking the default.
_HEADERS = {
    "User-Agent": "energy-load-shape-study",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Long enough that a normal reader never waits on it twice, short enough that a
# new star shows up within the session. The request happens on the server, so a
# slow one delays the page: the timeout is deliberately impatient.
_TTL_SECONDS = 900
_TIMEOUT_SECONDS = 2.5


def repo_path(repo_url: str) -> str | None:
    """Turn a repository URL into the ``owner/name`` the API wants.

    Parsed rather than hard-coded so the button and the API call cannot end up
    pointing at different repositories. Anything that is not a github.com URL with
    both parts present returns None, which also keeps this from being talked into
    requesting some other host.

    Args:
        repo_url: The repository's web URL.

    Returns:
        ``owner/name``, percent-encoded, or None if the URL is not one.
    """
    try:
        parsed = urllib.parse.urlparse(repo_url)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        return None
    owner, name = parts[0], parts[1]
    if name.endswith(".git"):
        name = name[:-4]
    if not owner or not name:
        return None
    quote = urllib.parse.quote
    return f"{quote(owner, safe='')}/{quote(name, safe='')}"


@st.cache_data(ttl=_TTL_SECONDS, show_spinner=False)
def star_count(repo_url: str) -> int | None:
    """How many stars the repository has, or None if that cannot be established.

    Args:
        repo_url: The repository's web URL.

    Returns:
        The star count, or None when the repository is private, the network is
        unavailable, the response is not what this expects, or GitHub declines.
    """
    path = repo_path(repo_url)
    if path is None:
        return None

    request = urllib.request.Request(_API.format(path=path), headers=_HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            if response.status != 200:
                return None
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, ValueError):
        # URLError covers HTTP status errors and DNS failures; ValueError covers a
        # body that is not the JSON object this expects. None of them is worth
        # surfacing to a reader who came here to look at load shapes.
        return None

    if not isinstance(body, dict):
        return None
    count = body.get("stargazers_count")
    # A bool is an int in Python and would format as "True".
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        return None
    return count


def format_count(count: int) -> str:
    """The count as it appears on the button.

    Exact below a thousand, because on a repository this size every star is a
    person and rounding one of them away would be a small lie. Abbreviated above
    it, where the exact digit stops meaning anything - and truncated rather than
    rounded, so the button can never claim a star the repository has not been
    given.
    """
    if count < 1000:
        return str(count)
    if count < 10000:
        return f"{count // 100 / 10:.1f}k".replace(".0k", "k")
    return f"{count // 1000}k"
