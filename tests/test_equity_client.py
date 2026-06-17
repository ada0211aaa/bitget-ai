import json

from bitget_ai_backtest.equity_client import YahooChartDailyClient, parse_yahoo_chart_response


def test_parse_yahoo_chart_response_converts_daily_rows_to_candles() -> None:
    raw = {
        "chart": {
            "result": [
                {
                    "timestamp": [1780876800, 1780963200],
                    "indicators": {
                        "quote": [
                            {
                                "open": [100.0, 101.0],
                                "high": [102.0, 104.0],
                                "low": [99.0, 100.0],
                                "close": [101.0, 103.0],
                                "volume": [1000, 1200],
                            }
                        ],
                        "adjclose": [{"adjclose": [101.0, 103.0]}],
                    },
                }
            ],
            "error": None,
        }
    }

    candles = parse_yahoo_chart_response(raw)

    assert len(candles) == 2
    assert candles[0].timestamp_ms == 1780876800000
    assert candles[0].open == 100.0
    assert candles[0].close == 101.0
    assert candles[0].quote_volume == 101000.0
    assert candles[-1].close == 103.0


def test_parse_yahoo_chart_response_skips_incomplete_rows() -> None:
    raw = json.loads(
        """
{
  "chart": {
    "result": [
      {
        "timestamp": [1780876800, 1780963200],
        "indicators": {
          "quote": [
            {
              "open": [100.0, null],
              "high": [102.0, 104.0],
              "low": [99.0, 100.0],
              "close": [101.0, 103.0],
              "volume": [1000, 1200]
            }
          ]
        }
      }
    ],
    "error": null
  }
}
""".strip()
    )

    candles = parse_yahoo_chart_response(raw)

    assert len(candles) == 1
    assert candles[0].close == 101.0


def test_yahoo_chart_daily_url_maps_limit_to_period_range() -> None:
    client = YahooChartDailyClient()

    url = client.build_chart_url("NVDA", limit=365, now_timestamp=1781308800)

    assert "https://query1.finance.yahoo.com/v8/finance/chart/NVDA" in url
    assert "interval=1d" in url
    assert "events=history" in url
    assert "includeAdjustedClose=true" in url
    assert "period1=1749772800" in url
    assert "period2=1781308800" in url
