CREATE OR REPLACE FUNCTION semantic_reranking3(query TEXT, vector_search_results TEXT[])
RETURNS TABLE (content TEXT, relevance NUMERIC) AS $$
BEGIN
    RETURN QUERY
        WITH
        json_pairs AS (
            SELECT jsonb_build_object(
                'pairs', jsonb_agg(jsonb_build_array(query, content_))
            ) AS json_pairs_data
            FROM (
                SELECT a.content AS content_
                FROM unnest(vector_search_results) AS a(content)
            )
        ),
        relevance_scores_raw AS (
            SELECT azure_ml.invoke(
                (SELECT json_pairs_data FROM json_pairs),
                deployment_name => 'msmarco-minilm-deployment-6',
                timeout_ms => 120000
            ) AS response_json
        ),
        relevance_scores AS (
            SELECT jsonb_array_elements(response_json) AS item
            FROM relevance_scores_raw
        )
        SELECT
            item ->> 'content' AS content,
            (item ->> 'score')::NUMERIC AS relevance
        FROM relevance_scores;
END
$$ LANGUAGE plpgsql;









WITH vector_results AS (
    SELECT content FROM sow_chunks c
    ORDER BY embedding <=> azure_openai.create_embeddings('embeddings', 'cost management and optimization')::vector
    LIMIT 10
)
SELECT content, relevance
FROM semantic_reranking3('cost management and optimization and price',  ARRAY(SELECT content from vector_results))
ORDER BY relevance DESC
LIMIT 3;







WITH vector_results AS (
    SELECT content FROM sow_chunks
    ORDER BY embedding <=> azure_openai.create_embeddings('embeddings', 'cost management and optimization')::vector
    LIMIT 10
),
json_pairs AS (
    SELECT jsonb_build_object(
        'pairs', jsonb_agg(jsonb_build_array('cost management and optimization and price', content))
    ) AS json_pairs_data
    FROM vector_results
),
debug_invoke AS (
    SELECT * FROM azure_ml.invoke(
        (SELECT json_pairs_data FROM json_pairs),
        deployment_name => 'msmarco-minilm-deployment-6', timeout_ms => 120000
    )
)
SELECT * FROM debug_invoke;





