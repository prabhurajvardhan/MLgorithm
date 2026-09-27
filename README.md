BM25 Name-Based Candidate Generation

Overview

This module implements name-based candidate generation for business entity resolution.

The objective is not to determine the final entity match directly. Instead, it reduces the search space by retrieving a smaller set of potentially matching records from S2 and S3 for each S1 business record.

The methodology follows a data-driven reasoning chain:

Problem
   ↓
Observation
   ↓
Problem with Observation
   ↓
Solution
   ↓
Experiment
   ↓
Evidence
   ↓
Decision

---

1. Problem: Large Search Space

We start with one S1 business record and need to find possible matching businesses from S2 and S3.

Since S2 and S3 together contain millions of records, comparing every S1 record against every S2/S3 record would be extremely expensive.

Therefore, before performing detailed pairwise comparison, we need to reduce the search space.

S1 Business
     |
     v
Millions of S2/S3 Records
     |
     v
Full Pairwise Comparison
     |
     v
Extremely Large Search Space

This creates the need for an efficient candidate-generation stage.

---

2. Observation: Business Names Are Useful but Noisy

Business names are one of the strongest pieces of information available for identifying potentially matching businesses.

However, names are noisy and can differ because of:

- Abbreviations
- Spelling variations
- Punctuation
- Word-order changes
- Legal suffixes
- Other naming variations

For example:

S1:
ABC TECHNOLOGIES PVT LTD

S2:
ABC Technologies Private Limited

Although these names may refer to the same business, exact string matching may fail.

Therefore, exact matching is not sufficient for candidate generation.

---

3. Solution: BM25 Name Retrieval

To handle lexical variations in business names, we use BM25 to retrieve S2/S3 records whose business names have strong lexical similarity to the S1 name.

S1 Business Name
       |
       v
     BM25
       |
       v
Rank S2/S3 Business Names
       |
       v
Potential Name Candidates

BM25 is used specifically for candidate retrieval, not for making the final entity-resolution decision.

---

4. The Next Problem: How Many Candidates Should We Keep?

After BM25 produces ranked results, we need to decide:

«How many retrieved records should be retained for each query?»

A straightforward approach would be to use a fixed Top-K value such as:

Top 50
Top 100
Top 500

However, a fixed K treats every business name in the same way.

Different queries can have very different BM25 score distributions.

For one business, useful matches may appear within the first few results, while for another business, valid matches may occur much farther down the ranked list.

Therefore:

«A fixed Top-K value is query-independent and does not adapt to the retrieval behaviour of each individual query.»

Instead of always keeping the first K results, we examine the BM25 score distribution for each S1 query.

---

5. Key Idea: BM25 Score Deviation

For each S1 query, let the highest BM25 score be:

[
S_{\max}
]

For every retrieved result with score (S_i), calculate its deviation from the strongest result:

[
D_i = S_{\max} - S_i
]

We call (D_i) the BM25 score deviation.

This gives us a query-specific way of asking:

«How much weaker than the strongest result are we willing to go?»

Instead of defining the candidate set using a fixed number of records, we define it relative to the strongest BM25 result for that query.

---

6. Candidate Selection Rule

For a selected deviation threshold (BP), a candidate is retained when:

[
S_i \geq S_{\max} - BP
]

Equivalently:

[
D_i \leq BP
]

For example, if:

Strongest BM25 score = 10.0
BP = 2.8

then:

Minimum retained score = 10.0 - 2.8
                        = 7.2

Therefore:

BM25 ≥ 7.2  → Candidate retained
BM25 < 7.2  → Candidate excluded

---

7. Why 2.8?

The value 2.8 was not chosen manually.

To determine an appropriate deviation threshold, we sampled 1,000 S1 entities and examined their BM25 retrieval results.

For different deviation thresholds, we measured how many known matching records were successfully recovered.

This produced a recall curve.

The observed behaviour was:

Small deviation
      ↓
Few candidates
      ↓
Lower recall

Larger deviation
      ↓
More candidates
      ↓
Higher recall

Eventually:

Further increase in deviation
      ↓
More candidates
      ↓
Progressively smaller improvements in recall

Therefore, we looked for the knee of the recall curve — the point where useful recall improvement begins to diminish relative to the additional search space.

---

8. Knee-Point Detection

The knee can be understood without complicated mathematics.

Imagine drawing a straight line between the beginning and end of the recall curve.

For every deviation value, measure how far the actual recall curve rises above this reference line.

The point with the largest distance is treated as the knee point.

Conceptually:

Recall
  ^
  |
  |                         ______
  |                    ____/
  |                ___/
  |             __/
  |          __/
  |       __/
  |    __/
  |___/____________________________> Deviation
      ^
      |
     Knee

This provides a data-driven method for selecting the cutoff instead of manually choosing an arbitrary value such as "1.5", "2.8", or "5".

---

9. Experimental Results

The experiment was repeated using five independent samples.

Experiment| Knee Deviation| Recall
1| 2.8| 89.62%
2| 3.1| 91.94%
3| 2.8| 89.75%
4| 2.9| 89.81%
5| 2.8| 89.80%

