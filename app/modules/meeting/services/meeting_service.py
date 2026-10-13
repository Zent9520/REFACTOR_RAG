from uuid import UUID

from backend.app.modules.meeting.repositories.meeting_analysis_repository import (
    MeetingAnalysisRepository,
)

from backend.app.modules.meeting.repositories.meeting_transcript_repository import (
    MeetingTranscriptRepository,
)


class MeetingService:

    @staticmethod
    async def get_all(
        db,
    ):

        meetings = await (
            MeetingAnalysisRepository
            .get_list(
                db=db,
            )
        )

        return [
            {
                "id": meeting["id"],
                "title": meeting["subject"],
                "start_time": meeting["start_time"],
                "end_time": meeting["end_time"],
            }
            for meeting in meetings
        ]

    @staticmethod
    async def get_by_id(
        db,
        id: UUID,
    ):

        meeting = await (
            MeetingAnalysisRepository
            .get_by_id(
                db=db,
                id=id,
            )
        )

        if meeting is None:
            return None

        transcripts = await (
            MeetingTranscriptRepository
            .get_by_meeting_id(
                db=db,
                meeting_id=meeting.id,
            )
        )

        return {
            #
            # Meeting identity
            #
            "id": meeting.id,
            "event_id": meeting.event_id,
            "online_meeting_id": (
                meeting.online_meeting_id
            ),

            #
            # Meeting metadata
            #
            "subject": meeting.subject,
            "body_preview": meeting.body_preview,
            "description": meeting.description,

            "organizer_name": (
                meeting.organizer_name
            ),

            "organizer_email": (
                meeting.organizer_email
            ),

            "start_time": meeting.start_time,
            "end_time": meeting.end_time,

            "location": meeting.location,

            "web_link": meeting.web_link,
            "join_url": meeting.join_url,

            "online_meeting_provider": (
                meeting.online_meeting_provider
            ),

            "attendees": meeting.attendees,

            #
            # Transcript state
            #
            "has_transcript": (
                meeting.has_transcript
            ),

            #
            # AI analysis
            #
            "analysis_status": (
                meeting.analysis_status
            ),

            "summary": meeting.summary,

            "key_points": (
                meeting.key_points
            ),

            "decisions": (
                meeting.decisions
            ),

            "action_items": (
                meeting.action_items
            ),

            "risks": meeting.risks,

            "unresolved_issues": (
                meeting.unresolved_issues
            ),

            "model_id": meeting.model_id,
            "analyzed_at": meeting.analyzed_at,

            #
            # Raw Graph
            #
            "raw_data": meeting.raw_data,

            #
            # Transcript
            #
            "transcripts": [
                {
                    "id": transcript.id,

                    "transcript_id": (
                        transcript.transcript_id
                    ),

                    "content": (
                        transcript.content
                    ),

                    "content_type": (
                        transcript.content_type
                    ),

                    "created_at_graph": (
                        transcript.created_at_graph
                    ),

                    "fetched_at": (
                        transcript.fetched_at
                    ),
                }
                for transcript in transcripts
            ],

            #
            # System
            #
            "created_at": meeting.created_at,
            "updated_at": meeting.updated_at,
        }