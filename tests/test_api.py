def test_seeds_and_health(client):
    assert client.get('/health').json()['mode'] == 'offline'
    assert len(client.get('/api/runbooks').json()) >= 5


def test_draft_has_sources_and_quality(client):
    r = client.post('/api/draft', json={'summary': 'Login service is failing for some customers'})
    assert r.status_code == 200
    body = r.json()
    assert body['quality']['passed']
    assert body['sources']
    assert 'Next update:' in body['draft']
    assert len(client.get('/api/history').json()) == 1


def test_compare_three_variants_without_history(client):
    r = client.post('/api/compare', json={'summary': 'Payment processing is delayed'})
    assert r.status_code == 200
    assert len(r.json()['variants']) == 3
    assert client.get('/api/history').json() == []


def test_validation(client):
    assert client.post('/api/draft', json={'summary': 'x'}).status_code == 422
    assert client.get('/api/search?q=').status_code == 400


def test_evaluation(client):
    assert client.get('/api/evaluate').json()['passed'] == 3