The detected knee remained between:

[
2.8 \text{ and } 3.1
]

with a median of:

[
2.8
]

---

10. Evidence From Repeated Experiments

The result was not based on a single random sample.

The experiment was repeated five times using independent samples.

The detected knee consistently remained within:

2.8 – 3.1

This stability provides evidence that the observed cutoff was not simply an artifact of one particular sample.

---

11. Decision: Initial BP = 2.8

Based on the repeated experiments, we use:

[
\boxed{BP = 2.8}
]

as the initial name-based candidate-generation deviation.

The resulting candidate-selection rule is:

[
\boxed{S_i \geq S_{\max} - 2.8}
]

In simple terms:

«For each S1 business, retain S2/S3 names whose BM25 score is no more than 2.8 below that query's strongest BM25 score.»

---

12. Important: BM25 Is Not the Final Entity-Matching Decision

The name-based retrieval stage is only the first candidate-generation layer.

We deliberately do not make the final entity-matching decision using BM25 alone.

A genuine match can have relatively weak name similarity but a highly similar address.

Conversely, unrelated businesses can have very similar names.

Therefore:

BM25 Candidate
      ≠
Final Match

The purpose of this stage is to identify plausible records that should proceed to the next stage of entity resolution.

---

13. Connection to the Next Stage

Candidates generated from business names will later be combined with candidates generated from addresses and other available attributes.

The resulting union becomes the search space for the final pairwise matching stage.

                    S1 Business
                         |
            +------------+------------+
            |                         |
            v                         v
     Name Candidates          Address Candidates
            |                         |
            +------------+------------+
                         |
                         v
                        UNION
                         |
                         v
                Candidate Search Space
                         |
                         v
                Final Pairwise Matching
                         |
                         v
                Multi-Attribute Decision

This ensures that the final matching stage does not depend only on name similarity.

---

14. Complete Methodology

The complete reasoning chain is:

Millions of S2/S3 records
          ↓
Can't compare everything
          ↓
Need candidate generation
          ↓
Business name is useful but noisy
          ↓
Exact matching is not sufficient
          ↓
Use BM25 for lexical retrieval
          ↓
But how many results should we keep?
          ↓
Fixed K is query-independent
          ↓
Use score deviation from each query's best result
          ↓
Measure ground-truth recall at different deviations
          ↓
Recall increases as the candidate boundary expands
          ↓
Eventually recall gains begin to diminish
          ↓
Find the mathematical knee
          ↓
Repeat on 5 independent samples
          ↓
Knee consistently ≈ 2.8–3.1
          ↓
Choose 2.8 as the initial name BP
          ↓
Generate name candidates
          ↓
UNION with address/other candidates
          ↓
Final pairwise refinement

---

15. Methodology Summary

Stage| Decision
Search-space problem| Full S2/S3 comparison is too expensive
Observation| Business names are useful but noisy
Retrieval method| BM25
Candidate-count problem| Fixed Top-K is query-independent
Adaptive approach| BM25 score deviation
Evaluation| 1,000 sampled S1 entities
Evaluation metric| Known-match recall
Threshold selection| Knee of recall curve
Stability check| Five independent experiments
Observed knee range| 2.8–3.1
Median knee| 2.8
Initial BP| 2.8
Candidate rule| (S_i \geq S_{\max}-2.8)
Next stage| Union with address/other candidates
Final decision| Performed downstream using multiple attributes

---

16. Final Candidate Rule

For every S1 business:

Step 1 — Find the strongest BM25 score

[
S_{\max} = \max(S_1,S_2,\ldots,S_n)
]

Step 2 — Calculate deviation

[
D_i = S_{\max} - S_i
]

Step 3 — Apply the selected threshold

[
\boxed{D_i \leq 2.8}
]

or equivalently:

[
\boxed{S_i \geq S_{\max}-2.8}
]

Result

The retained records form the name-based candidate set.

These candidates are then combined with candidates generated from addresses and other available attributes before final pairwise matching.

---

17. Key Takeaway

The methodology is not simply:

«"We used BM25 + knee detection + threshold 2.8."»

The actual reasoning is:

Problem
   ↓
Large search space
   ↓
Need candidate generation
   ↓
Business names are useful but noisy
   ↓
BM25 retrieval
   ↓
Need to determine candidate boundary
   ↓
Fixed Top-K is query-independent
   ↓
Use query-specific score deviation
   ↓
Evaluate against known matches
   ↓
Measure recall at different deviations
   ↓
Observe diminishing returns
   ↓
Find the mathematical knee
   ↓
Repeat across 5 independent samples
   ↓
Knee consistently ≈ 2.8–3.1
   ↓
Select 2.8 as initial BP
   ↓
Generate name-based candidates
   ↓
UNION with address/other candidates
   ↓
Final pairwise refinement

Final Rule

[
\boxed{S_i \geq S_{\max}-2.8}
]

This threshold is used as the initial name-based candidate-generation boundary, not as the final entity-resolution decision.