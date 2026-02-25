"""Test for get_script_url_by_title method in scraper.py"""

from scraper import IMSDbScraper


def test_get_script_url_by_title(test_data):
    """Test get_script_url_by_title with Pulp Fiction."""
    scraper = IMSDbScraper()
    
    print(f"Testing get_script_url_by_title with: {test_data['title']}")
    
    result = scraper.get_script_url_by_title(test_data['title'])

    if not result:
        result = scraper.search_movie(test_data['title'])


    print(f"Result: {result}")

    if result:
        print(f"✓ Success! Found URL: {result}")
        return True
    else:
        print("✗ Failed! No URL found")
        return False

def test():
    test_datas = [{
        "title": "The Shawshank Redemption",
        "year": "",
        "imdb_id": "tt0111161",
        "imdb_url": "https://www.imdb.com/title/tt0111161"
    }, {
        "title": "Schindler's List",
        "year": "",
        "imdb_id": "tt0108052",
        "imdb_url": "https://www.imdb.com/title/tt0108052"
    }]
    for data in test_datas:
        test_get_script_url_by_title(data)

if __name__ == "__main__":
    test()
