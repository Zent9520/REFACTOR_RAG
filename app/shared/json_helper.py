import json
import re


class JsonHelper:

    @staticmethod
    def parse_llm_json(
        response: str
    ) -> dict:

        if not response:
            return {}

        response = response.strip()

        #
        # remove ```json
        #
        response = re.sub(
            r"^```json",
            "",
            response,
            flags=re.IGNORECASE
        )

        #
        # remove ```
        #
        response = re.sub(
            r"```$",
            "",
            response
        )

        response = response.strip()

        #
        # find first {
        #
        start = response.find("{")

        #
        # find last }
        #
        end = response.rfind("}")

        if start == -1 or end == -1:

            raise ValueError(
                "No JSON object found"
            )

        response = response[
            start:end + 1
        ]

        return json.loads(
            response
        )