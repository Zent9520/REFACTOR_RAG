import json


class ResponseParser:

    @staticmethod
    def parse_json_array(
        raw_response: str
    ) -> list[str]:

        try:

            data = json.loads(raw_response)

            if isinstance(data, list):
                return data

        except Exception:
            pass

        return []