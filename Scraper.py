from apify_client import ApifyClient
import time
import json
import gradio as gr
import os
from datetime import datetime
from threading import Thread
from dotenv import load_dotenv


load_dotenv('.env')
apify_api_key = os.environ.get("Apify_Token")


def scrape(progress=gr.Progress()):

    # Create 'historicals' directory if it doesn't exist
    if not os.path.exists("historicals"):
        os.makedirs("historicals")

    # Start the scraping process and simulate periodic progress updates
    progress(0, desc="Initiating the scraping process - this may take a few minutes...")

    # Initialize the ApifyClient with your API token
    client = ApifyClient(apify_api_key)

    # Prepare the Actor input
    run_input = {
        "startUrls": [{ "url": "https://eyewire.news/search?q=iol"}, 
                      {"url": "https://glance.eyesoneyecare.com/stories/?q=iol"},
                      {"url": "https://investors.rxsight.com/news-events/news-releases?page=0"},
                      {"url":"https://www.jjvision.com/news-media-center"}],
        "useSitemaps": True,
        "crawlerType": "playwright:adaptive",
        "includeUrlGlobs": ["https://eyewire.news/news/**iol**", 
                            "https://glance.eyesoneyecare.com/stories/2024**/**iol**"],
        "excludeUrlGlobs": [],
        "keepUrlFragments": False,
        "ignoreCanonicalUrl": False,
        "maxCrawlDepth": 20,
        "maxCrawlPages": 30,
        "initialConcurrency": 0,
        "maxConcurrency": 200,
        "initialCookies": [],
        "proxyConfiguration": { "useApifyProxy": True },
        "maxSessionRotations": 10,
        "maxRequestRetries": 5,
        "requestTimeoutSecs": 60,
        "minFileDownloadSpeedKBps": 128,
        "dynamicContentWaitSecs": 10,
        "waitForSelector": "",
        "maxScrollHeightPixels": 5000,
        "keepElementsCssSelector": "",
        "removeElementsCssSelector": "",
        "removeCookieWarnings": True,
        "expandIframes": True,
        "clickElementsCssSelector": "[aria-expanded=\"false\"]",
        "htmlTransformer": "readableText",
        "readableTextCharThreshold": 100,
        "aggressivePrune": False,
        "debugMode": False,
        "debugLog": False,
        "saveHtml": False,
        "saveHtmlAsFile": False,
        "saveMarkdown": True,
        "saveFiles": False,
        "saveScreenshots": False,
        "maxResults": 9999999,
        "clientSideMinChangePercentage": 15,
        "renderingTypeDetectionPercentage": 10,
    }

    # Prepare the Actor input
    run_input2 = {
        "startUrls": [{ "url": "https://www.healio.com/search#q=iol&sort=%40posteddate%20descending"}],
        "useSitemaps": True,
        "crawlerType": "playwright:adaptive",
        "includeUrlGlobs": ["https://www.healio.com/news/ophthalmology/2024**/**"],
        "excludeUrlGlobs": [],
        "keepUrlFragments": False,
        "ignoreCanonicalUrl": False,
        "maxCrawlDepth": 20,
        "maxCrawlPages": 10,
        "initialConcurrency": 0,
        "maxConcurrency": 200,
        "initialCookies": [],
        "proxyConfiguration": { "useApifyProxy": True },
        "maxSessionRotations": 10,
        "maxRequestRetries": 2,
        "requestTimeoutSecs": 20,
        "minFileDownloadSpeedKBps": 128,
        "dynamicContentWaitSecs": 10,
        "waitForSelector": "",
        "maxScrollHeightPixels": 5000,
        "keepElementsCssSelector": "",
        "removeElementsCssSelector": "",
        "removeCookieWarnings": True,
        "expandIframes": True,
        "clickElementsCssSelector": "[aria-expanded=\"false\"]",
        "htmlTransformer": "readableText",
        "readableTextCharThreshold": 100,
        "aggressivePrune": False,
        "debugMode": False,
        "debugLog": False,
        "saveHtml": False,
        "saveHtmlAsFile": False,
        "saveMarkdown": True,
        "saveFiles": False,
        "saveScreenshots": False,
        "maxResults": 9999999,
        "clientSideMinChangePercentage": 15,
        "renderingTypeDetectionPercentage": 10,
    }

        # Define a function to handle the scraping process
    def run_scraping(results_list):
        # Run the Actor and fetch results for the first input
        run1 = client.actor("aYG0l9s7dbB7j3gbS").call(run_input=run_input)
        for item in client.dataset(run1["defaultDatasetId"]).iterate_items():
            result = {
                'url': item.get('url'),
                'title': item.get('metadata', {}).get('title'),
                'text': item.get('text')
            }
            results_list.append(result)

        # Run the Actor and fetch results for the second input
        run2 = client.actor("aYG0l9s7dbB7j3gbS").call(run_input=run_input2)
        for item in client.dataset(run2["defaultDatasetId"]).iterate_items():
            result = {
                'url': item.get('url'),
                'title': item.get('metadata', {}).get('title'),
                'text': item.get('text')
            }
            results_list.append(result)

    # List to store the results
    results_list = []

    # Start the scraping in a separate thread
    scraping_thread = Thread(target=run_scraping, args=(results_list,))
    scraping_thread.start()

    # Progress update loop while the scraping thread is running
    total_time = 600  # Total time in seconds (10 minutes)
    update_interval = 2  # Update every 5 seconds
    num_updates = total_time // update_interval

    for i in range(num_updates):
        if not scraping_thread.is_alive():
            break  # Exit if the thread completes
        # Update the progress bar
        if (((i + 1) / num_updates) < 1):
            progress((i + 1) / num_updates, desc=f"Scraping in progress - this may take a few minutes...")
            time.sleep(update_interval)

    # Ensure the scraping thread completes
    scraping_thread.join()

    # Generate a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Save the results to a timestamped JSON file in 'historicals' folder
    file_path = f"historicals/scraped_results_{timestamp}.json"
    with open(file_path, "w") as file:
        json.dump(results_list, file, indent=4)

    # Also save the latest results to a general scraped_results.json file
    with open("scraped_results.json", "w") as file:
        json.dump(results_list, file, indent=4)

    # Final progress update to indicate completion
    progress(1, desc="Scraping complete.")
    return results_list