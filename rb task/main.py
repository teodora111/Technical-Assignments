import urllib

import requests
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import csv
import re

user_agent_index = -1
user_agents_list = []
cookie = ''


def print_html(url):
    hdr = {
        'User-Agent': 'Mozilla/5.0 (en-us) AppleWebKit/534.14 (KHTML, like Gecko; Google Wireless Transcoder) '
                      'Chrome/9.0.597 '
                      'Safari/534.14 ',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'cookie': cookie
    }
    request_site = Request(url, headers=hdr)
    page = urlopen(request_site, timeout=10)
    html_bytes = page.read()
    print(html_bytes.decode("utf-8"))


def url_to_html(url):
    global user_agent_index
    global user_agents_list
    global cookie

    num_of_tries = 0
    found = False
    while not found:

        hdr = {
            'User-Agent': user_agents_list[user_agent_index],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive',
            'cookie': cookie
        }

        user_agent_index = (user_agent_index + 1) % len(user_agents_list)

        # request_site = Request(url, headers={'User-Agent': user_agents_list[user_agent_index]})
        request_site = Request(url, headers=hdr)

        if num_of_tries > 10:
            return ""
        try:
            page = urlopen(request_site, timeout=10)
            found = True
            print("succ")
        except urllib.error.HTTPError as e:
            print(e.fp.read())
            num_of_tries = num_of_tries + 1

    html_bytes = page.read()
    return html_bytes.decode("utf-8")


