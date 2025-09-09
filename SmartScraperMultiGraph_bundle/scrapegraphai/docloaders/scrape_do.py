"""
Scrape_do module
"""

import os
import urllib.parse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def scrape_do_fetch(
    token, target_url, use_proxy=False, geoCode=None, super_proxy=False
):
    """
    Fetches the IP address of the machine associated with the given URL using Scrape.do.

    Args:
        token (str): The API token for Scrape.do service.
        target_url (str): A valid web page URL to fetch its associated IP address.
        use_proxy (bool): Whether to use Scrape.do proxy mode. Default is False.
        geoCode (str, optional): Specify the country code for
        geolocation-based proxies. Default is None.
        super_proxy (bool): If True, use Residential & Mobile Proxy Networks. Default is False.

    Returns:
        str: The raw response from the target URL.
    """
    encoded_url = urllib.parse.quote(target_url)
    if use_proxy:
        proxy_scrape_do_url = os.getenv("PROXY_SCRAPE_DO_URL", "proxy.scrape.do:8080")
        proxy_mode_url = f"http://{token}:@{proxy_scrape_do_url}"
        proxies = {
            "http": proxy_mode_url,
            "https": proxy_mode_url,
        }
        params = (
            {"geoCode": geoCode, "super": str(super_proxy).lower()} if geoCode else {}
        )
        response = requests.get(
            target_url, proxies=proxies, verify=False, params=params
        )
    else:
        api_scrape_do_url = os.getenv("API_SCRAPE_DO_URL", "api.scrape.do")
        url = f"http://{api_scrape_do_url}?token={token}&url={encoded_url}"
        response = requests.get(url)

    return response.text
