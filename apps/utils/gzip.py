import gzip
import io
import json
import logging

from requests import Response

_logger = logging.getLogger(__name__)


class GzipExtracter:
    def __init__(self, response: Response):
        self.response = response

    def extract(self):
        with io.BytesIO() as buf:
            buf.write(self.response.content)
            buf.seek(0)
            with gzip.open(buf, "rt") as compressed_report:
                report_content = compressed_report.read()
                report_content_array = json.loads(report_content)
        return report_content_array
