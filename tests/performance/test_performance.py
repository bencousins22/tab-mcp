"""Performance and load tests for Tabcorp MCP Server

These tests measure response times and system behavior under load.
Run with: pytest tests/performance -v -m performance
"""
import pytest
import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import respx
from httpx import Response

from tab_mcp.server import create_server


@pytest.mark.performance
class TestOAuthPerformance:
    """Test OAuth authentication performance"""

    def test_oauth_response_time(self, mock_context, respx_mock, valid_oauth_response, benchmark):
        """Benchmark OAuth token request time"""
        route = respx_mock.post("https://api.beta.tab.com.au/oauth/token")
        route.return_value = Response(200, json=valid_oauth_response)

        server = create_server()
        
        def oauth_call():
            return server.tool_manager.tools["tab_oauth_client_credentials"].fn(
                mock_context,
                client_id="test",
                client_secret="test"
            )

        # Benchmark the call
        result = benchmark(oauth_call)
        assert "access_token" in result

    def test_oauth_concurrent_requests(self, mock_context, respx_mock, valid_oauth_response):
        """Test OAuth under concurrent load"""
        route = respx_mock.post("https://api.beta.tab.com.au/oauth/token")
        route.return_value = Response(200, json=valid_oauth_response)

        server = create_server()
        
        def oauth_call():
            return server.tool_manager.tools["tab_oauth_client_credentials"].fn(
                mock_context,
                client_id="test",
                client_secret="test"
            )

        # Simulate 10 concurrent requests
        num_requests = 10
        response_times = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(oauth_call) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                start = time.time()
                result = future.result()
                response_times.append(time.time() - start)
                assert "access_token" in result

        # Verify all requests completed
        assert len(response_times) == num_requests
        
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"\nConcurrent OAuth Performance:")
        print(f"  Average response time: {avg_time:.3f}s")
        print(f"  Max response time: {max_time:.3f}s")
        print(f"  Requests completed: {num_requests}")


@pytest.mark.performance
class TestRacingPerformance:
    """Test Racing API performance"""

    def test_racing_dates_response_time(self, mock_context, respx_mock, benchmark):
        """Benchmark racing dates request time"""
        response_data = {
            "dates": [
                {"date": "2025-10-29", "meetingCount": 15}
                for _ in range(30)  # 30 days of data
            ]
        }
        
        route = respx_mock.get("https://api.beta.tab.com.au/v1/tab-info-service/racing/dates")
        route.return_value = Response(200, json=response_data)

        server = create_server()
        
        def racing_call():
            return server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
                mock_context,
                access_token="test_token"
            )

        result = benchmark(racing_call)
        assert "dates" in result

    def test_multiple_race_queries(self, mock_context, respx_mock, sample_race_details):
        """Test performance of multiple race queries"""
        route = respx_mock.get(
            "https://api.beta.tab.com.au/v1/tab-info-service/racing/dates/2025-10-29/meetings/R/RAN/races/1"
        )
        route.return_value = Response(200, json=sample_race_details)

        server = create_server()
        
        num_queries = 20
        start_time = time.time()
        
        for _ in range(num_queries):
            result = server.tool_manager.tools["racing_get_race"].fn(
                mock_context,
                access_token="test_token",
                meeting_date="2025-10-29",
                race_type="R",
                venue_mnemonic="RAN",
                race_number=1
            )
            assert "runners" in result

        total_time = time.time() - start_time
        avg_time = total_time / num_queries
        
        print(f"\nMultiple Race Queries Performance:")
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Average per query: {avg_time:.3f}s")
        print(f"  Queries per second: {num_queries/total_time:.2f}")
        
        # Should handle at least 10 queries per second
        assert num_queries / total_time >= 10


@pytest.mark.performance
class TestSportsPerformance:
    """Test Sports API performance"""

    def test_sports_list_response_time(self, mock_context, respx_mock, sample_sports_list, benchmark):
        """Benchmark sports list request time"""
        route = respx_mock.get("https://api.beta.tab.com.au/v1/tab-info-service/sports")
        route.return_value = Response(200, json=sample_sports_list)

        server = create_server()
        
        def sports_call():
            return server.tool_manager.tools["sports_get_all_open"].fn(
                mock_context,
                access_token="test_token"
            )

        result = benchmark(sports_call)
        assert "sports" in result


@pytest.mark.performance
class TestErrorHandlingPerformance:
    """Test error handling performance"""

    def test_error_response_time(self, mock_context, respx_mock, benchmark):
        """Benchmark error handling response time"""
        error_data = {
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR"
            }
        }
        
        route = respx_mock.get("https://api.beta.tab.com.au/v1/tab-info-service/racing/dates")
        route.return_value = Response(500, json=error_data)

        server = create_server()
        
        def error_call():
            try:
                server.tool_manager.tools["racing_get_all_meeting_dates"].fn(
                    mock_context,
                    access_token="test_token"
                )
            except Exception:
                pass  # Expected to fail

        # Error handling should be fast
        benchmark(error_call)


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage and efficiency"""

    def test_large_response_handling(self, mock_context, respx_mock):
        """Test handling of large API responses"""
        # Create large response with many runners
        large_response = {
            "raceNumber": 1,
            "raceName": "Large Field Race",
            "runners": [
                {
                    "runnerNumber": str(i),
                    "runnerName": f"Runner {i}",
                    "barrier": i,
                    "fixedOdds": {"returnWin": 5.00 + i * 0.1}
                }
                for i in range(1, 51)  # 50 runners
            ]
        }
        
        route = respx_mock.get(
            "https://api.beta.tab.com.au/v1/tab-info-service/racing/dates/2025-10-29/meetings/R/RAN/races/1"
        )
        route.return_value = Response(200, json=large_response)

        server = create_server()
        
        start_time = time.time()
        result = server.tool_manager.tools["racing_get_race"].fn(
            mock_context,
            access_token="test_token",
            meeting_date="2025-10-29",
            race_type="R",
            venue_mnemonic="RAN",
            race_number=1
        )
        processing_time = time.time() - start_time
        
        # Verify all runners processed
        assert len(result["runners"]) == 50
        
        # Should handle large responses quickly
        assert processing_time < 1.0  # Less than 1 second
        
        print(f"\nLarge Response Handling:")
        print(f"  Runners processed: 50")
        print(f"  Processing time: {processing_time:.3f}s")
