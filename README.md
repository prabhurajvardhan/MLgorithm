BM25 Name-Based Candidate Generation

1. Overview

This module implements name-based candidate generation for business entity resolution.

The objective is not to determine the final entity match directly. Instead, the objective is to reduce the extremely large search space by retrieving a smaller set of potentially matching records from the reference datasets.

The overall problem can be represented as:

S1 Business Record
       |
       v
Candidate Generation
       |
       +---- Name-based candidates
       |
       +---- Address-based candidates
       |
       +---- Other attribute-based candidates
       |
       v
Union of Candidates
       |
       v
Final Pairwise Matching / Entity Resolution

This module focuses specifically on the business-name retrieval layer.

---

2. Problem Statement

For each business record in S1, potential matching records need to be identified from S2 and S3.

The datasets contain a very large number of records. Comparing every S1 record against every S2/S3 record would create an extremely large number of candidate pairs.

Therefore, performing detailed pairwise comparison over the complete datasets is computationally expensive and unnecessary.

We need an efficient candidate-generation / blocking strategy that:

1. Reduces the number of candidate pairs.
2. Retains genuine matching records with high recall.
3. Handles noisy and inconsistent business names.
4. Avoids using an arbitrary fixed number of candidates for every query.

---

3. Why Business Names?

Business names are one of the strongest identifying attributes available in the datasets.

However, business names are not always identical even when two records represent the same business.

Typical variations include:

- Spelling variations
- Abbreviations
- Punctuation differences
- Different word ordering
- Missing or additional words
- Legal entity suffixes
- Token variations
- Formatting differences
- Minor typographical errors

For example:

ABC Technologies Pvt Ltd
ABC Technology Private Limited

or:

Sri Lakshmi Hotel
Sri Lakshmi Hotels

An exact string comparison would fail to identify some of these relationships.

Therefore, exact matching alone is insufficient for candidate generation.

---

4. Why BM25?

To handle lexical variations in business names, we use BM25 (Best Matching 25) for name-based retrieval.

BM25 is an information-retrieval scoring method that measures how relevant a candidate document is to a query based on its terms.

In our setting:

- The S1 business name acts as the query.
- Business names in S2/S3 act as documents.
- BM25 produces a relevance score between the query name and each candidate name.

Conceptually:

S1 Business Name
       |
       v
     BM25
       |
       v
Rank S2/S3 business names
       |
       v
Highest lexical similarity
       |
       v
Potential candidates

BM25 is useful here because it considers token-level lexical similarity rather than requiring complete string equality.

However, BM25 is not treated as the final entity-resolution decision.

It is used only to generate a candidate set.

---

5. The Candidate-Count Problem

After applying BM25, the next question is:

«How many retrieved candidates should be retained for each S1 query?»

A simple approach would be to use a fixed top-K value:

Top 50
Top 100
Top 500

However, this introduces an important limitation.

Different business names produce very different BM25 score distributions.

For example:

Query A:
100.0
98.7
97.5
96.9
20.2
19.7
...

Query B:
15.4
14.9
14.7
14.5
14.2
13.9
...

For Query A, useful candidates may be concentrated near the top.

For Query B, relevant candidates may appear much farther down the ranking.

Therefore:

«A fixed K treats every query in the same way even though their BM25 score distributions can be very different.»

This motivates a score-based cutoff rather than a fixed candidate count.

---

6. Query-Specific BM25 Score Deviation

For each S1 query, let the highest BM25 score be:

[
S_{\max}
]

For every retrieved candidate with score:

[
S_i
]

we calculate its deviation from the strongest result:

[
D_i = S_{\max} - S_i
]

where:

- S_{\max} = highest BM25 score for that query
- S_i = BM25 score of candidate i
- D_i = BM25 score deviation

We call D_i the BM25 score deviation.

This allows us to ask a query-independent question:

«How much weaker than the strongest result are we willing to go?»

Instead of saying:

