# from array import array
# from datetime import datetime, timedelta

# import pyexcel
# from django.db.models import Q

# from apps.ads_api.constants import SpReportType
# from apps.ads_api.models import Campaign, Profile, ReportData

# a_list_of_dictionaries = [
#     {"Name": "Adam", "Age": 28},
#     {"Name": "Beatrice", "Age": 29},
#     {"Name": "Ceri", "Age": 30},
#     {"Name": "Dean", "Age": 26},
#     {"Name": "Dean", "Age": 26},
#     {"Name": "Dean", "Age": 26},
#     {"Name": "Dean", "Age": 26},
# ]


# def get_query_data():
#     today = datetime.today()
#     date_from = today - timedelta(days=30)
#     date_to = today - timedelta(days=2)

#     profile = Profile.objects.get(nickname="MeganFerry", country_code="US")

#     query_data = ReportData.objects.filter(
#         Q(report_type=SpReportType.KEYWORD_QUERY) | Q(report_type=SpReportType.TARGET_QUERY),
#         campaign__profile=profile,
#         date__gte=date_from,
#         date__lte=date_to,
#         clicks__gt=0,
#     )

#     data_list = []
#     data_headers = [
#         "ASIN",
#         "Target",
#         "Query",
#         "Impressions",
#         "Clicks",
#         "Orders",
#         "Spend",
#         "Sales",
#         "Kenp Royalties",
#     ]
#     data_list.append(data_headers)

#     profile_campaigns = Campaign.objects.filter(profile=profile, managed=True)
#     asins_per_compaign = {}
#     for campaign in profile_campaigns:
#         if campaign.id not in asins_per_compaign:
#             asins_per_compaign[campaign.id] = campaign.asins[0]

#     for query in query_data:
#         data_row = [
#             asins_per_compaign[query.campaign_id],
#             query.keyword_text if len(query.keyword_text) > 0 else query.target_text,
#             query.query,
#             query.impressions,
#             query.clicks,
#             query.orders,
#             query.spend,
#             query.sales,
#             query.kenp_royalties,
#         ]

#         data_list.append(data_row)

#     return data_list


# # pyexcel.save_as(array=get_query_data(), dest_file_name="your_file.xlsx")

# # get_query_data()
