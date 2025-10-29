"""Unit tests for Sports API tools"""
import pytest
import respx
from httpx import Response

from tab_mcp.server import (
    create_server,
    TabcorpAPIError,
    TAB_BASE_URL
)


@pytest.mark.unit
@pytest.mark.sports
class TestSportsGetAllOpen:
    """Test sports_get_all_open tool"""

    def test_get_all_open_success(self, mock_context, respx_mock, sample_sports_list):
        """Test successful retrieval of all open sports"""
        route = respx_mock.get(f"{TAB_BASE_URL}/v1/tab-info-service/sports")
        route.return_value = Response(200, json=sample_sports_list)

        server = create_server()
        result = server.tool_manager.tools["sports_get_all_open"].fn(
            mock_context,
            access_token="test_token"
        )

        # Verify request
        assert route.called
        request = route.calls[0].request
        assert "Bearer test_token" in request.headers["authorization"]

        # Verify response
        assert "sports" in result
        assert len(result["sports"]) == 2
        assert result["sports"][0]["sportName"] == "Basketball"

    def test_get_all_open_with_jurisdiction(self, mock_context, respx_mock, sample_sports_list):
        """Test sports list with custom jurisdiction"""
        route = respx_mock.get(f"{TAB_BASE_URL}/v1/tab-info-service/sports")
        route.return_value = Response(200, json=sample_sports_list)

        server = create_server()
        result = server.tool_manager.tools["sports_get_all_open"].fn(
            mock_context,
            access_token="test_token",
            jurisdiction="QLD"
        )

        assert route.called
        assert "jurisdiction=QLD" in str(route.calls[0].request.url)


@pytest.mark.unit
@pytest.mark.sports
class TestSportsGetOpenSport:
    """Test sports_get_open_sport tool"""

    def test_get_open_sport_success(self, mock_context, respx_mock, sample_sport_competition):
        """Test successful retrieval of specific sport"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/Basketball"
        )
        route.return_value = Response(200, json={"competitions": [sample_sport_competition]})

        server = create_server()
        result = server.tool_manager.tools["sports_get_open_sport"].fn(
            mock_context,
            access_token="test_token",
            sport_name="Basketball"
        )

        assert route.called
        assert "competitions" in result

    def test_get_open_sport_not_found(self, mock_context, respx_mock):
        """Test sport not found returns error"""
        error_data = {
            "error": {
                "message": "Sport not found",
                "code": "NOT_FOUND"
            }
        }
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/InvalidSport"
        )
        route.return_value = Response(404, json=error_data)

        server = create_server()
        with pytest.raises(TabcorpAPIError) as exc_info:
            server.tool_manager.tools["sports_get_open_sport"].fn(
                mock_context,
                access_token="test_token",
                sport_name="InvalidSport"
            )

        assert exc_info.value.status_code == 404


@pytest.mark.unit
@pytest.mark.sports
class TestSportsGetOpenCompetition:
    """Test sports_get_open_competition tool"""

    def test_get_open_competition_success(self, mock_context, respx_mock, sample_sport_competition):
        """Test successful retrieval of competition"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/Basketball/competitions/NBA"
        )
        route.return_value = Response(200, json=sample_sport_competition)

        server = create_server()
        result = server.tool_manager.tools["sports_get_open_competition"].fn(
            mock_context,
            access_token="test_token",
            sport_name="Basketball",
            competition_name="NBA"
        )

        assert route.called
        assert result["competitionName"] == "NBA"
        assert "matches" in result
        assert len(result["matches"]) == 1


@pytest.mark.unit
@pytest.mark.sports
class TestSportsNextToGo:
    """Test sports_get_next_to_go tool"""

    def test_next_to_go_success(self, mock_context, respx_mock):
        """Test successful retrieval of next-to-go sports"""
        response_data = {
            "matches": [
                {
                    "matchName": "Lakers v Warriors",
                    "sportName": "Basketball",
                    "competitionName": "NBA",
                    "startTime": "2025-10-30T02:00:00Z"
                },
                {
                    "matchName": "Celtics v Heat",
                    "sportName": "Basketball",
                    "competitionName": "NBA",
                    "startTime": "2025-10-30T03:00:00Z"
                }
            ]
        }
        
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/nextToGo"
        )
        route.return_value = Response(200, json=response_data)

        server = create_server()
        result = server.tool_manager.tools["sports_get_next_to_go"].fn(
            mock_context,
            access_token="test_token"
        )

        assert route.called
        assert "matches" in result
        assert len(result["matches"]) == 2

    def test_next_to_go_with_limit(self, mock_context, respx_mock):
        """Test next-to-go with limit parameter"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/nextToGo"
        )
        route.return_value = Response(200, json={"matches": []})

        server = create_server()
        result = server.tool_manager.tools["sports_get_next_to_go"].fn(
            mock_context,
            access_token="test_token",
            limit=10
        )

        assert route.called
        assert "limit=10" in str(route.calls[0].request.url)

    def test_next_to_go_with_filters(self, mock_context, respx_mock):
        """Test next-to-go with multiple filters"""
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/nextToGo"
        )
        route.return_value = Response(200, json={"matches": []})

        server = create_server()
        result = server.tool_manager.tools["sports_get_next_to_go"].fn(
            mock_context,
            access_token="test_token",
            live_betting_only=True,
            open_only=True
        )

        assert route.called
        request_url = str(route.calls[0].request.url)
        assert "liveBettingOnly=true" in request_url
        assert "openOnly=true" in request_url


@pytest.mark.unit
@pytest.mark.sports
class TestSportsGetOpenMatch:
    """Test sports match retrieval tools"""

    def test_get_open_match_in_competition(self, mock_context, respx_mock):
        """Test retrieval of match in competition"""
        match_data = {
            "matchName": "Lakers v Warriors",
            "startTime": "2025-10-30T02:00:00Z",
            "markets": [
                {
                    "marketName": "Head To Head",
                    "propositions": [
                        {"name": "Lakers", "returnWin": 1.85},
                        {"name": "Warriors", "returnWin": 2.00}
                    ]
                }
            ]
        }
        
        route = respx_mock.get(
            f"{TAB_BASE_URL}/v1/tab-info-service/sports/Basketball/competitions/NBA/matches/Lakers v Warriors"
        )
        route.return_value = Response(200, json=match_data)

        server = create_server()
        result = server.tool_manager.tools["sports_get_open_match_in_competition"].fn(
            mock_context,
            access_token="test_token",
            sport_name="Basketball",
            competition_name="NBA",
            match_name="Lakers v Warriors"
        )

        assert route.called
        assert result["matchName"] == "Lakers v Warriors"
        assert "markets" in result
        assert len(result["markets"]) == 1