«"Always keep the top 100 records."»

we can say:

«"Keep candidates whose BM25 score is sufficiently close to the strongest score for this query."»

---

7. Candidate Selection Rule

For a selected deviation threshold BP, a candidate is retained when:

[
D_i \leq BP
]

Since:

[
D_i = S_{\max} - S_i
]

the equivalent condition is:

[
S_{\max} - S_i \leq BP
]

Therefore:

[
\boxed{S_i \geq S_{\max} - BP}
]

For our initial experiments, the selected deviation threshold is:

[
\boxed{BP = 2.8}
]

Therefore, the initial candidate-generation rule becomes:

[
\boxed{S_i \geq S_{\max} - 2.8}
]

This means that for every S1 business, we retain S2/S3 business names whose BM25 score is no more than 2.8 points below that query's strongest BM25 score.

---

8. Why 2.8?

The value 2.8 was not manually selected.

Choosing a threshold arbitrarily would make the methodology difficult to justify.

For example, simply saying:

BP = 2.8

would raise several questions:

- Why 2.8?
- Why not 1.5?
- Why not 5?
- Why not 10?
- Was the value chosen after looking at only one example?
- Does the value generalize to other queries?

Therefore, the threshold was selected through an experimental, data-driven procedure.

---

9. Experimental Methodology

We sampled 1,000 S1 entities and examined their BM25 retrieval results.

For different possible deviation thresholds, we measured how many known matching records were successfully recovered.

The important evaluation metric was:

Ground-Truth Recall

[
Recall =
\frac{\text{Number of known true matches recovered}}
{\text{Total number of known true matches}}
]

The purpose of this experiment was to understand the trade-off between:

Deviation threshold
        |
        +---- Candidate count
        |
        +---- Ground-truth recall

---

10. Threshold vs Recall

The expected behavior is:

Small deviation
      |
      v
Fewer candidates
      |
      v
Lower recall

As the deviation threshold increases:

Larger deviation
      |
      v
More candidates
      |
      v
Higher recall

However, after a certain point, increasing the deviation continues to increase the candidate set while providing progressively smaller improvements in recall.

This creates a diminishing-return region.

Conceptually:

Recall
  ^
  |                         ________
  |                     ___/
  |                 ___/
  |             ___/
  |         ___/
  |     ___/
  |____/
  +----------------------------------> BM25 deviation
                   ^
                   |
                 Knee

The objective is therefore not simply to maximize recall by retrieving an extremely large number of candidates.

Instead, we want to identify a region where the useful recall improvement begins to diminish relative to the additional candidate search space.

---

11. Knee-Point Detection

To make the threshold selection data-driven, we identify the knee point of the recall curve.

The knee represents the region where the curve changes from relatively rapid improvement to comparatively slower improvement.

Rather than selecting the knee visually, we use a geometric approach.

Geometric Interpretation

Imagine drawing a straight line between the beginning and ending points of the recall curve.

For every threshold value, calculate how far the actual recall curve lies above this reference line.

Conceptually:

Recall
  ^
  |                         *
  |                     *       *
  |                 *
  |             *
  |         *
  |      *
  |   *
  | *
  +----------------------------------> Deviation
    \_______________________________
             Reference line

The threshold with the maximum perpendicular distance from the reference line is treated as the knee point.

This provides a reproducible mathematical procedure instead of selecting a threshold by visual inspection.

---

12. Why Use the Knee Point?

The knee-point approach provides a practical compromise between:

Too Small a Threshold

Small candidate set
        |
        v
Lower computational cost
        |
        v
But potentially lower recall

Too Large a Threshold

Large candidate set
        |
        v
Higher recall
        |
        v
More pairwise comparisons
        |
        v
Higher computational cost

The knee provides a data-driven operating point where the recall improvement begins to show diminishing returns compared with the additional candidate space.

---

13. Stability Experiment

A single sample could produce a threshold that is specific to that particular sample.

