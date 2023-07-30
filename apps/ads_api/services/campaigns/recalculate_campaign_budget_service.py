import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Sum

from apps.ads_api.constants import SpReportType
from apps.ads_api.models import Campaign, RecentReportData

_logger = logging.getLogger(__name__)


class RecalculateCampaignBudgetService:
    def __init__(self, campaign: Campaign):
        self.campaign = campaign

    def recalculate_budget(self) -> float:
        new_budget = self.campaign.daily_budget
        campaign_data = RecentReportData.objects.filter(
            report_type=SpReportType.CAMPAIGN,
            campaign=self.campaign,
            date__gte=datetime.today() - timedelta(days=30),
        ).aggregate(
            sales_sum=Sum("sales"),
            spend_sum=Sum("spend"),
        )

        sales = campaign_data.get("sales_sum", 0)
        spend = campaign_data.get("spend_sum", 0)

        if sales is None or spend is None:
            _logger.info(
                f"Campaign: {self.campaign} on profile {self.campaign.profile} has spend: {spend} and sales {sales}. RecalculateCampaignBudgetService skipped."
            )
            return new_budget

        acos = spend / sales if sales > 0 else 0.0
        if 0.5 > acos > 0.0:
            new_budget = float(self.campaign.daily_budget * Decimal("1.2"))
            new_budget_str = str(new_budget)
            if len(new_budget_str[new_budget_str.index(".") + 1 :]) == 1:
                new_budget += 0.01

        return new_budget
