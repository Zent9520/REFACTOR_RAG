# app/services/meeting/meeting_analysis_service.py

import json
import re
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings

from app.enums.prompt_code import PromptCode

from backend.app.models.meetings.meeting_analysis import (
    MeetingAnalysis,
)

from backend.app.models.meetings.meeting_transcript import (
    MeetingTranscript,
)

from backend.app.repositories.meetings.meeting_analysis_repository import (
    MeetingAnalysisRepository,
)

from backend.app.repositories.meetings.meeting_transcript_repository import (
    MeetingTranscriptRepository,
)

from backend.app.repositories.ai.ai_prompt_repository import (
    AIPromptRepository,
)

from backend.app.repositories.ai.ai_model_repository import (
    AIModelRepository,
)

from app.services.llm.azure_openai_service import (
    AzureOpenAIService,
)

from app.services.azure.microsoft_meeting_service import (
    MicrosoftMeetingService,
)


class MeetingAnalysisService:

    _GRAPH_DATETIME_FRACTION_RE = re.compile(
        r"(\.\d{6})\d+"
    )

    @staticmethod
    def _parse_graph_datetime(
        value: str | None,
    ) -> datetime | None:

        if not value:
            return None

        normalized_value = value.strip()

        if normalized_value.endswith(
            "Z"
        ):
            normalized_value = (
                normalized_value[:-1]
                + "+00:00"
            )

        normalized_value = (
            MeetingAnalysisService
            ._GRAPH_DATETIME_FRACTION_RE
            .sub(
                r"\1",
                normalized_value,
            )
        )

        parsed = datetime.fromisoformat(
            normalized_value
        )

        if parsed.tzinfo is None:
            return parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed.astimezone(
            timezone.utc
        )

    @staticmethod
    async def sync(
        db: AsyncSession,
    ):

        start_time, now = (
            MicrosoftMeetingService
            .get_sync_range()
        )

        print(
            "Meeting sync:",
            start_time,
            "->",
            now,
        )

        access_token = await (
            MicrosoftMeetingService
            .get_access_token()
        )

        #
        # 1. Calendar
        #

        events = await (
            MicrosoftMeetingService
            .get_calendar_events(
                access_token=access_token,
                start_time=start_time,
                end_time=now,
            )
        )

        print(
            "Calendar events:",
            len(events),
        )

        #
        # 2. Chỉ lấy Teams meeting đã kết thúc
        #

        completed_events = []

        for event in events:

            if not event.get(
                "isOnlineMeeting",
                False,
            ):
                continue

            provider = event.get(
                "onlineMeetingProvider"
            )

            if provider != "teamsForBusiness":
                continue

            end_data = event.get(
                "end",
                {},
            )

            end_value = end_data.get(
                "dateTime"
            )

            if not end_value:
                continue

            end_time = (
                MeetingAnalysisService
                ._parse_graph_datetime(
                    end_value
                )
            )

            if (
                end_time is not None
                and end_time <= now
            ):
                completed_events.append(
                    event
                )

        print(
            "Completed Teams meetings:",
            len(completed_events),
        )

        #
        # 3. Lấy transcript trong cùng window
        #

        transcripts = await (
            MicrosoftMeetingService
            .get_transcripts(
                access_token=access_token,
                start_time=start_time,
                end_time=now,
            )
        )

        print(
            "Transcripts:",
            len(transcripts),
        )

        #
        # 4. Lưu Calendar metadata trước
        #

        for event in completed_events:

            await (
                MeetingAnalysisService
                ._save_event(
                    db=db,
                    event=event,
                )
            )

        await db.flush()

        #
        # 5. Xử lý từng transcript
        #

        for transcript in transcripts:

            try:

                await (
                    MeetingAnalysisService
                    ._process_transcript(
                        db=db,
                        access_token=access_token,
                        transcript=transcript,
                        completed_events=completed_events,
                    )
                )

            except Exception as e:

                print(
                    "PROCESS TRANSCRIPT ERROR:",
                    transcript.get("id"),
                )

                print(e)

        await db.commit()

    @staticmethod
    async def _save_event(
        db: AsyncSession,
        event: dict,
    ):

        event_id = event.get(
            "id"
        )

        if not event_id:
            return

        existing = await (
            MeetingAnalysisRepository
            .get_by_event_id(
                db=db,
                event_id=event_id,
            )
        )

        if existing is not None:
            return existing

        organizer = (
            event
            .get(
                "organizer",
                {},
            )
            .get(
                "emailAddress",
                {},
            )
        )

        attendees = []

        for attendee in event.get(
            "attendees",
            [],
        ):

            email_address = attendee.get(
                "emailAddress",
                {},
            )

            status = attendee.get(
                "status",
                {},
            )

            attendees.append({
                "name": email_address.get(
                    "name"
                ),
                "email": email_address.get(
                    "address"
                ),
                "type": attendee.get(
                    "type"
                ),
                "response": status.get(
                    "response"
                ),
            })

        location = (
            event
            .get(
                "location",
                {},
            )
            .get(
                "displayName"
            )
        )

        start_value = (
            event
            .get(
                "start",
                {},
            )
            .get(
                "dateTime"
            )
        )

        end_value = (
            event
            .get(
                "end",
                {},
            )
            .get(
                "dateTime"
            )
        )

        online_meeting = event.get(
            "onlineMeeting"
        ) or {}

        body = event.get(
            "body"
        ) or {}

        model = MeetingAnalysis(
            event_id=event_id,

            subject=event.get(
                "subject"
            ),

            body_preview=event.get(
                "bodyPreview"
            ),

            description=body.get(
                "content"
            ),

            organizer_name=organizer.get(
                "name"
            ),

            organizer_email=organizer.get(
                "address"
            ),

            start_time=(
                MeetingAnalysisService
                ._parse_graph_datetime(
                    start_value
                )
            ),

            end_time=(
                MeetingAnalysisService
                ._parse_graph_datetime(
                    end_value
                )
            ),

            location=location,

            web_link=event.get(
                "webLink"
            ),

            join_url=online_meeting.get(
                "joinUrl"
            ),

            online_meeting_provider=(
                event.get(
                    "onlineMeetingProvider"
                )
            ),

            attendees=attendees,

            raw_data=event,

            has_transcript=False,

            analysis_status="pending",
        )

        await (
            MeetingAnalysisRepository
            .create(
                db=db,
                model=model,
            )
        )

        return model

    @staticmethod
    async def _process_transcript(
        db: AsyncSession,
        access_token: str,
        transcript: dict,
        completed_events: list[dict],
    ):

        transcript_id = transcript.get(
            "id"
        )

        meeting_id = transcript.get(
            "meetingId"
        )

        if (
            not transcript_id
            or not meeting_id
        ):
            return

        #
        # Đã xử lý rồi => bỏ qua
        #

        existing_transcript = await (
            MeetingTranscriptRepository
            .get_by_transcript_id(
                db=db,
                transcript_id=transcript_id,
            )
        )

        if existing_transcript is not None:

            print(
                "Transcript already processed:",
                transcript_id,
            )

            return

        #
        # Tìm calendar event tương ứng.
        #
        # Hiện tại ưu tiên joinUrl / metadata.
        # Nếu chưa match được thì không tạo analysis sai meeting.
        #

        meeting = await (
            MeetingAnalysisService
            ._find_meeting_for_transcript(
                db=db,
                transcript=transcript,
                completed_events=completed_events,
            )
        )

        if meeting is None:

            print(
                "Cannot match transcript to calendar event:",
                transcript_id,
                meeting_id,
            )

            return

        #
        # Gắn Teams meeting ID
        #

        meeting.online_meeting_id = (
            meeting_id
        )

        #
        # Download raw VTT
        #

        content = await (
            MicrosoftMeetingService
            .get_transcript_content(
                access_token=access_token,
                meeting_id=meeting_id,
                transcript_id=transcript_id,
            )
        )

        transcript_model = (
            MeetingTranscript(
                meeting_id=meeting.id,

                transcript_id=transcript_id,

                content=content,

                content_type="text/vtt",

                created_at_graph=(
                    MeetingAnalysisService
                    ._parse_graph_datetime(
                        transcript.get(
                            "createdDateTime"
                        )
                    )
                ),

                fetched_at=datetime.now(
                    timezone.utc
                ),
            )
        )

        await (
            MeetingTranscriptRepository
            .create(
                db=db,
                model=transcript_model,
            )
        )

        meeting.has_transcript = True

        meeting.analysis_status = (
            "processing"
        )

        await db.flush()

        #
        # AI analyze
        #

        result = await (
            MeetingAnalysisService
            .analyze(
                db=db,
                transcript=content,
            )
        )

        meeting.summary = result.get(
            "summary"
        )

        meeting.key_points = result.get(
            "key_points",
            [],
        )

        meeting.decisions = result.get(
            "decisions",
            [],
        )

        meeting.action_items = result.get(
            "action_items",
            [],
        )

        meeting.risks = result.get(
            "risks",
            [],
        )

        meeting.unresolved_issues = (
            result.get(
                "unresolved_issues",
                [],
            )
        )

        meeting.model_id = (
            settings.EXECUTIVE_DATA_MODEL_ID
        )

        meeting.analysis_status = (
            "completed"
        )

        meeting.analyzed_at = (
            datetime.now(
                timezone.utc
            )
        )

        await (
            MeetingAnalysisRepository
            .update(
                db=db,
                model=meeting,
            )
        )

    @staticmethod
    async def _find_meeting_for_transcript(
        db: AsyncSession,
        transcript: dict,
        completed_events: list[dict],
    ):

        meeting_id = transcript.get(
            "meetingId"
        )

        #
        # Nếu lần sync trước đã resolve meetingId
        #

        if meeting_id:

            result = await (
                MeetingAnalysisRepository
                .get_by_online_meeting_id(
                    db=db,
                    online_meeting_id=meeting_id,
                )
            )

            if result is not None:
                return result

        #
        # Transcript có endDateTime.
        # Match với calendar event gần thời điểm kết thúc nhất.
        #
        # Chỉ dùng khi chưa resolve được meetingId.
        #

        transcript_end = (
            MeetingAnalysisService
            ._parse_graph_datetime(
                transcript.get(
                    "endDateTime"
                )
            )
        )

        if transcript_end is None:
            return None

        best_event = None
        best_difference = None

        for event in completed_events:

            event_end = (
                MeetingAnalysisService
                ._parse_graph_datetime(
                    event
                    .get(
                        "end",
                        {},
                    )
                    .get(
                        "dateTime"
                    )
                )
            )

            if event_end is None:
                continue

            difference = abs(
                (
                    event_end
                    - transcript_end
                )
                .total_seconds()
            )

            if (
                best_difference is None
                or difference < best_difference
            ):

                best_difference = difference
                best_event = event

        #
        # Không match nếu lệch quá 30 phút.
        #

        if (
            best_event is None
            or best_difference is None
            or best_difference > 1800
        ):
            return None

        return await (
            MeetingAnalysisRepository
            .get_by_event_id(
                db=db,
                event_id=best_event["id"],
            )
        )