Therefore, the experiment was repeated using five independent samples.

The observed results were:

Experiment| Knee Deviation| Recall
1| 2.8| 89.62%
2| 3.1| 91.94%
3| 2.8| 89.75%
4| 2.9| 89.81%
5| 2.8| 89.80%

The detected knee values remained within:

[
2.8 \leq BP \leq 3.1
]

The median knee deviation was:

[
\boxed{2.8}
]

This repeated behavior provides evidence that the observed threshold is not simply an artifact of one particular random sample.

---

14. Decision

Based on the repeated experiments:

- The knee consistently occurred around 2.8–3.1.
- The median knee deviation was 2.8.
- Therefore, 2.8 is selected as the initial name-based candidate-generation deviation.

The resulting rule is:

[
\boxed{S_i \geq S_{\max} - 2.8}
]

or equivalently:

[
\boxed{D_i \leq 2.8}
]

where:

[
D_i = S_{\max} - S_i
]

---

15. Important Interpretation

The value 2.8 should not be interpreted as a universal BM25 constant.

It is a dataset-driven operating threshold obtained from the observed ground-truth recall behavior of the current data.

Its purpose is to provide an initial, evidence-based candidate-generation cutoff rather than an arbitrary fixed value.

If the dataset, BM25 configuration, text preprocessing, or data distribution changes substantially, the threshold should be re-evaluated using the same experimental procedure.

---

16. Why We Do Not Use BM25 as the Final Matcher

BM25 only captures lexical similarity between business names.

This creates two important cases.

Case 1: True Match With Weak Name Similarity

Two records may represent the same business but have substantially different names because of:

- Abbreviations
- Name changes
- Transliteration
- Missing tokens
- Spelling differences
- Different legal naming conventions

The name score may therefore be relatively weak.

However, their addresses or other attributes may strongly agree.

Case 2: Similar Name But Different Business

Two unrelated businesses may have very similar or identical names.

For example:

ABC Restaurant
ABC Restaurant

may refer to different businesses operating at different locations.

Therefore, name similarity alone cannot establish the final identity.

---

17. Multi-Attribute Candidate Generation

The BM25 name retrieval layer is therefore only the first candidate-generation mechanism.

The overall candidate-generation process is:

                     S1 Record
                         |
             +-----------+-----------+
             |                       |
             v                       v
       Name Blocking           Address Blocking
          (BM25)                   (...)
             |                       |
             v                       v
       Name Candidates         Address Candidates
             |                       |
             +-----------+-----------+
                         |
                         v
                  UNION OF CANDIDATES
                         |
                         v
              Final Pairwise Matching
                         |
                         v
              Multi-Attribute Scoring

The union of candidates from different blocking strategies forms the search space for the final matching stage.

This reduces the risk that a genuine match is lost simply because it had a weak name similarity.

---

18. End-to-End Methodology

The complete reasoning chain is:

Millions of S2/S3 records
          |
          v
Comparing every pair is computationally expensive
          |
          v
Need candidate generation / blocking
          |
          v
Business name is a strong identifying attribute
          |
          v
But names contain noise and variations
          |
          v
Exact matching is insufficient
          |
          v
Use BM25 for lexical name retrieval
          |
          v
BM25 produces ranked candidates
          |
          v
Need to determine how many candidates to retain
          |
          v
Fixed top-K is query-independent
          |
          v
Different queries have different score distributions
          |
          v
Use score deviation from each query's best result
          |
          v
D_i = S_max - S_i
          |
          v
Evaluate ground-truth recall at different deviations
          |
          v
Recall increases as the candidate set expands
          |
          v
Eventually recall gains begin to diminish
          |
          v
Identify the mathematical knee of the recall curve
          |
          v
Repeat using 5 independent samples
          |
          v
Knee remains around 2.8–3.1
          |
          v
Median knee = 2.8
          |
          v
