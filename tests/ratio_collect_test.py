import requests
from bs4 import BeautifulSoup
import json
import time
import random

# Not working with simplize.vn as it blocks scraping

def try_convert_to_float(value_str):
    """
    Attempts to convert a string value to a float.
    Handles None, '-', and 'N/A' strings.
    """
    if value_str is None:
        return None
    value_str = value_str.strip()
    if value_str == '-' or value_str == 'N/A':
        return None
    try:
        value_str = value_str.replace('%', '') # Remove percentage if any (though not typical for P/E, P/B)
        return float(value_str)
    except ValueError:
        print(f"Warning: Could not convert '{value_str}' to float.")
        return None

def get_random_user_agent():
    """
    Returns a random user agent from a predefined list
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    ]
    return random.choice(user_agents)

def get_headers():
    """
    Returns a dictionary of headers that mimic a real browser
    """
    return {
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers',
        'DNT': '1'  # Do Not Track request header
    }

def scrape_industry_financial_ratios_from_url(session, url):
    """
    Fetches HTML from a URL and scrapes industry names, P/E, and P/B ratios.

    Args:
        session (requests.Session): The session object to use for requests.
        url (str): The URL of the webpage to scrape.

    Returns:
        list: A list of dictionaries, where each dictionary contains:
              'name' (str): The name of the industry or sub-category.
              'P/E' (float or None): The P/E ratio.
              'P/B' (float or None): The P/B ratio.
              Returns an empty list if the page cannot be fetched, the main data table
              is not found, or in case of other errors.
    """
    results = []
    try:
        # Add a random delay before each request (1-3 seconds)
        time.sleep(random.uniform(1, 3))
        
        # Send an HTTP GET request to the URL using the session
        headers = get_headers()
        response = session.get(url, headers=headers, timeout=15)  # Increased timeout
        
        # Check if we got a 403 error
        if response.status_code == 403:
            print(f"Error 403 Forbidden when accessing {url}")
            print("The website may be blocking scraping attempts.")
            print("Trying again with different headers...")
            
            # Wait a bit longer and try again with different headers
            time.sleep(random.uniform(3, 5))
            headers = get_headers()  # Get new headers
            response = session.get(url, headers=headers, timeout=15)
        
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        html_content = response.content
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return results  # Return empty list on fetch error

    soup = BeautifulSoup(html_content, 'html.parser')

    # The main data table body has the class 'simplize-table-tbody'
    table_body = soup.find('tbody', class_='simplize-table-tbody')

    if not table_body:
        # Fallback if the primary class is not found
        table_container_div = soup.find('div', class_='simplize-table-body')
        if table_container_div:
            table_tag = table_container_div.find('table')
            if table_tag:
                table_body = table_tag.find('tbody')

    if not table_body:
        print(f"Warning: Data table body not found in HTML from {url}.")
        return results

    rows = table_body.find_all('tr', class_='simplize-table-row')
    if not rows:
        rows = table_body.find_all('tr')  # Fallback to all <tr> if specific class not found
        if not rows:
            print(f"Warning: No rows found in the table body from {url}.")
            return results

    for i, row in enumerate(rows):
        cols = row.find_all('td', class_='simplize-table-cell')
        if not cols:
            cols = row.find_all('td')  # Fallback

        if len(cols) >= 5:  # Name, P/E, P/B are expected
            try:
                name_tag = cols[0].find('h6', class_='css-138qa5a')
                name = name_tag.text.strip() if name_tag else None

                pe_tag = cols[3].find('h6')  # P/E is in the 4th column (index 3)
                pe_value_str = pe_tag.text.strip() if pe_tag else None
                
                pb_tag = cols[4].find('h6')  # P/B is in the 5th column (index 4)
                pb_value_str = pb_tag.text.strip() if pb_tag else None

                if name:
                    results.append({
                        'name': name,
                        'P/E': try_convert_to_float(pe_value_str),
                        'P/B': try_convert_to_float(pb_value_str)
                    })
            except Exception as e:
                print(f"Error processing row {i+1} from {url}: {e}")
                continue
    return results

def get_sub_industry_links(session, main_industry_url):
    """
    Fetches the main industry page and extracts links to sub-industry pages.

    Args:
        session (requests.Session): The session object to use for requests.
        main_industry_url (str): The URL of the main industry listing page.

    Returns:
        list: A list of URLs for sub-industry pages. Returns empty list on error.
    """
    sub_industry_links = []
    try:
        # Add a random delay before each request (1-3 seconds)
        time.sleep(random.uniform(1, 3))
        
        headers = get_headers()
        response = session.get(main_industry_url, headers=headers, timeout=15)
        
        # Check if we got a 403 error
        if response.status_code == 403:
            print(f"Error 403 Forbidden when accessing {main_industry_url}")
            print("The website may be blocking scraping attempts.")
            print("Trying again with different headers...")
            
            # Wait a bit longer and try again with different headers
            time.sleep(random.uniform(3, 5))
            headers = get_headers()  # Get new headers
            response = session.get(main_industry_url, headers=headers, timeout=15)
            
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        table_body = soup.find('tbody', class_='simplize-table-tbody')
        if not table_body:
             # Fallback
            table_container_div = soup.find('div', class_='simplize-table-body')
            if table_container_div:
                table_tag = table_container_div.find('table')
                if table_tag:
                    table_body = table_tag.find('tbody')
        
        if not table_body:
            print(f"Could not find the main table body on {main_industry_url}")
            return sub_industry_links

        rows = table_body.find_all('tr', class_='simplize-table-row')
        if not rows: rows = table_body.find_all('tr')

        for row in rows:
            cols = row.find_all('td', class_='simplize-table-cell')
            if not cols: cols = row.find_all('td')

            if cols:
                link_tag = cols[0].find('a', class_='css-m9pfjn', href=True)
                if link_tag:
                    href = link_tag['href']
                    # Ensure the link is absolute
                    if href.startswith('/'):
                        base_site_url = main_industry_url.split('/co-phieu')[0]  # e.g. "https://simplize.vn"
                        full_url = base_site_url + href
                        sub_industry_links.append(full_url)
                    elif href.startswith('http'):
                        sub_industry_links.append(href)
        
        return list(set(sub_industry_links))  # Return unique links

    except requests.exceptions.RequestException as e:
        print(f"Error fetching main industry page {main_industry_url}: {e}")
        return sub_industry_links


if __name__ == '__main__':
    # --- Create a session object to maintain cookies across requests ---
    session = requests.Session()
    
    # --- URL for the main industry page ---
    base_url = "https://simplize.vn/co-phieu/nganh"
    all_data = {}  # Dictionary to store all scraped data

    print(f"--- Scraping main industry data from: {base_url} ---")
    main_industry_data = scrape_industry_financial_ratios_from_url(session, base_url)
    
    if main_industry_data:
        all_data['main_industries'] = main_industry_data
        print(f"Found {len(main_industry_data)} main industries.")
    else:
        print(f"No data scraped from the main industry page: {base_url}")

    # --- Get sub-industry links and scrape data from them ---
    print(f"\n--- Fetching sub-industry links from: {base_url} ---")
    sub_links = get_sub_industry_links(session, base_url)
    
    if sub_links:
        print(f"Found {len(sub_links)} sub-industry pages to scrape.")
        all_data['sub_industries'] = {}
        for link in sub_links:
            industry_name_from_link = link.split('/')[-1]  # Get a readable name from URL
            print(f"\n--- Scraping sub-category data from: {link} ---")
            sub_category_data = scrape_industry_financial_ratios_from_url(session, link)
            if sub_category_data:
                all_data['sub_industries'][industry_name_from_link] = sub_category_data
                print(f"Found {len(sub_category_data)} items for {industry_name_from_link}.")
            else:
                print(f"No data scraped from sub-category page: {link}")
    else:
        print("No sub-industry links found to scrape.")

    # --- Output all collected data in JSON format ---
    if all_data:
        print("\n\n--- All Scraped Data (JSON Output) ---")
        # Convert the list of dictionaries to a JSON string with indentation for readability
        json_output = json.dumps(all_data, indent=4, ensure_ascii=False)  # ensure_ascii=False for Vietnamese characters
        print(json_output)
        
        # Save to a file
        with open("industry_data.json", "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
        print("\nData also saved to industry_data.json")
    else:
        print("\nNo data was collected overall.")