#Phân tích transcript đã có trên FE

    @staticmethod
    async def analyze(
        db: AsyncSession,
        transcript: str,
        model_id: UUID | None = None,
    ) -> dict:

        prompt = await (
            AIPromptRepository
            .get_by_code(
                db=db,
                code=PromptCode.MEETING_SUMMARY,
            )
        )

        if prompt is None:

            raise Exception(
                "Prompt MEETING_SUMMARY not found."
            )

        model = await (
            AIModelRepository
            .get_by_id(
                db=db,
                id=model_id or settings.EXECUTIVE_DATA_MODEL_ID,
            )
        )

        if model is None:

            raise LookupError(
                "AI model not found."
            )

        user_prompt_template = (
            prompt.user_prompt
            or "{transcript}"
        )

        if "{transcript}" in user_prompt_template:
            user_prompt = user_prompt_template.replace(
                "{transcript}",
                transcript,
            )
        else:
            user_prompt = (
                f"{user_prompt_template}\n\n"
                f"{transcript}"
            )

        analysis_prompt = (
            f"{prompt.system_prompt}\n\n"
            f"Transcript:\n"
            f"{user_prompt}"
        )

        #
        # CHỖ NÀY gọi đúng method hiện tại
        # của AzureOpenAIService trong project.
        #

        response = await (
            AzureOpenAIService()
            .generate(
                model=model.model_name,
                prompt=analysis_prompt,
                temperature=0.0,
            )
        )

        if isinstance(
            response,
            dict,
        ):
            return response

        content = response.strip()

        if content.startswith(
            "```json"
        ):
            content = content[7:]

        if content.startswith(
            "```"
        ):
            content = content[3:]

        if content.endswith(
            "```"
        ):
            content = content[:-3]

        return json.loads(
            content.strip()
        )
