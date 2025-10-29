"""Unit tests for Racing API tools"""
import pytest
import respx
from httpx import Response

from tab_mcp.server import (
    create_server,
    TabcorpAPIError,
    TAB_BASE_URL
)


@pytest.mark.unit
@pytest.mark.racing
class TestRacingGetAllMeetingDates:
    """Test racing_get_all_meeting_dates tool"""

    def test_get_meeting_dates_success(self, mock_context, respx_mock):
        """Test successful retrieval of meeting dates"""
        # Mock API response
        response_data = {
            "dates": [
                {"date": "2025-10-29", "meetingCount": 15},
                {"date": "2025-10-30", "meetingCount": 12},
                {"date": "2025-10-31", "meetingCount": 18}
            ]
        }
        
        route = respx_mock.get(f"{TAB_BASE_URL}/v1/tab-info-service/racing/dates")
        route.return_value = Response(200, json=response_data)

        server = create_server()
        result = server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
            mock_context,
            access_token="test_token"
        )

        # Verify request
        assert route.called
        request = route.calls[0].request
        assert "Bearer test_token" in request.headers["authorization"]
        assert "jurisdiction" in str(request.url)

        # Verify response
        assert "dates" in result
        assert len(result["dates"]) == 3
        assert result["dates"][0]["date"] == "2025-10-29"

    def test_get_meeting_dates_with_jurisdiction(self, mock_context, respx_mock):
        """Test meeting dates with custom jurisdiction"""
        response_data = {"dates": []}
        route = respx_mock.get(f"{TAB_BASE_URL}/v1/tab-info-service/racing/dates")
        route.return_value = Response(200, json=response_data)

        server = create_server()
        result = server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
            mock_context,
            access_token="test_token",
            jurisdiction="VIC"
        )

        assert route.called
        assert "jurisdiction=VIC" in str(route.calls[0].request.url)

    def test_get_meeting_dates_invalid_jurisdiction(self, mock_context):
        """Test invalid jurisdiction raises error"""
        server = create_server()
        
        with pytest.raises(ValueError, match="Invalid jurisdiction"):
            server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
                mock_context,
                access_token="test_token",
                jurisdiction="INVALID"
            )


@pytest.mark.unit
@pytest.mark.racing
class TestRacingGetMeetings:
    """Test racing_get_meetings tool"""

    def test_get_meetings_success(self, mock_context, respx_mock, sample_race_meeting):
        """Test successful retrieval of meetings for a date"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/dates/2025-10-29/meetings"
        )
        route.return_value = Response(200, json=sample_race_meeting)

        server = create_server()
        result = server.tool_manager.tools["racing_get_meetings"].fn(
            mock_context,
            access_token="test_token",
            meeting_date="2025-10-29"
        )

        assert route.called
        assert "meetings" in result
        assert len(result["meetings"]) > 0
        assert result["meetings"][0]["venueMnemonic"] == "RAN"


@pytest.mark.unit
@pytest.mark.racing
class TestRacingGetRace:
    """Test racing_get_race tool"""

    def test_get_race_success(self, mock_context, respx_mock, sample_race_details):
        """Test successful retrieval of race details"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/dates/2025-10-29/meetings/R/RAN/races/1"
        )
        route.return_value = Response(200, json=sample_race_details)

        server = create_server()
        result = server.tool_manager.tools["racing_get_race"].fn(
            mock_context,
            access_token="test_token",
            meeting_date="2025-10-29",
            race_type="R",
            venue_mnemonic="RAN",
            race_number=1
        )

        assert route.called
        assert result["raceNumber"] == 1
        assert "runners" in result
        assert len(result["runners"]) == 2

    def test_get_race_with_fixed_odds(self, mock_context, respx_mock, sample_race_details):
        """Test race retrieval with fixed odds parameter"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/dates/2025-10-29/meetings/R/RAN/races/1"
        )
        route.return_value = Response(200, json=sample_race_details)

        server = create_server()
        result = server.tool_manager.tools["racing_get_race"].fn(
            mock_context,
            access_token="test_token",
            meeting_date="2025-10-29",
            race_type="R",
            venue_mnemonic="RAN",
            race_number=1,
            fixed_odds=True
        )

        assert route.called
        assert "fixedOdds=true" in str(route.calls[0].request.url)

    def test_get_race_invalid_race_type(self, mock_context):
        """Test invalid race type raises error"""
        server = create_server()
        
        with pytest.raises(ValueError, match="Invalid race type"):
            server.tool_manager.tools["racing_get_race"].fn(
                mock_context,
                access_token="test_token",
                meeting_date="2025-10-29",
                race_type="X",  # Invalid
                venue_mnemonic="RAN",
                race_number=1
            )


@pytest.mark.unit
@pytest.mark.racing
class TestRacingNextToGo:
    """Test racing_get_next_to_go tool"""

    def test_next_to_go_success(self, mock_context, respx_mock, sample_next_to_go):
        """Test successful retrieval of next-to-go races"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/next-to-go/races"
        )
        route.return_value = Response(200, json=sample_next_to_go)

        server = create_server()
        result = server.tool_manager.tools["racing_get_next_to_go"].fn(
            mock_context,
            access_token="test_token"
        )

        assert route.called
        assert "races" in result
        assert len(result["races"]) == 2
        assert result["races"][0]["secondsToJump"] == 300

    def test_next_to_go_with_max_races(self, mock_context, respx_mock, sample_next_to_go):
        """Test next-to-go with maxRaces parameter"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/next-to-go/races"
        )
        route.return_value = Response(200, json=sample_next_to_go)

        server = create_server()
        result = server.tool_manager.tools["racing_get_next_to_go"].fn(
            mock_context,
            access_token="test_token",
            max_races=5
        )

        assert route.called
        assert "maxRaces=5" in str(route.calls[0].request.url)

    def test_next_to_go_with_filters(self, mock_context, respx_mock, sample_next_to_go):
        """Test next-to-go with includeRecentlyClosed filter"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/racing/next-to-go/races"
        )
        route.return_value = Response(200, json=sample_next_to_go)

        server = create_server()
        result = server.tool_manager.tools["racing_get_next_to_go"].fn(
            mock_context,
            access_token="test_token",
            include_recently_closed=True
        )

        assert route.called
        assert "includeRecentlyClosed=true" in str(route.calls[0].request.url)
