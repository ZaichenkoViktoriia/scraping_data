from playwright.sync_api import sync_playwright
import pandas as pd
import matplotlib.pyplot as plt


def scrape_hotels(page):
    hotels = page.locator('//div[@data-testid="property-card"]').all()
    print(f'There are: {len(hotels)} hotels.')

    hotels_list = []
    for hotel in hotels:
        hotel_dict = {}
        hotel_dict['hotel'] = hotel.locator('//div[@data-testid="title"]').inner_text()
        price_info = hotel.locator('//span[@data-testid="price-and-discounted-price"]').inner_text()
        price_values = price_info.replace('zł', '').split()
        hotel_dict['price'] = float(price_values[-1]) if price_values else None
        hotel_dict['score'] = hotel.locator('//div[@data-testid="review-score"]/div[1]').inner_text()
        hotel_dict['avg review'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[1]').inner_text()
        hotel_dict['reviews count'] = hotel.locator('//div[@data-testid="review-score"]/div[2]/div[2]').inner_text().split()[0]

        hotels_list.append(hotel_dict)

    return hotels_list


def main():
    with sync_playwright() as p:
        checkin_date = "2024-01-17"
        checkout_date = "2024-01-18"

        all_hotels_list = []
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for page_number in range(1, 6):
            page_url = f'https://www.booking.com/searchresults.html?page={page_number}&ss=Luxembourg&ssne=Luxembourg&ssne_untouched=Luxembourg&label=gen173nr-1FCAQoggI46wdIMVgEaLYBiAEBmAExuAEHyAEM2AEB6AEB-AEDiAIBqAIDuALJxrKrBsACAdICJGQ5N2FhY2EzLTUyMzMtNDk3Zi04NGVjLWY3ZDg3YzhlYWQwOdgCBeACAQ&aid=304142&lang=en-us&sb=1&src_elem=sb&src=searchresults&dest_id=-1736191&dest_type=city&checkin={checkin_date}&checkout={checkout_date}&group_adults=1&no_rooms=1&group_children=0'
            page.goto(page_url, timeout=60000)

            hotels_list = scrape_hotels(page)
            all_hotels_list.extend(hotels_list)

            next_button = page.locator('//li[@data-id="pagination-next"]')
            if next_button.is_visible():
                next_button.click()
                page.wait_for_timeout(2000)  # Wait for some time to let the next page load

        df = pd.DataFrame(all_hotels_list)
        df.to_excel("hotels_list.xlsx", index=False)
        df.to_csv("hotels_list.csv", index=False)

        df["price"] = df["price"].replace("[^\d.]", "", regex=True).astype(float)
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

        top_10_scores = df.nlargest(10, 'score')
        top_10_prices = df.nlargest(10, 'price')

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        top_10_prices.sort_values("price").plot(kind="bar", x="hotel", y="price", color="blue", legend=False)
        plt.title("Top 10 Hotel Prices")
        plt.xlabel("Hotel")
        plt.ylabel("Price (zł)")

        plt.subplot(1, 2, 2)
        top_10_scores.sort_values("score").plot(kind="bar", x="hotel", y="score", color="green", legend=False)
        plt.title("Top 10 Hotel Scores")
        plt.xlabel("Hotel")
        plt.ylabel("Score")

        plt.tight_layout()
        plt.show()

        browser.close()


if __name__ == '__main__':
    main()
