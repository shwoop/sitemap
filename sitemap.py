#!/usr/bin/python3.5
import aiohttp
import argparse
import asyncio
import re
import requests
from sys import stderr

SITE_RESPONSES = []
SITE_RESPONSES_LOCK = asyncio.Lock()


def eprint(*args, **kwargs):
    """ Print errors to stderr. """
    print(*args, file=stderr, **kwargs)


def get_sitemap(sitemap_url):
    """ Fetch requested sitemap. """
    r = requests.get(sitemap_url)
    if r.status_code != 200:
        eprint("Sitemap unavailable")
        exit(1)
    return r.text


def get_urls(sitemap_xml, regex):
    """ Extract urls from sitemap. """
    urls= [
        m.group(1) for m in map(regex.search, sitemap_xml.splitlines())
        if m is not None
    ]
    urls.sort()
    return urls


async def check_status_code(url):
    """ Asynchronously fetch url and record response code. """
    async with aiohttp.request("GET", url) as resp:
      async with SITE_RESPONSES_LOCK:
          SITE_RESPONSES.append((resp.status, url))


def check_sitemap():
    """ Asynchronously check response of urls present in target sitemap. """
    sitemap = get_sitemap(SITEMAP)
    r = re.compile(r"<loc>(.*)</loc>")
    urls = get_urls(sitemap, r)
    tasks = []
    for url in urls:
        tasks.append(asyncio.ensure_future(check_status_code(url)))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    for code, url in SITE_RESPONSES:
        if not CODES:
            print("%s%s%s" % (code, DEMARK, url))
        elif code in CODES:
            print("%s%s%s" % (code, DEMARK, url))


def handle_arguments():
    """ Command line arguments. """
    global CODES
    global DEMARK
    global SITEMAP
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-d",
        "--demark",
        type=str,
        default=" - ",
        help="set inter value demarkation characters. (default: \" - \").",
    )
    ap.add_argument(
        "-t",
        "--target",
        type=str,
        default="https://www.google.com/sitemap.xml",
        help=(
            "target url of sitemap (default: "
            "https://www.google.com/sitemap.xml)"
        )
    )
    ap.add_argument(
        "-c",
        "--codes",
        type=str,
        default=None,
        help=(
            "comma seperated list of response codes to report."
            "(defualt: all)"
        )
    )
    args = ap.parse_args()
    SITEMAP = args.target
    DEMARK = args.demark
    CODES = args.codes.split(",") if args.codes else None
    CODES = list(map(int, args.codes.split(","))) if args.codes else None


if __name__ == "__main__":
    handle_arguments()
    check_sitemap()
