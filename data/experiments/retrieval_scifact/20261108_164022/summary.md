# Retrieval recall on SciFact (BM25, full corpus)

188 SciFact dev claims with gold evidence; corpus of 5183 abstracts split into 16386 chunks. No API calls.

| k | Gold abstract in top k | Gold rationale sentence in top k |
|---|---|---|
| 1 | 64.4% | 36.7% |
| 4 | 81.9% | 64.4% |
| 8 | 90.4% | 75.0% |
| 20 | 93.1% | 82.5% |

Index build 1.05s, mean query 2.64 ms.
