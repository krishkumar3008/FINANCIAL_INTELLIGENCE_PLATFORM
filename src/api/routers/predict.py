from fastapi import APIRouter, HTTPException, Query
from src.analytics.predictor import predict_stock_tomorrow, get_top_forecasts
from src.etl.live_updater import fetch_and_update_prices

router = APIRouter()


@router.get("/predict/top-forecasts", summary="Get top bullish and bearish market forecasts for tomorrow")
def get_market_top_forecasts(
    top_n: int = Query(5, ge=1, le=20, description="Number of top bullish and bearish setups to return")
):
    """
    Evaluates machine learning market prediction models across all Nifty 100 constituents
    and returns top ranked Bullish and Bearish stocks for tomorrow.
    """
    try:
        results = get_top_forecasts(top_n=top_n)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate top forecasts: {str(e)}")


@router.get("/predict/{ticker}", summary="Get next-day market trend prediction for a stock")
def get_stock_prediction(ticker: str):
    """
    Generates machine learning next-day price forecast, directional signal (BULLISH/BEARISH),
    confidence percentage, price targets, and key technical indicators for a specific ticker.
    """
    ticker_clean = ticker.upper().strip()
    result = predict_stock_tomorrow(ticker_clean)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/predict/refresh-data", summary="Trigger live market data ingestion up to today")
def refresh_live_market_data():
    """
    Downloads latest daily stock price candles from Yahoo Finance (NSE) and updates the database.
    """
    try:
        updated_count = fetch_and_update_prices()
        return {
            "status": "success",
            "message": f"Live market data update complete. Updated {updated_count} price records."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market data update failed: {str(e)}")
