from h.subtask import model


def hello_world(request):
    return {'hello': 'world!'}


def query(kn, querying):
    response_list = kn.query_retrieval_optimised([querying])

    topics, status = [], '200'
    for topic in response_list:
        results = []
        for i, (doc, score) in enumerate(topic):
            m = doc.metadata
            summary = m.get("summary", "")
            if isinstance(summary, dict) and 'input_documents' in summary:
                m["summary"] = summary.get("output_text", m.get("url", ""))
            results.append({'id': i, 'page_content': doc.page_content, 'metadata': m, 'score': score})
        topics.append(results)
    top20 = topics[0][:20] if topics else []
    return {'status': status, 'query': querying, 'context': [top20]}


def knowledge_pushing(kn, payload):
    # is_valid = validate_payload(payload, request_schema)
    # if not is_valid:
    #     log.error('request error')
    #     return

    content = payload["textContent"]
    response = kn.knowledge_pushing(content)

    summary = response[0]
    response_list = response[1]
    topics = []
    for topic in response_list:
        results = []
        for i, (doc, score) in enumerate(topic):
            m = doc.metadata
            if isinstance(m.get("summary", {}), dict):
                m["summary"] = m["summary"].get("output_text", m.get("title", ""))
            results.append({'id': i, 'page_content': doc.page_content, 'metadata': m, 'score': score})
        topics.append(results)
        top5 = topics[0][:5] if topics else []

    return {
        "client_id": payload['client_id'],
        "type": "knowledge-push",
        "payload": {
            "summary": summary,
            "context": [top5]
        }
    }


def includeme(config):  # pragma: no cover
    repository = config.registry.settings.get("kn.repository")
    database = config.registry.settings.get("kn.database")
    model_name = config.registry.settings.get("kn.model_name")

    # log

    kn = model.Knowledge_Nuggest(model_name, repository, database)
    config.registry["kn"] = kn
