from app.quality import score_draft
from app.search import embed, cosine, search


def test_embedding_is_deterministic_and_normalized():
    assert embed('payment delayed') == embed('payment delayed')
    assert abs(cosine(embed('payment delayed'), embed('payment delayed')) - 1) < 1e-8


def test_vector_retrieval():
    rows = [{'id':'a', 'title':'payments', 'content':'payment failed'},
            {'id':'b', 'title':'delivery', 'content':'parcel arrived'}]
    assert search('payment failed', rows, 1)[0]['id'] == 'a'


def test_eval_catches_unsupported_claim():
    result = score_draft('Impact: x\nAction: guaranteed resolved\nNext update: soon')
    assert not result['passed']
