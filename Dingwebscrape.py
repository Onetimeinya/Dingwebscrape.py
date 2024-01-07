import asyncio
import random
import subprocess
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import aiohttp
from googlesearch import search as google_search

class SiteScraper:
    def __init__(self, email_list, use_theharvester=True, use_userrecon=True, use_additional_tools=True, custom_search_engines=None):
        self.email_list = email_list
        self.use_theharvester = use_theharvester
        self.use_userrecon = use_userrecon
        self.use_additional_tools = use_additional_tools
        self.custom_search_engines = custom_search_engines or [
            "https://www.google.com/search?q={}",
            "https://www.bing.com/search?q={}",
            "https://www.yahoo.com/search?q={}",
            "https://duckduckgo.com/search?q={}",
        ]
        self.results = {}

    async def fetch_url(self, session, url):
        try:
            headers = {
                'User-Agent': UserAgent().random,
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }

            async with session.get(url, headers=headers) as response:
                return await response.text()

        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    async def search_sites_for_email(self, email, session):
        try:
            for engine in self.custom_search_engines:
                search_url = engine.format(email)

                # Fetch the HTML content asynchronously with retries
                html_content = await self.fetch_url(session, search_url)

                if html_content:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    links = [a['href'] for a in soup.find_all('a', href=True)]

                    # Filter links that contain the email domain
                    filtered_links = [link for link in links if self.is_valid_link(link, email)]

                    self.results.setdefault(email, []).extend(filtered_links)

                    # Introduce a dynamic delay between requests based on the number of requests
                    await asyncio.sleep(self.get_dynamic_delay())
        except Exception as e:
            print(f"Error processing email {email}: {str(e)}")

    def is_valid_link(self, link, email):
        # Additional logic to validate and refine links
        email_domain = email.split('@')[1]
        return re.search(fr'\b{re.escape(email_domain)}\b', link) and not re.search(r'\.(jpg|png|gif|pdf)$', link)

    async def run_theharvester(self, email):
        try:
            theharvester_command = f"theharvester -d {email.split('@')[1]} -b all -f output_theharvester.html"
            subprocess.run(theharvester_command, shell=True, check=True)
            with open("output_theharvester.html", "r", encoding="utf-8") as file:
                content = file.read()

            soup = BeautifulSoup(content, 'html.parser')
            links = [a['href'] for a in soup.find_all('a', href=True)]
            self.results.setdefault(email, []).extend(links)

        except Exception as e:
            print(f"Error running theHarvester for email {email}: {str(e)}")

    async def run_userrecon(self, email):
        try:
            userrecon_command = f"userrecon -e {email} -o output_userrecon.txt"
            subprocess.run(userrecon_command, shell=True, check=True)
            with open("output_userrecon.txt", "r", encoding="utf-8") as file:
                content = file.read()

            # Extract relevant information from the userrecon output
            links = re.findall(r'https?://\S+', content)
            self.results.setdefault(email, []).extend(links)

        except Exception as e:
            print(f"Error running userrecon for email {email}: {str(e)}")

    async def run_additional_tools(self, email):
        try:
            # Implement additional tools for email scraping here
            # Example: Using Google search
            google_links = [link for link in google_search(email, num=5)]
            self.results.setdefault(email, []).extend(google_links)

            # Add more tools as needed

        except Exception as e:
            print(f"Error running additional tools for email {email}: {str(e)}")

    async def scrape_sites(self):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            tasks = [self.search_sites_for_email(email, session) for email in self.email_list]
            await asyncio.gather(*tasks)

            if self.use_theharvester:
                theharvester_tasks = [self.run_theharvester(email) for email in self.email_list]
                await asyncio.gather(*thharvester_tasks)

            if self.use_userrecon:
                userrecon_tasks = [self.run_userrecon(email) for email in self.email_list]
                await asyncio.gather(*userrecon_tasks)

            if self.use_additional_tools:
                additional_tools_tasks = [self.run_additional_tools(email) for email in self.email_list]
                await asyncio.gather(*additional_tools_tasks)

    def display_results(self):
        for email, links in self.results.items():
            print(f"\nSites associated with the email address {email}:")
            if links:
                for link in links:
                    print(link)
            else:
                print("Unable to retrieve search results.")

    def save_results_to_file(self, filename='search_results.txt'):
        try:
            with open(filename, 'w') as file:
                for email, links in self.results.items():
                    file.write(f"\nSites associated with the email address {email}:\n")
                    if links:
                        for link in links:
                            file.write(link + '\n')
                    else:
                        file.write("Unable to retrieve search results.\n")
            print(f"Results saved to {filename}")
        except Exception as e:
            print(f"Error saving results to file: {str(e)}")

    def get_dynamic_delay(self):
        # Introduce a more sophisticated dynamic delay logic based on the number of requests made
        base_delay = random.uniform(1.0, 2.0)
        num_requests = sum(len(links) for links in self.results.values())
        delay = base_delay + min(num_requests / 10, 3.0)  # Adjust as needed
        return delay

def get_email_list():
    try:
        email_list = input("Enter email addresses separated by commas: ").split(',')
        return [email.strip() for email in email_list]
    except KeyboardInterrupt:
        print("Cancelled by user.")

if __name__ == "__main__":
    try:
        email_list = get_email_list()

        use_theharvester = input("Use theHarvester tool? (y/n): ").lower() == 'y'
        use_userrecon = input("Use userrecon tool? (y/n): ").lower() == 'y'
        use_additional_tools = input("Use additional tools? (y/n): ").lower() == 'y'
        
        scraper = SiteScraper(email_list, use_theharvester, use_userrecon, use_additional_tools)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(scraper.scrape_sites())

        scraper.display_results()

        save_results = input("Do you want to save the results to a file? (y/n): ")
        if save_results.lower() == 'y':
            filename = input("Enter the filename to save the results (default: search_results.txt): ")
            scraper.save_results_to_file(filename if filename else 'search_results.txt')

    except KeyboardInterrupt:
        print("Cancelled by user.")
        scraper.save_results_to_file(filename if filename else 'search_results.txt')
