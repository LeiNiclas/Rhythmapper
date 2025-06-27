def get_optimal_wait_time(request) -> float:
    """
    Calculate the optimal wait time between requests to avoid hitting the rate limit.
    
    Args:
        request (requests.Response): _The response object from the request._
    
    Returns:
        time (float): _The optimal wait time in seconds._
    """
    try:
        remaining = int(request.headers.get("Ratelimit-Remaining", 0))
        reset = int(request.headers.get("Ratelimit-Reset", 1))
    
        if remaining > 5:
            return 0.2
        elif remaining > 0:
            return max(reset / remaining, 1.0)
        else:
            return max(reset, 1.0)
    except Exception:
        return 0.5
