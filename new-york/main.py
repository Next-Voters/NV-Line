import time 
import asyncio

from .helper.newyorkScraper import scrapeCouncilMeetings, scrapeMeetingDetails, scrapeLegislationDetail
from .helper.senderServices.emailService import sendEmails
from .helper.senderServices.htmlReportPackage import buildHTMLReport
from .helper.webRequester import fetchCouncilMeetings, fetchMeetingDetails, fetchLegislationDetails
from .helper.ai.aiProcessor import processBillsWithAI

async def cli():
    start_time = time.time()
    
    print("Fetching meetings...")
    meetingHTML = await fetchCouncilMeetings()
    
    print("Scraping meetings...")
    scrapeCouncilMeetings(meetingHTML)
    
    print("Fetching meeting details (legislation list)...")
    await fetchMeetingDetails()
    
    print("Scraping meeting details (legislation list)...")
    scrapeMeetingDetails()

    print("Fetching legislation details...")
    await fetchLegislationDetails()

    print("Scraping legislation details...")
    scrapeLegislationDetail()
    
    print("Processing bills with AI...")
    await processBillsWithAI() 

    print("Compile HTML report...")
    buildHTMLReport()
    
    print("Sending emails...")
    sendEmails()
    
    elapsed_time = time.time() - start_time
    print(f"Total time: {elapsed_time:.2f} seconds")

def main():
    asyncio.run(cli())

if __name__ == "__main__":
    main()