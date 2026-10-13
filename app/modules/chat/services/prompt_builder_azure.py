from typing import Any

import re


class PromptBuilderAzure:

    @staticmethod
    def build(
        prompt: str,
        cv_text: str,
        job_description: str | None = None,
    ) -> str:

        sections: list[str] = [
            prompt.strip(),
        ]

        if job_description and job_description.strip():

            sections.extend(
                [
                    "",
                    "=" * 80,
                    "JOB DESCRIPTION",
                    "=" * 80,
                    job_description.strip(),
                ],
            )

        if cv_text and cv_text.strip():

            sections.extend(
                [
                    "",
                    "=" * 80,
                    "CANDIDATE CV",
                    "=" * 80,
                    cv_text.strip(),
                ],
            )

        return "\n".join(
            sections,
        )