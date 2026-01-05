# app/services/report_service.py
"""
Report Service
- Generates textual region reports using LLM or templating (views.llm_text)
- Aggregates data for all regions and returns report objects
"""

from typing import List, Dict, Any
from app.services import directus_service
from app.views.llm_text import generate_gpt_report  # to be implemented in views
from app.views.graph_builder import generate_graphs  # to be implemented in views
import logging
from collections import defaultdict
from app.constants.regions import GOVERNORATE_FROM_REGION_ID

logger = logging.getLogger("tanmiya.services.report")


async def generate_region_reports() -> List[Dict[str, Any]]:
    """
    Fetch latest leaderboard and predicted data, generate textual reports per region,
    and persist reports to Directus.
    """
    # fetch latest data and predicted data
    latest_data = await directus_service.get_leaderboard_latest()
    predicted_data = await directus_service.get_leaderboard_predictions()

    # print("Fetched latest data: ", latest_data)
    # print("Fetched predicted data: ", predicted_data)

    # Collect region data
    regions_data = defaultdict(list)

    for item in latest_data:
        regions_data[item['Region_id']].append(item['Region'])

    latest_data_list = []
    predicted_data_list = []
    for item in latest_data:
        latest_data_list.append(f"Region: {item['Region']}, Meeting Score: {item['meeting_score'] * 100}, Participants Score: {item['participants_score'] * 100}, Total Topics: {item['total_topics']}, Transferred Topics: {item['transferred_topics']}, Total Score: {item['total_score'] * 100}, Rank: {item['Rank']}")
    for item in predicted_data:
        predicted_data_list.append(f"Region: {item['Region']}, Meeting Score: {item['meeting_score'] * 100}, Participants Score: {item['participants_score'] * 100}, Total Topics: {item['total_topics']}, Transferred Topics: {item['transferred_topics']}, Total Score: {item['total_score'] * 100}, Rank: {item['Rank']}")

    # Generate report
    ar_reports = {}
    en_reports = {}
    for region_id, region_name in regions_data.items():
        # Generate analysis text
        system_prompt = '''You are a knowledgeable assistant tasked with analyzing provided JSON data and generating a detailed report. There are two JSON datasets: one representing actual data of this month and the other containing predictions for the next month. The data includes six primary fields:
                1. participants_score: This field indicates the score based on the number of participants relative to the total participants. Participant score is out of 100.
                2. total_topics: This is the total number of topics scheduled for the discussion in that month.
                3. trasfered_topics: this means the topics which are not discussed and transferred for the next month meetings. So total topics covered is total_topics - transfered_topics. Covering all topics is ideal for achieving higher points.
                3. meeting_score: This score is derived from meeting minutes, evaluating the relevance of the discussed content to the topics. Meeting score is out of 100.
                4. total_score: This is the cumulative score of the three fields mentioned above. Total score is out of 100.
                5. Rank: This rank is determined by comparing the total score across all regions, with higher scores receiving better ranks.'''

        user_prompt_intro = f'''You have provided the scores for all regions for this month here in this prompt.
                Please analyze these given data and provide a detailed introductory report for the {region_name} region by giving a thorough explanation of what occurred in the region in given month.
                by considering participants_score, total_topics and transferred_topics, meeting_score, total_score and Rank.
                Ensure the report is written in natural language without any Markdown-like formatting, focusing on readability and clear comparisons.
                In the report I want:\n\n
                1. Heading: Introduction
                2. Paragraph body under head line: introductory report in min three paragraphs. Use more texts rather than numbers.
                Here is the JSON data:\n\n
                This month data of all regions: {latest_data_list}'''

        user_prompt_analysis = f'''You have provided the scores for all regions for this month here in this prompt.
                Please analyze these given data and provide a detailed performance analysis for the {region_name} region.
                Compare the current month performance with other regions and point out where the region can improve.
                by considering participants_score, total_topics and transferred_topics, meeting_score, total_score and Rank.
                Ensure the report is written in natural language without any Markdown-like formatting, focusing on readability and clear comparisons.
                In the report I want:\n\n
                1. Heading: Performance Analysis
                2. Paragraph body under head line: Compare the current month performance of {region_name} region with all other regions in separate paragraphs and point out where the region can improve. Use more texts rather than numbers.
                Here is the JSON data:\n\n
                This month data of all regions: {latest_data_list}'''

        user_prompt_prediction = f'''You have provided the AI forecasted scores for all regions for next month here in this prompt.
                Please analyze these given data and provide a detailed forecasting report for the {region_name} region using the given AI forecasting data.
                by considering participants_score, total_topics and transferred_topics, meeting_score, total_score and Rank of all regions.
                Ensure the report is written in natural language without any Markdown-like formatting, focusing on readability and clear comparisons.
                In the report I want:\n\n
                1. Heading: AI Predictions for next month
                2. Paragraph body under head line: Compare Predicted data of {region_name} region with all other regions data and recommend steps get into higher ranking in separate paragraphs. Use more texts rather than numbers.
                Here is the JSON data:\n\n
                This month data of all regions: {predicted_data_list}'''

        # Generate reports for each month and append to a list with corresponding region ids
        report_text_1  = await generate_gpt_report(system_prompt, user_prompt_intro)
        report_text_2 = await generate_gpt_report(system_prompt, user_prompt_analysis)
        report_text_3 = await generate_gpt_report(system_prompt, user_prompt_prediction)

        report_text_updated_1 = report_text_1.replace("### ", "").replace("#### ", "").replace("- **", "").replace("**", "").replace("#", "")
        report_text_updated_2 = report_text_2.replace("### ", "").replace("#### ", "").replace("- **", "").replace("**", "").replace("#", "")
        report_text_updated_3 = report_text_3.replace("### ", "").replace("#### ", "").replace("- **", "").replace("**", "").replace("#", "")

        en_reports[region_id] = f"$\t{report_text_updated_1}\n\n$\t{report_text_updated_2}\n\n$\t{report_text_updated_3}"

        # Generate Arabic Report
        system_prompt_for_ar_report = "You are a helpful assistant that translates English text to Arabic. Translate the following text accurately and preserve the original meaning."
        ar_report_text_updated_1 = await generate_gpt_report(system_prompt_for_ar_report, report_text_updated_1)
        ar_report_text_updated_2 = await generate_gpt_report(system_prompt_for_ar_report, report_text_updated_2)
        ar_report_text_updated_3 = await generate_gpt_report(system_prompt_for_ar_report, report_text_updated_3)

        ar_reports[region_id] = f"$\t{ar_report_text_updated_1}\n\n$\t{ar_report_text_updated_2}\n\n$\t{ar_report_text_updated_3}"

    # Generate graphs
    graphs = await generate_graphs(latest_data, predicted_data)

    report_payloads = []
    # Prepare and send the final report
    for region_id, report_text in en_reports.items():

        # Get region name from region_id
        region_name = GOVERNORATE_FROM_REGION_ID.get(region_id)

        # validating before collecting month info from latest_data
        if not latest_data:
            raise ValueError("latest_data is empty")

        month = latest_data[0].get('month')  # Assuming all items are from the same month

        report_payload = {
            "graph": graphs,
            "mail": "",
            "month": month,
            "Region": region_name,
            "Region_id": region_id,
            "report": report_text,
            "report_ar": ar_reports[region_id],
            "report_file": None
        }
        report_payloads.append(report_payload)

        # Post results to leaderboards using directus_service (collection names: Leaderboard_all, Leaderboard)
    try:
        await directus_service.post_reports(report_payloads)      # post calculated scores to leaderbord

    except Exception as e:
        logger.exception("Failed to upsert leaderboard: %s", e)

    return report_payloads
