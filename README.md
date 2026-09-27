
# Candidate Generation Methodology

## 1. Problem

We start with one S1 business record.

Our goal is to find possible matching businesses from S2 and S3.

Searching every S2/S3 record would be extremely expensive because together they contain millions of records. Therefore, before doing detailed comparison, we need a way to reduce the search space.

## 2. Observation: Business Names Are Useful but Noisy

Business names are one of the strongest pieces of information available.

However, names are noisy because of:

- Abbreviations.
- Spelling variations.
- Punctuation differences.
- Word-order changes.
- Legal suffixes.
- Other formatting variations.

Therefore, exact matching is not sufficient.

We use BM25 to retrieve S2/S3 records whose business names have strong lexical similarity to the S1 name.

BM25 is used for lexical retrieval because it can identify records that share important terms with the query name while accounting for term frequency and document frequency.

However, BM25 is used only to generate possible candidates. It is not used by itself to make the final entity-matching decision.

## 3. Problem: How Many Retrieved Records Should Be Kept?

After using BM25, another problem appears:

> How many retrieved records should we keep?

A fixed top-\(K\) value such as 50, 100, or 500 treats every business name the same.

However, different queries have very different BM25 score distributions:

- For one business, useful matches may appear within the first few results.
- For another business, valid matches may occur much farther down the result list.

Therefore, a fixed top-\(K\) value is query-independent and may either:

- Exclude valid matches when \(K\) is too small.
- Produce an unnecessarily large candidate set when \(K\) is too large.

Instead of always keeping the first \(K\) records, we examine the BM25 score distribution for each individual query.

## 4. Score-Deviation-Based Candidate Selection

For each S1 query, let the highest BM25 score be \(S_{\max}\).

For every subsequent result \(i\), we measure how far its score is from the strongest result:

\[
D_i = S_{\max} - S_i
\]

We call \(D_i\) the BM25 score deviation.

This gives us a query-independent way of asking:

> How much weaker than the strongest result are we willing to go?

A candidate is retained when its BM25 score satisfies:

\[
S_i \geq S_{\max} - D
\]

where \(D\) is the selected deviation threshold.

This approach adapts the number of retained candidates to the score distribution of each individual query instead of applying the same fixed number of candidates to every business.

## 5. Why the Deviation Threshold Was Not Chosen Manually

We did not choose the deviation value manually.

We sampled 1,000 S1 entities and examined their BM25 retrieval results.

For each possible deviation threshold, we measured how many known matching records were recovered. This produced a recall curve.

The general relationship was:

- Small deviation → fewer candidates → lower recall.
- Larger deviation → more candidates → higher recall.
- After a certain point, increasing the deviation continued to add candidates but produced progressively smaller improvements in recall.

Therefore, we looked for the knee of the recall curve.

The knee represents the point where the useful recall gain begins to diminish relative to the additional search space.

## 6. Knee-Point Detection

To identify the knee, we used the following geometric interpretation.

Imagine stretching a straight line between the beginning and end of the recall curve.

For every deviation value, we measure how far the actual recall curve rises above that line.

The point with the largest distance is treated as the knee point.

This gives us a data-driven way to select the cutoff rather than choosing an arbitrary threshold such as 1.5, 2.8, or 5.

The process can be represented as:

1. Sort the tested deviation values.
2. Calculate recall at every deviation value.
3. Draw a straight line between the first and last points of the recall curve.
4. Calculate the distance between every actual curve point and the straight line.
5. Select the deviation with the largest distance as the knee point.

The selected knee is the point where increasing the deviation provides the strongest trade-off between additional recall and additional candidate volume.

## 7. Experimental Evidence

We repeated the experiment five times using independent samples.

The results were:

| Experiment | Knee Deviation | Recall |
|---|---:|---:|
| 1 | 2.8 | 89.62% |
| 2 | 3.1 | 91.94% |
| 3 | 2.8 | 89.75% |
| 4 | 2.9 | 89.81% |
| 5 | 2.8 | 89.80% |

The detected knee stayed between 2.8 and 3.1.

The median knee deviation was 2.8.

The repeated experiments demonstrate that the result was not based on a single random sample. The knee remained within a narrow range across five independent samples, providing evidence that the selected cutoff was not simply an artifact of one particular sample.

## 8. Selected Initial Threshold

Based on the repeated experiments, we use 2.8 as the initial name-based candidate-generation deviation:

\[
\boxed{S_i \geq S_{\max} - 2.8}
\]

In other words, for each S1 business, we retain S2/S3 names whose BM25 score is no more than 2.8 below that query's strongest BM25 score.

This threshold is an initial name-based candidate-generation parameter. It is not a final entity-resolution threshold.

## 9. Candidate Generation Is Not Final Entity Resolution

Name-based retrieval is only the first candidate-generation layer.

We deliberately do not make the final entity-matching decision using BM25 alone.

A genuine match can have:

- Weak name similarity but a highly similar address.
- A different spelling or abbreviation.
- A different word order.
- A legal suffix or formatting difference.

Similarly, unrelated businesses can have very similar names.

Therefore, the candidates generated from business names will later be combined with candidates generated from addresses and other available attributes.

The resulting union of candidates becomes the search space for the final pairwise matching stage, where multiple features can be considered together.

The final matching stage can therefore combine evidence from:

- Business names.
- Addresses.
- Countries.
- Other available attributes.
- Pairwise similarity features.

BM25 helps reduce the search space, but it does not solve entity resolution by itself.

## 10. Methodology Decision Chain

The complete reasoning chain is:

```text
Millions of S2/S3 records
          ↓
Cannot compare every S1 record with every S2/S3 record
          ↓
Need candidate generation
          ↓
Business name is useful but noisy
          ↓
Exact name matching is not sufficient
          ↓
Use BM25 for lexical retrieval
          ↓
Need to decide how many retrieved results to keep
          ↓
Fixed K is query-independent
          ↓
Different queries have different BM25 score distributions
          ↓
Use score deviation from each query's best result
          ↓
Measure ground-truth recall at different deviation values
          ↓
Recall increases as the deviation increases
          ↓
Recall eventually shows diminishing returns
          ↓
Find the mathematical knee of the recall curve
          ↓
Repeat the experiment on five independent samples
          ↓
Knee consistently falls between approximately 2.8 and 3.1
          ↓
Median knee is 2.8
          ↓
Choose 2.8 as the initial name-based deviation threshold
          ↓
Generate name-based candidates
          ↓
Union name candidates with address and country candidates
          ↓
Use the combined candidate set for final pairwise refinement
```

## 11. Final Candidate-Generation Rule

For every S1 business:

1. Use the business name to retrieve candidate businesses from S2 and S3 using BM25.
2. Identify the maximum BM25 score for that query, \(S_{\max}\).
3. Retain every candidate whose score satisfies:

\[
S_i \geq S_{\max} - 2.8
\]

4. Generate additional candidates using address, country, and other available attributes.
5. Take the union of all generated candidates.
6. Pass the resulting candidate pairs to the final pairwise matching stage.
7. Use multiple features together to make the final entity-matching decision.

This design reduces the search space while preserving a data-driven basis for the number of name-based candidates retained.
