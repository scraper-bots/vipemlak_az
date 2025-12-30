import asyncio
import aiohttp
from bs4 import BeautifulSoup
import csv
import re
from dataclasses import dataclass, asdict
from typing import Optional, List
import hashlib
from urllib.parse import urljoin, unquote
from enum import Enum

BASE_URL = "https://vipemlak.az"


class PropertyCategory(Enum):
    YENI_TIKILI = "yeni-tikili"  # New buildings
    KOHNE_TIKILI = "kohne-tikili"  # Old buildings


@dataclass
class Listing:
    url: str
    title: str
    category: Optional[str] = None  # yeni-tikili or kohne-tikili
    property_type: Optional[str] = None
    rooms: Optional[str] = None
    area: Optional[str] = None
    price: Optional[str] = None
    price_per_sqm: Optional[str] = None
    district: Optional[str] = None
    settlement: Optional[str] = None
    address: Optional[str] = None
    floor: Optional[str] = None
    description: Optional[str] = None
    phone: Optional[str] = None
    agent_name: Optional[str] = None
    date: Optional[str] = None


def extract_listing_urls(html: str, category: str = None) -> List[dict]:
    """Extract listing URLs and basic info from the main page HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    listings = []

    for item in soup.select('div.pranto.prodbig'):
        link = item.select_one('a')
        if link and link.get('href'):
            href = link.get('href')
            full_url = urljoin(BASE_URL, href)
            title = link.get('title', '')

            # Extract price from the listing card
            price_elem = item.select_one('span.sprice')
            price = price_elem.get_text(strip=True) if price_elem else None

            listings.append({
                'url': full_url,
                'title': title,
                'price_preview': price,
                'category': category
            })

    return listings


def generate_hash(listing_id: str, referer: str) -> str:
    """Generate the hash needed for the phone number AJAX request."""
    # The hash appears to be MD5 of some combination
    # Based on the example: id=776330, h=adb4cac911806732c6abc7d6b9e81bb8
    # This is likely server-generated, we'll need to extract it from the page
    return ""


async def fetch_page(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch a page and return its HTML content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    async with session.get(url, headers=headers) as response:
        return await response.text()


async def fetch_phone_number(
    session: aiohttp.ClientSession,
    listing_id: str,
    hash_value: str,
    referer: str
) -> Optional[str]:
    """Fetch the phone number via AJAX POST request."""
    url = f"{BASE_URL}/ajax.php"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': BASE_URL,
        'Referer': referer,
        'X-Requested-With': 'XMLHttpRequest',
    }

    data = {
        'act': 'telshow',
        'id': listing_id,
        't': 'homeobject',
        'h': hash_value,
        'rf': referer.replace(BASE_URL + '/', '')
    }

    try:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 200:
                json_data = await response.json()
                if json_data.get('ok') == 1:
                    return json_data.get('tel')
    except Exception as e:
        print(f"Error fetching phone for listing {listing_id}: {e}")

    return None


def parse_detail_page(html: str, url: str) -> Listing:
    """Parse the detail page and extract all listing information."""
    soup = BeautifulSoup(html, 'html.parser')
    listing = Listing(url=url, title='')

    # Extract title
    title_elem = soup.select_one('h1')
    if title_elem:
        listing.title = title_elem.get_text(strip=True)

    # Parse the info table
    info_div = soup.select_one('div#openhalf')
    if info_div:
        # Extract key-value pairs from infotd/infotd2 pattern
        info_items = info_div.select('div.infotd')
        info_values = info_div.select('div.infotd2')

        for i, item in enumerate(info_items):
            label = item.get_text(strip=True)
            if i < len(info_values):
                value = info_values[i].get_text(strip=True)

                if 'Əmlakın növü' in label:
                    listing.property_type = value
                elif 'Otaq sayı' in label:
                    listing.rooms = value
                elif 'Sahə' in label:
                    listing.area = value
                elif 'Qiymət' in label:
                    # Extract main price
                    price_elem = info_values[i].select_one('span.pricecolor')
                    if price_elem:
                        listing.price = price_elem.get_text(strip=True)
                    # Extract price per sqm
                    price_sqm = info_values[i].select_one('span.pricekv')
                    if price_sqm:
                        listing.price_per_sqm = price_sqm.get_text(strip=True)

        # Extract address from infotd100
        address_div = info_div.select_one('div.infotd100')
        if address_div:
            # Parse address parts
            address_text = address_div.get_text(separator=' ', strip=True)
            listing.address = address_text.split('Ünvan:')[-1].strip() if 'Ünvan:' in address_text else address_text

            # Try to extract district and settlement from spans
            spans = address_div.select('span.sep')
            text_parts = address_div.get_text(separator='|', strip=True).split('|')

            for part in text_parts:
                part = part.strip()
                if 'rayonu' in part.lower():
                    listing.district = part
                elif 'qəs.' in part.lower() or 'qəsəbəsi' in part.lower():
                    listing.settlement = part

        # Extract description from second infotd100
        description_divs = info_div.select('div.infotd100')
        for div in description_divs:
            if 'Ümumi məlumat' in div.get_text():
                listing.description = div.get_text(strip=True).replace('Ümumi məlumat', '').strip()
                break

        # Extract agent name
        contact_div = info_div.select_one('div.infocontact')
        if contact_div:
            agent_link = contact_div.select_one('a[href*="/user/"]')
            if agent_link:
                listing.agent_name = agent_link.get_text(strip=True).replace('(Bütün Elanları)', '').strip()

        # Extract date
        date_span = info_div.select_one('span.viewsbb')
        if date_span:
            date_text = date_span.get_text(strip=True)
            if 'Tarix:' in date_text:
                listing.date = date_text.replace('Tarix:', '').strip()

    return listing


def extract_phone_hash(html: str) -> tuple:
    """Extract the listing ID and hash from the page for phone number request."""
    soup = BeautifulSoup(html, 'html.parser')

    tel_div = soup.select_one('div#telshow')
    if tel_div:
        listing_id = tel_div.get('data-id')
        hash_value = tel_div.get('data-h')
        rf_value = tel_div.get('data-rf', '')
        return listing_id, hash_value, unquote(rf_value)

    return None, None, None


async def scrape_listing(session: aiohttp.ClientSession, listing_info: dict) -> Optional[Listing]:
    """Scrape a single listing's detail page."""
    url = listing_info['url']
    category = listing_info.get('category')

    try:
        print(f"Scraping: {url}")
        html = await fetch_page(session, url)

        # Parse the detail page
        listing = parse_detail_page(html, url)
        listing.category = category

        # Extract phone hash and fetch phone number
        listing_id, hash_value, rf = extract_phone_hash(html)
        if listing_id and hash_value:
            phone = await fetch_phone_number(session, listing_id, hash_value, url)
            listing.phone = phone

        return listing

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