Select BP = 2.8 as initial name threshold
          |
          v
S_i >= S_max - 2.8
          |
          v
Generate name-based candidates
          |
          v
UNION with address / other attribute candidates
          |
          v
Final pairwise matching

---

19. Computational Benefit

Without candidate generation, the number of possible comparisons grows approximately as:

[
|S1| \times (|S2| + |S3|)
]

For large datasets, this can result in an extremely large number of pairwise comparisons.

Candidate generation reduces this search space by retaining only records that satisfy the blocking criteria.

Therefore:

Full Dataset
    |
    |  millions of possible pairs
    v
Candidate Generation
    |
    |  much smaller candidate set
    v
Detailed Pairwise Matching

The purpose of this stage is therefore to achieve a practical balance between:

- Recall — retaining genuine matches.
- Candidate volume — avoiding unnecessary comparisons.
- Computational efficiency — reducing downstream matching cost.

---

20. Key Design Decisions

Decision| Reason
Use business names for initial retrieval| Names are strong identifying attributes
Use BM25| Handles token-level lexical similarity and ranking
Do not use exact matching alone| Business names contain variations and noise
Do not use fixed top-K| Different queries have different score distributions
Use score deviation| Provides a query-relative cutoff
Evaluate against ground truth| Allows threshold selection based on actual recovery
Use recall curve| Measures how many known matches are retained
Detect the knee| Identifies diminishing-return region
Repeat experiments| Tests threshold stability
Select median knee = 2.8| Provides an evidence-based initial threshold
Do not use BM25 as final matcher| Name similarity alone cannot establish entity identity
Union with other blocking methods| Protects against weak name similarity
Perform final pairwise matching afterward| Allows multiple attributes to determine the final relationship

---

21. Final Candidate Rule

For each S1 business:

1. Retrieve S2/S3 records using BM25 on the business name.
2. Identify the highest BM25 score:

[
S_{\max}
]

3. Calculate the deviation for each candidate:

[
D_i = S_{\max} - S_i
]

4. Retain candidates satisfying:

[
\boxed{D_i \leq 2.8}
]

or:

[
\boxed{S_i \geq S_{\max} - 2.8}
]

5. Combine these name-based candidates with candidates generated using other attributes such as address and country.

6. Pass the resulting candidate pairs to the final entity-resolution stage.

---

22. Important Limitation

The BM25 threshold is a candidate-generation threshold, not a final match threshold.

A candidate falling outside the name-based threshold does not necessarily mean that the two businesses are different.

Similarly, a candidate inside the threshold does not necessarily mean that the two businesses are the same.

The final decision must consider multiple available attributes.

Therefore:

«Candidate generation prioritizes recall and computational efficiency, while final matching determines entity identity using richer evidence.»

---

23. Reproducibility

The threshold-selection experiment should be reproducible by recording:

- Dataset/version used
- Number of sampled S1 entities
- Sampling procedure
- Random seeds, where applicable
- BM25 implementation/configuration
- Text preprocessing/tokenization procedure
- Candidate retrieval depth
- Tested deviation values
- Ground-truth definition
- Recall calculation
- Knee-point calculation method
- Results from each independent experiment
- Final selected threshold

This ensures that the choice of BP = 2.8 can be independently verified rather than appearing to be a manually chosen constant.

---

24. Summary

The candidate-generation methodology follows a problem-driven approach:

«Large search space → need blocking → names are useful but noisy → use BM25 → fixed K is not query-adaptive → use score deviation → evaluate recall using ground truth → identify diminishing returns → detect the knee → validate across independent samples → select 2.8 as the initial deviation → combine with other blocking strategies → perform final pairwise matching.»

The key principle is:

[
\boxed{\text{Do not choose the candidate threshold arbitrarily.}}
]

Instead:

[
\boxed{\text{Choose it from observed recall behavior and validate its stability.}}
]

This makes the candidate-generation stage both computationally practical and experimentally defensible.