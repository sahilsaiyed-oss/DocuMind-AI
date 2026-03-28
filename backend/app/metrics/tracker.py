import structlog

logger = structlog.get_logger()

# Dummy functions taaki crash na ho
def log_query(query_text, response_text, sources_used, retrieval_score, latency_ms, session_id):
    logger.info("query_logged_locally", query=query_text[:50], latency=latency_ms)
    return True

def get_metrics_summary():
    return {"status": "Metrics are disabled in local mode"}

def track_feedback(query_id, is_positive):
    logger.info("feedback_received", status=is_positive)
    return True