async def scrape_main_page(
    session: aiohttp.ClientSession,
    category: str,
    start: int = 0
) -> List[dict]:
    """Scrape the main listing page to get all listing URLs."""
    url = f"{BASE_URL}/{category}/?start={start}"
    html = await fetch_page(session, url)
    return extract_listing_urls(html, category)


async def scrape_all_pages(
    session: aiohttp.ClientSession,
    categories: List[str],
    max_pages_per_category: int = 10
) -> List[dict]:
    """Scrape multiple pages of listings for all categories."""
    all_listings = []

    for category in categories:
        print(f"\n{'='*50}")
        print(f"Scraping category: {category}")
        print('='*50)

        for page in range(max_pages_per_category):
            start = page * 20  # 20 listings per page
            print(f"Fetching {category} page {page + 1} (start={start})...")

            listings = await scrape_main_page(session, category, start)
            if not listings:
                print(f"No more listings found for {category}")
                break

            all_listings.extend(listings)
            await asyncio.sleep(0.5)  # Be polite to the server

    return all_listings


def save_to_csv(listings: List[Listing], filename: str = 'vipemlak_listings.csv'):
    """Save listings to a CSV file."""
    if not listings:
        print("No listings to save.")
        return

    fieldnames = [
        'url', 'title', 'category', 'property_type', 'rooms', 'area', 'price',
        'price_per_sqm', 'district', 'settlement', 'address',
        'floor', 'description', 'phone', 'agent_name', 'date'
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for listing in listings:
            writer.writerow(asdict(listing))

    print(f"Saved {len(listings)} listings to {filename}")


async def main(
    categories: List[str] = None,
    max_pages_per_category: int = 5,
    concurrent_limit: int = 5
):
    """Main scraping function.

    Args:
        categories: List of property categories to scrape (e.g., ['yeni-tikili', 'kohne-tikili'])
        max_pages_per_category: Maximum number of pages to scrape per category
        concurrent_limit: Maximum concurrent requests
    """
    if categories is None:
        categories = [
            PropertyCategory.YENI_TIKILI.value,
            PropertyCategory.KOHNE_TIKILI.value
        ]

    connector = aiohttp.TCPConnector(limit=concurrent_limit)

    async with aiohttp.ClientSession(connector=connector) as session:
        # Get all listing URLs from main pages
        print("Fetching listing URLs from main pages...")
        listing_infos = await scrape_all_pages(session, categories, max_pages_per_category)
        print(f"\nFound {len(listing_infos)} total listings across all categories")

        # Scrape each listing detail page
        print("\nScraping detail pages...")

        # Process in batches to avoid overwhelming the server
        batch_size = concurrent_limit
        all_listings = []

        for i in range(0, len(listing_infos), batch_size):
            batch = listing_infos[i:i + batch_size]
            tasks = [scrape_listing(session, info) for info in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Listing):
                    all_listings.append(result)
                elif isinstance(result, Exception):
                    print(f"Error: {result}")

            # Progress update
            print(f"Progress: {min(i + batch_size, len(listing_infos))}/{len(listing_infos)}")

            # Small delay between batches
            await asyncio.sleep(1)

        # Save to CSV
        save_to_csv(all_listings)

        return all_listings


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Scrape vipemlak.az property listings')
    parser.add_argument(
        '--categories',
        nargs='+',
        default=['yeni-tikili', 'kohne-tikili'],
        help='Property categories to scrape (default: yeni-tikili kohne-tikili)'
    )
    parser.add_argument(
        '--max-pages',
        type=int,
        default=5,
        help='Maximum pages to scrape per category (default: 5)'
    )
    parser.add_argument(
        '--concurrent',
        type=int,
        default=3,
        help='Maximum concurrent requests (default: 3)'
    )

    args = parser.parse_args()

    print(f"Starting scraper...")
    print(f"Categories: {args.categories}")
    print(f"Max pages per category: {args.max_pages}")
    print(f"Concurrent requests: {args.concurrent}")

    listings = asyncio.run(main(
        categories=args.categories,
        max_pages_per_category=args.max_pages,
        concurrent_limit=args.concurrent
    ))
    print(f"\nTotal listings scraped: {len(listings)}")
