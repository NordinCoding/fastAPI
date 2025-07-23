def bol_scraper(URL):
    print(f"SCRAPING: {URL}")


def coolblue_scraper(URL):
    print(f"SCRAPING: {URL}")


def main():
    url = "https://www.bol.com/nl/nl/p/rogelli-core-fietsshirt-korte-mouwen-heren-zwart-fluor-maat-2xl/9200000106120768"



    supported_sites = {"www.bol.com/": bol_scraper,
                        "www.coolblue.nl/": coolblue_scraper,
                        "www.coolblue.be/": coolblue_scraper
                        }
    
    for url_check in supported_sites:
        if url_check in url:
            supported_sites[url_check](url)

main()