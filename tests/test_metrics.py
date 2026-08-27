import sys
from pathlib import Path

# Add scripts to sys.path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from evaluate import average_precision, dcg, ndcg

def test_dcg_and_ndcg_are_bounded_and_order_sensitive():
    labels = [3.0, 2.0, 0.0]
    assert dcg(labels, 3) > 0
    assert ndcg(labels, labels, 3) == 1.0
    assert ndcg([0.0, 0.0, 3.0], labels, 3) < 1.0

def test_average_precision_uses_positive_relevance():
    # AP = (1/1 + 2/3) / 2 = (1 + 0.666) / 2 = 0.8333
    assert average_precision([3.0, 0.0, 2.0]) == (1.0 + 2.0 / 3.0) / 2.0
    assert average_precision([0.0, 3.0, 0.0]) == 0.5
    assert average_precision([0.0, 0.0]) == 0.0
