import gspread
import logging
import os
from gspread.utils import rowcol_to_a1
from typing import Optional

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

_logger = logging.getLogger(__name__)

SHEETS_API_THROTLING_SEC = 150
THROTTLING_HTTP_CODE = 429

INPUT_SHEET_NAME = "Input"
OUTPUT_SHEET_NAME = "Output"
RETRY_SHEET_NAME = "Retry"


class GoogleSheet:
    def __init__(
        self, credentials_file_path: str = "./google_sheets_credentials.json"
    ) -> None:
        self._credentials_file_path = credentials_file_path
        self.client = self._initialize_client()

    def _initialize_client(self):
        return gspread.service_account(filename=self._credentials_file_path)

    def _get_sheet_object_by_key(self, worksheet_key: str) -> gspread.Spreadsheet:
        """Returns a spredsheet object by using the spreadsheet's key.

        The key is the unique identifier of the spreadsheet,
        and it's located in the URL of the spreadsheet.

        """
        return self.client.open_by_key(worksheet_key)

    def get_new_campaign_info(self, spreadsheet: gspread.Spreadsheet) -> list[str]:
        """Gets new campaign info from google spreadsheet"""
        worksheet = spreadsheet.worksheet(INPUT_SHEET_NAME)
        values_list = worksheet.col_values(2)
        # _logger.info(f"Writing {asin} to the google spreadsheet")
        return values_list

    def _clear_created_campaign_info(self, spreadsheet: gspread.Spreadsheet):
        worksheet = spreadsheet.worksheet(INPUT_SHEET_NAME)
        worksheet.add_cols(1)
        worksheet.delete_columns(start_index=2)

    def move_created_campaign_to_output(
        self,
        campaign_info: list[str],
        spreadsheet: gspread.Spreadsheet,
        write_sheet_name: str = OUTPUT_SHEET_NAME,
    ) -> None:
        self._clear_created_campaign_info(spreadsheet=spreadsheet)
        worksheet = spreadsheet.worksheet(write_sheet_name)
        first_free_col = len(worksheet.row_values(1)) + 1
        write_cell = rowcol_to_a1(1, first_free_col)
        campaign_info_formatted = []
        for value in campaign_info:
            campaign_info_formatted.append([value])
        worksheet.add_cols(1)
        worksheet.update(write_cell, campaign_info_formatted)

    def correct_campaign_purpose(self, spreadsheet: gspread.Spreadsheet):
        """Comment on the first campaign info column about an invalid campaign purpose"""
        worksheet = spreadsheet.worksheet(INPUT_SHEET_NAME)
        worksheet.update("B3", "Invalid. Update please.")

    def get_rank_check_info(self, spreadsheet: gspread.Spreadsheet) -> list[list[str]]:
        """Gets new campaign info from google spreadsheet as a list of lists, each list represents 1 row, without the header row"""
        worksheet = spreadsheet.worksheet(INPUT_SHEET_NAME)
        values = worksheet.get_values()
        values.pop(0)
        return values

    def write_rank_check_info(
        self, spreadsheet: gspread.Spreadsheet, data_to_write: list
    ):
        worksheet = spreadsheet.worksheet(INPUT_SHEET_NAME)
        worksheet.update("A2", data_to_write)


def _process_read_values(values_from_sheet: list[str]) -> dict:
    """Converts the list returned from Google Sheets into a pretty dictionary"""
    pretty_values = {}
    pretty_values["asin"] = str(values_from_sheet[0]).strip().upper()
    pretty_values["country_code"] = values_from_sheet[1]
    pretty_values["type"] = values_from_sheet[2]
    if len(values_from_sheet) > 3:
        pretty_values["bid"] = values_from_sheet[3]
    if len(values_from_sheet) > 5:
        pretty_values["targets"] = values_from_sheet[5:]  # type: ignore
    return pretty_values