def scrape():
    url = "https://www.crunchbase.com/lists/acquisitions-of-the-past-week/f73873b1-093e-40a7-a329-ec4635731873" \
          "/acquisitions "

    html = url_to_html(url)
    if html == "":
        print("Scraper blocked")
        return

    soup = BeautifulSoup(html, "html.parser")

    with open('file.csv', mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(['Transaction Name', 'Acquiree Name', 'Acquirer Name', 'Announced Date', 'Price',
                         'Acquiree Industries', 'Acquiree Headquarters', 'Acquirer Industries',
                         'Acquirer Headquarters', 'Acquiree CB Rank', 'Acquirer CB Rank'])

        arr = ["", "", "", "", "", "", "", "", "", "", ""]

        i = 0

        count = 0
        for x in soup.find_all(["a", "span"], {"class": "component--field-formatter"}):
            # if count == 6:
            #     return

            # Transaction Name arr[0], Acquiree Name arr[1], Acquirer Name arr[2], Announced Date arr[3]
            arr[i] = x["title"]
            try:
                link = "https://www.crunchbase.com/" + x["href"]
            except KeyError as e:
                link = ""

            i = i + 1

            # Transaction details
            if i == 1:
                soup = BeautifulSoup(url_to_html(link), "html.parser")
                if soup == "":
                    print("Scraper blocked")
                    return

                # Price
                price = soup.find("span", {"class": "field-type-money"})
                if price is None:
                    arr[4] = "undisclosed"
                else:
                    arr[4] = price["title"]

            # Acquiree  or Acquirer details
            elif i == 2 or i == 3:
                if i == 2:
                    index_industries = 5
                    index_rank = 9
                else:
                    index_industries = 7
                    index_rank = 10
                soup = BeautifulSoup(url_to_html(link), "html.parser")
                if soup == "":
                    print("Scraper blocked")
                    return

                scrape_task_2(soup)

                # Industries
                industries_arr = []
                industries = soup.find_all("div", {"class": "chip-text"})
                for ind in industries:
                    industries_arr.append(ind.string)
                arr[index_industries] = industries_arr

                # Headquarters
                hr = soup.find('span', string='Headquarters Regions')
                if hr is not None:
                    root = hr.parent.parent.parent
                    arr[index_industries + 1] = root.find('a')['title']
                else:
                    arr[index_industries + 1] = 'undisclosed'

                # CB Rank
                rank = soup.find('a', {
                    'href': re.compile('^/search/organization.companies/field/organizations/rank_org_company.*')})
                if rank is None:
                    arr[index_rank] = 'undisclosed'
                else:
                    arr[index_rank] = rank.string

            # End of row
            elif i == 4:
                writer.writerow(arr)
                count = count + 1
                i = 0

    file.close()


file2_init = False


def scrape_task_2(soup):
    global file2_init
    mode = 'a'
    if not file2_init:
        mode = 'w'

    with open('file2.csv', mode=mode, newline='', encoding='utf-8-sig') as file2:
        writer = csv.writer(file2)
        if not file2_init:
            file2_init = True
            writer.writerow(['Company Name', 'Headquarter Location', 'Employee Count Range', 'Founding Type',
                             'Type of a Company', 'Company Rank', 'Total Funding Amount', 'Number of Contacts',
                             'Number of Employee Profiles', 'List of Employee Profiles', 'Industries', 'Founded Date',
                             'Company Type', 'Contact Email', 'Contact Phone'])

        arr = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]

        # Company Name
        company_name = soup.find(class_="profile-name")
        arr[0] = company_name.string

        # Headquarter Location
        hc_locations = soup.find_all('a', {
            'href': re.compile('^/search/organizations/field/organizations/location_identifiers/.*')})
        if len(hc_locations) == 0:
            arr[1] = "undisclosed"
        else:
            location_arr = []
            for loc in hc_locations:
                if loc.string not in location_arr:
                    location_arr.append(loc.string)
            arr[1] = ", ".join(location_arr)

        # Employee Count Range, added _ because Exel reading it as a date
        emp_num = soup.find('a', {
            'href': re.compile('^/search/people/field/organizations/num_employees_enum/.*')})
        if emp_num is None:
            arr[2] = 'undisclosed'
        else:
            arr[2] = '_' + emp_num.string

        # Founding Type
        ft = soup.find('a', {
            'href': re.compile('^/search/funding_rounds/field/organizations/last_funding_type/.*')})
        if ft is None:
            arr[3] = 'undisclosed'
        else:
            arr[3] = ft.string

        # Type of a Company
        ct = soup.find('span', string='Company Type')
        if ct is not None:
            root = ct.parent.parent.parent
            arr[4] = root.find(class_='component--field-formatter')['title']
        else:
            arr[4] = 'undisclosed'

        # Company Rank
        rank = soup.find('a', {
            'href': re.compile('^/search/organization.companies/field/organizations/rank_org_company.*')})
        if rank is None:
            arr[5] = 'undisclosed'
        else:
            arr[5] = rank.string

        # Total Funding Amount
        financials_link = soup.find('a', {'href': re.compile(r"company_financials$")})
        if financials_link is None:
            arr[6] = 'undisclosed'
        else:
            html = url_to_html("https://www.crunchbase.com" + financials_link['href'])
            if html == "":
                print("Scraper blocked")
                return
            soup_financials = BeautifulSoup(html, "html.parser")
            fa = soup_financials.find('span', string='Total Funding Amount')
            if fa is not None:
                root = fa.parent.parent.parent
                arr[6] = root.find(class_='component--field-formatter').string
            else:
                arr[6] = 'undisclosed'

        # Number of Contacts
        people_link = soup.find('a', {'href': re.compile(r"people$")})
        if people_link is None:
            arr[7] = 'undisclosed'
        else:
            html = url_to_html("https://www.crunchbase.com" + people_link['href'])
            if html == "":
                print("Scraper blocked")
                return
            soup_people = BeautifulSoup(html, "html.parser")

            contacts = soup_people.find('span', string='Contacts')
            if contacts is not None:
                root = contacts.parent.parent.parent
                arr[7] = root.find(class_='component--field-formatter').string
            else:
                # second check if it is not in highlights
                text = soup_people.find(string=re.compile('^Showing 10 of .*'))
                if text is not None:
                    arr[7] = text.string[14:]
                else:
                    arr[7] = 'undisclosed'

        # Number of Employee Profiles
        if people_link is None:
            arr[8] = 'undisclosed'
        else:
            employees = soup_people.find('span', string='Number of Employee Profiles')
            if employees is not None:
                root = employees.parent.parent.parent
                arr[8] = root.find(class_='component--field-formatter').string
            else:
                arr[8] = 'undisclosed'

        # List of Employee Profiles
        if people_link is None:
            arr[9] = 'undisclosed'
        else:
            ilk = soup_people.find('image-list-card')
            if ilk is not None:
                employees_links = ilk.find_all('a', {'href': re.compile('^/person/.*')})
                if employees_links is not None:

                    links_list = []
                    for e in employees_links:
                        links_list.append("https://www.crunchbase.com" + e['href'])
                    arr[9] = links_list
                else:
                    arr[9] = 'undisclosed'
            else:
                arr[9] = 'undisclosed'

        writer.writerow(arr)
    file2.close()


def import_agents():
    global user_agents_list
    with open('agents.txt', 'r') as file:
        for line in file:
            user_agents_list.append(line[:-1])


def import_cookie():
    global cookie
    with open('cookie.txt', 'r') as file:
        cookie = file.read()


if __name__ == '__main__':
    import_agents()
    import_cookie()
    scrape()
    # print(url_to_html('https://www.crunchbase.com/organization/ada-3894/people'))
