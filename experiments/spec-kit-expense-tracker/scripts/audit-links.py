import argparse
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

LINK = re.compile(r"!?\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")
BARE_URL = re.compile(r"https?://[^\s<>\])\"'`]+")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
REPO_URL = re.compile(
    r"https://github\.com/([^/]+)/([^/]+)/(?:(?:blob|tree)/([^/]+)/(.+))?"
)


def slugify(value):
    value = re.sub(r"[`*_~]", "", value).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"\s", "-", value)


def anchors(path):
    counts = {}
    result = set()
    for heading in HEADING.findall(path.read_text()):
        base = slugify(heading)
        count = counts.get(base, 0)
        counts[base] = count + 1
        result.add(base if count == 0 else f"{base}-{count}")
    return result


def documents(root, draft):
    for path in sorted(root.rglob("*.md")):
        if any(part in {"node_modules", "dist", ".capture-tmp"} for part in path.parts):
            continue
        yield path.relative_to(root).as_posix(), path.read_text(), path.parent
    if draft:
        data = json.loads(Path(draft).read_text())
        yield "Hashnode draft", data["content"]["markdown"], root / "article"


def github_target(url):
    match = REPO_URL.fullmatch(url.split("#")[0].rstrip("/"))
    if not match:
        return None
    owner, repo, ref, path = match.groups()
    if not ref:
        return None
    return owner, repo, ref, urllib.parse.unquote(path or "")


def check_github(url):
    owner, repo, ref, path = github_target(url)
    if not path:
        return True, "repository"
    try:
        subprocess.run(
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}/contents/{path}?ref={ref}",
                "--silent",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return True, "GitHub API"
    except subprocess.CalledProcessError as error:
        return False, error.stderr.strip() or "GitHub API lookup failed"


def check_http(url):
    headers = {"User-Agent": "experiment-link-audit/1.0"}
    try:
        request = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(request, timeout=25) as response:
            return 200 <= response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False, "HTTP 404"
    except Exception:
        pass
    try:
        request = urllib.request.Request(
            url, headers={**headers, "Range": "bytes=0-0"}, method="GET"
        )
        with urllib.request.urlopen(request, timeout=25) as response:
            return 200 <= response.status < 400, f"HTTP {response.status} via GET"
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except Exception as error:
        return False, f"{type(error).__name__}: {error}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--draft")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    occurrences = []
    remote = {}

    for name, text, base in documents(root, args.draft):
        links = [match.group(1) or match.group(2) for match in LINK.finditer(text)]
        plain_text = re.sub(r"`[^`\n]*`", "", re.sub(LINK, "", text))
        links += [url.rstrip(".,;") for url in BARE_URL.findall(plain_text)]
        for url in dict.fromkeys(links):
            record = {"document": name, "url": url}
            hostname = urllib.parse.urlparse(url).hostname or ""
            if hostname in {"example.com", "example.org", "example.net", "example.internal"} or url.startswith("https://github.com/example/"):
                record.update(status="illustrative example", ok=True)
                occurrences.append(record)
                continue
            if url.startswith(("http://", "https://")):
                target, fragment = (url.split("#", 1) + [""])[:2]
                if target.startswith(("http://localhost", "http://127.0.0.1")):
                    record.update(status="runtime URL", ok=True)
                else:
                    record["remote"] = target
                if fragment:
                    record["anchor"] = fragment
            elif url.startswith(("mailto:", "tel:", "data:")):
                record.update(status="scheme skipped", ok=True)
            else:
                target, fragment = (url.split("#", 1) + [""])[:2]
                destination = (base / urllib.parse.unquote(target)).resolve()
                try:
                    destination.relative_to(root)
                except ValueError:
                    destination = root / "__outside_experiment__"
                exists = destination.exists()
                record.update(
                    status="local target" if exists else "missing local target",
                    ok=exists,
                    resolved=destination.relative_to(root).as_posix()
                    if destination != root / "__outside_experiment__"
                    else str(destination),
                )
                if exists and fragment and destination.is_file():
                    valid = fragment in anchors(destination)
                    record.update(
                        status="local anchor" if valid else "missing local anchor",
                        ok=valid,
                        anchor=fragment,
                    )
            occurrences.append(record)

    urls = sorted({record["remote"] for record in occurrences if "remote" in record})
    for url in urls:
        if github_target(url):
            remote[url] = check_github(url)
        else:
            remote[url] = check_http(url)

    for record in occurrences:
        if "remote" in record:
            ok, status = remote[record["remote"]]
            record.update(ok=ok, status=status)
        record["ok"] = bool(record.get("ok", False))
    report = {
        "documents": len(list(documents(root, args.draft))),
        "occurrences": len(occurrences),
        "uniqueRemoteUrls": len(urls),
        "broken": [record for record in occurrences if not record["ok"]],
        "results": occurrences,
    }
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        f"Checked {report['documents']} documents, {len(occurrences)} links, "
        f"and {len(urls)} remote URLs; broken: {len(report['broken'])}"
    )
    for record in report["broken"]:
        print(f"BROKEN {record['document']}: {record['url']} ({record['status']})")
    return 1 if report["broken"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
