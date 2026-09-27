

# BM25 Name-Based Candidate Generation

## 1. Overview

This module implements **name-based candidate generation** for large-scale **Business Entity Resolution**.

The objective of this module is **not to determine the final entity match directly**.

Instead, it reduces the extremely large search space by retrieving a smaller set of **potentially matching records** from Source 2 (S2) and Source 3 (S3).

### Overall Pipeline

```text
                         S1 Business Record
                                |
                                v
                    Candidate Generation
                                |
              +-----------------+-----------------+
              |                 |                 |
              v                 v                 v
        Name Candidates   Address Candidates   Other
            (BM25)                              Attributes
              |                 |                 |
              +-----------------+-----------------+
                                |
                                v
                      Union of Candidates
                                |
                                v
                    Final Pairwise Matching
                                |
                                v
                       Entity Resolution

This module focuses specifically on the business-name retrieval layer.

> Key idea: BM25 is used to efficiently generate promising candidates. It is not used as the final entity-resolution decision.




---

2. Problem Statement

For every business record in Source 1 (S1), potential matching records need to be identified from Source 2 (S2) and Source 3 (S3).

The datasets contain a very large number of records.

A naïve approach would compare every S1 record with every S2 and S3 record:

Every S1 record
      |
      +---- Compare with every S2 record
      |
      +---- Compare with every S3 record

This creates an extremely large number of candidate pairs.

Performing detailed pairwise comparison across the complete datasets would therefore be:

Computationally expensive

Unnecessary for most record pairs

Difficult to scale


The Actual Problem

> How can we reduce the search space without losing genuine matches?



This leads to the need for an efficient candidate-generation / blocking strategy.

The candidate-generation stage should:

1. Reduce the number of candidate pairs


2. Retain genuine matching records with high recall


3. Handle noisy and inconsistent business names


4. Avoid arbitrary fixed candidate counts




---

3. Observation: Business Names Are Strong but Noisy

Business names are one of the strongest identifying attributes available in the datasets.

However, the same real-world business may appear differently across independent sources.

For example:

ABC Technologies Pvt Ltd
ABC Tech
A.B.C. Technologies Private Limited
ABC Technologies

Other common variations include:

Spelling variations

Abbreviations

Punctuation differences

Word-order changes

Missing words

Additional words

Legal entity suffixes

Formatting differences

Minor typographical errors


For example:

ABC Technologies Pvt Ltd
ABC Technology Private Limited

may refer to the same real-world business despite not being identical strings.

Similarly:

Sri Lakshmi Hotel
Sri Lakshmi Hotels

may represent the same entity.

Problem With Exact Matching

An exact string comparison would require:

String A == String B

But real-world entity data rarely satisfies this condition consistently.

Therefore:

> Exact string matching is insufficient for candidate generation.



We need a retrieval method that can identify records based on lexical similarity.


---

4. Solution: BM25 Name Retrieval

To handle lexical variations in business names, we use BM25 (Best Matching 25) for name-based retrieval.

BM25 is a classical information-retrieval scoring method that measures the relevance of a document to a query based on its terms.

In our setting:

BM25 Concept	Entity Resolution Equivalent

Query	S1 business name
Document	S2/S3 business name
Relevance score	BM25 similarity score
Search results	Potential matching candidates


Conceptually:

S1 Business Name
       |
       v
     BM25
       |
       v
Rank S2/S3 Business Names
       |
       v
Potential Candidate Records

The BM25 score provides a ranking of candidates according to their lexical relevance to the S1 business name.

BM25 is useful because it considers token-level lexical similarity rather than requiring complete string equality.

Important Distinction

> BM25 retrieves candidates; it does not establish entity identity.



The final entity-resolution decision is performed later using multiple attributes.


---

5. New Problem: How Many BM25 Results Should We Keep?

After BM25 retrieval, we obtain a ranked list of candidates.

For example:

Candidate        BM25 Score
---------------------------
Candidate A        10.4
Candidate B        10.1
Candidate C         9.8
Candidate D         9.4
Candidate E         8.9
Candidate F         7.5
Candidate G         6.8
...

Now a new question appears:

> How many retrieved candidates should be retained for each S1 query?



A simple approach would be to use a fixed Top-K value:

Top 50
Top 100
Top 500

However, this introduces an important limitation.


---

6. Why Fixed Top-K Is Not Ideal

Different business-name queries can produce very different BM25 score distributions.

Query A

100.0
98.7
97.5
96.9
20.2
19.7
...

Here, strong candidates are concentrated near the top.

Query B

15.4
14.9
14.7
14.5
14.2
13.9
13.5
...

Here, the scores are much more closely distributed.

Using:

Top 100

for both queries assumes that the same number of candidates is appropriate for every business.

That assumption is not necessarily valid.

Core Observation

> A fixed K is query-independent, while BM25 score distributions are query-dependent.



Therefore, instead of asking:

> "How many records should we always keep?"



we ask:

> "How much weaker than the strongest result are we willing to go?"



This leads to the idea of BM25 score deviation.


---

7. Key Idea: BM25 Score Deviation

For each S1 query, let the highest BM25 score be:

\[
S_{\max}
\]

For every retrieved candidate with score:

\[
S_i
\]

we calculate:

\[
\boxed{D_i = S_{\max} - S_i}
\]

We call \(D_i\) the BM25 Score Deviation.

Where:

\(S_{\max}\) = highest BM25 score for that query

\(S_i\) = BM25 score of candidate \(i\)

\(D_i\) = distance from the strongest result


Example

Suppose:

\[
S_{\max}=10.0
\]

and a candidate has:

\[
S_i=8.2
\]

Then:

\[
D_i=10.0-8.2=1.8
\]

The candidate is therefore 1.8 BM25 points below the strongest result.

Why This Helps

Instead of saying:

> "Always keep the top 100 records."



we can say:

> "Keep candidates whose BM25 scores are sufficiently close to the strongest result for that particular query."



This makes the cutoff query-relative rather than rank-relative.


---

8. Candidate Selection Rule

Let the selected deviation threshold be:

\[
BP
\]

A candidate is retained when:

\[
D_i \leq BP
\]

Since:

\[
D_i=S_{\max}-S_i
\]

we get:

\[
S_{\max}-S_i\leq BP
\]

Therefore:

\[
\boxed{S_i\geq S_{\max}-BP}
\]

This is our adaptive candidate-selection rule.

The critical question now becomes:

> What should BP be?



This is where the value 2.8 comes from.


---

9. Why BP = 2.8?

The value 2.8 was not manually selected.

Simply writing:

> "We selected BP = 2.8 using a knee-point algorithm."



would leave several important questions unanswered:

Why 2.8?

Why not 1.5?

Why not 5?

Why not 10?

Why not Top-500?

Was the value selected from one particular sample?

Does the value remain stable across different queries?


Therefore, the threshold was selected through an experimental, data-driven procedure.

Objective

We want a threshold that provides:

High candidate recall

while avoiding:

Unnecessary candidate expansion

This creates a trade-off between:

Candidate Space
       ↕
Ground-Truth Recall


---

10. Experimental Methodology

We sampled 1,000 S1 entities and examined their BM25 retrieval results.

For different deviation thresholds, we measured how many known matching records were successfully recovered.

The primary evaluation metric was:

Ground-Truth Recall

\[
Recall =
\frac{
\text{Number of known true matches recovered}
}{
\text{Total number of known true matches}
}
\]

The experiment therefore measures the relationship between:

Deviation Threshold
        |
        +------ Candidate Count
        |
        +------ Ground-Truth Recall

The purpose is to understand how candidate-set expansion affects the recovery of known true matches.


---

11. Threshold vs. Recall

The expected behavior is:

Small Deviation

Small threshold
      |
      v
Fewer candidates
      |
      v
Smaller search space
      |
      v
Some true matches may be missed
      |
      v
Lower recall

Larger Deviation

Larger threshold
      |
      v
More candidates
      |
      v
Larger search space
      |
      v
More true matches recovered
      |
      v
Higher recall

However, increasing the threshold indefinitely is not desirable.

Eventually:

> Increasing the deviation continues to add candidates while producing progressively smaller improvements in recall.



This creates a diminishing-return region.

Conceptually:

Recall
  |
  |                              ________
  |                         _____
  |                    _____
  |                ____
  |            ___
  |        ___
  |    ____
  |____
  +--------------------------------------> BM25 Deviation

The goal is therefore not simply to maximize recall by retrieving an extremely large candidate set.

Instead, we want to identify the region where:

> Useful recall improvement begins to diminish relative to the additional candidate search space.




---

12. Knee-Point Detection

To make threshold selection data-driven, we identify the knee point of the recall curve.

The knee represents the region where the curve changes from relatively rapid improvement to comparatively slower improvement.

Rather than selecting the knee visually, we use a geometric approach.

Imagine drawing a straight line between the beginning and ending points of the recall curve.

For every deviation value, calculate the distance between the actual recall curve and this reference line.

Conceptually:

Recall
  |
  |                         *
  |                     *
  |                 *
  |             *
  |         *
  |      *
  |   *
  | *
  +-------------------------------------> Deviation
    \___________________________________
              Reference Line

The threshold with the maximum distance from the reference line is treated as the knee point.

Why This Matters

This gives us a:

Reproducible

Data-driven

Non-arbitrary


method for selecting the cutoff.

We are not simply looking at the curve and choosing a convenient number.


---

13. Why Use the Knee Point?

There are two undesirable extremes.

Too Small a Threshold

Small candidate set
        |
        v
Lower computational cost
        |
        v
Potentially lower recall

Too Large a Threshold

Large candidate set
        |
        v
Higher recall
        |
        v
More unnecessary candidates
        |
        v
Higher downstream computation

The knee provides an operating point where:

> Further increasing the candidate space begins to provide diminishing recall improvement.



Therefore, the knee is used as an evidence-based initial cutoff.


---

14. Stability Experiment

A threshold obtained from a single sample could be specific to that particular sample.

To test whether the result is stable, we repeated the experiment using five independent samples.

The observed results were:

Experiment	Knee Deviation	Recall

1	2.8	89.62%
2	3.1	91.94%
3	2.8	89.75%
4	2.9	89.81%
5	2.8	89.80%


The detected knee remained within:

\[
\boxed{2.8 \leq BP \leq 3.1}
\]

The median knee deviation was:

\[
\boxed{2.8}
\]

Interpretation

The result was not based on a single random sample.

Across five independent experiments, the detected knee remained in a relatively narrow range.

This provides evidence that the observed cutoff is not simply an artifact of one particular sample.


---

15. Decision: BP = 2.8

Based on the repeated experiments:

Knee values remained between 2.8 and 3.1

The median knee was 2.8

The behavior remained reasonably stable across independent samples


Therefore:

\[
\boxed{BP=2.8}
\]

is selected as the initial name-based candidate-generation deviation.

The final candidate-selection rule becomes:

\[
\boxed{D_i\leq2.8}
\]

or equivalently:

\[
\boxed{S_i\geq S_{\max}-2.8}
\]

In Plain Language

> For each S1 business, retain S2/S3 candidates whose BM25 score is no more than 2.8 below that query's strongest BM25 score.




---

16. Important Interpretation of BP = 2.8

The value 2.8 should not be interpreted as a universal BM25 constant.

It is a dataset-driven operating threshold obtained from the observed ground-truth recall behavior of the current data and BM25 configuration.

If the following change substantially:

Dataset

Data distribution

Text preprocessing

Tokenization

BM25 configuration

Ground-truth definition


then the threshold should be re-evaluated using the same experimental procedure.

Therefore:

> BP = 2.8 is an evidence-based parameter for this candidate-generation setup, not a universal constant.




---

17. Important: BM25 Is Not the Final Matcher

This distinction is critical.

BM25 measures lexical similarity between business names.

A genuine match can have weak name similarity but strong similarity in another attribute.

For example:

Name similarity
      |
      v
    Weak

Address similarity
      |
      v
   Strong

The opposite situation can also occur.

Two unrelated businesses may have highly similar names:

ABC Restaurant
ABC Restaurant

but completely different addresses.

Therefore:

> Name similarity alone cannot establish entity identity.



The BM25 stage is intentionally limited to candidate generation.


---

18. Multi-Attribute Candidate Generation

The name-based candidate set is only one source of candidates.

Additional blocking strategies can generate candidates using:

Address

Country

Location

Other available business attributes


The candidate sets are then combined.

S1 Business
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        Name Blocking   Address Blocking   Other
           (BM25)            (...)        Attributes
              |               |               |
              v               v               v
        Name Candidates  Address Candidates  Other
              |               |               |
              +---------------+---------------+
                              |
                              v
                    UNION OF CANDIDATES
                              |
                              v
                    Final Pairwise Matching
                              |
                              v
                    Multi-Attribute Model

This union strategy is important because a genuine match that is weak in name similarity may still be recovered through another attribute.


---

19. Complete Methodology Chain

The complete reasoning is:

Millions of S2/S3 records
          |
          v
Cannot compare every possible pair
          |
          v
Need candidate generation
          |
          v
Business name is useful but noisy
          |
          v
Exact matching is insufficient
          |
          v
Use BM25 for lexical retrieval
          |
          v
BM25 produces ranked candidates
          |
          v
But how many candidates should we keep?
          |
          v
Fixed K is query-independent
          |
          v
Different queries have different BM25 score distributions
          |
          v
Use score deviation from each query's best result
          |
          v
D_i = S_max - S_i
          |
          v
Measure ground-truth recall at different deviations
          |
          v
Small deviation -> fewer candidates -> lower recall
          |
          v
Large deviation -> more candidates -> higher recall
          |
          v
Recall gains eventually diminish
          |
          v
Find the mathematical knee
          |
          v
Repeat on 5 independent samples
          |
          v
Knee consistently approximately 2.8-3.1
          |
          v
Median knee = 2.8
          |
          v
Choose BP = 2.8
          |
          v
S_i >= S_max - 2.8
          |
          v
Generate name-based candidates
          |
          v
UNION with address / other candidates
          |
          v
Final pairwise refinement


---

20. Why Each Design Decision Was Made

Design Decision	Reason

Candidate generation	Full pairwise comparison is computationally expensive
Business names	Strong identifying attribute
BM25	Handles lexical and token-level similarity
No exact matching alone	Business names contain real-world noise
No fixed Top-K	Queries have different score distributions
Score deviation	Provides a query-relative cutoff
Ground-truth recall	Measures actual match recovery
Recall curve	Shows threshold versus retrieval performance
Knee detection	Identifies the diminishing-return region
Five experiments	Tests threshold stability
BP = 2.8	Median of the observed knee values
Multiple blocking methods	Protects against weak name similarity
Final pairwise matching	Uses richer evidence to determine identity



---

21. Computational Perspective

Without candidate generation, the potential comparison space is approximately:

\[
|S1|\times(|S2|+|S3|)
\]

For large datasets, this can result in an extremely large number of pairwise comparisons.

Candidate generation changes the workflow from:

S1
 |
 +---- Millions of possible comparisons
 |
 +---- Millions of possible comparisons

to:

S1
 |
 v
Candidate Generation
 |
 v
Smaller set of plausible candidates
 |
 v
Detailed Pairwise Matching

The candidate-generation stage therefore attempts to balance three objectives:

Recall

Retain genuine matching records.

Candidate Volume

Avoid generating an unnecessarily large candidate set.

Computational Efficiency

Reduce the amount of work required by the downstream matching stage.


---

22. Reproducibility

To make the selection of BP = 2.8 independently verifiable, the experiment should record:

Dataset/version

Number of sampled S1 entities

Sampling procedure

Random seeds, where applicable

BM25 implementation

BM25 configuration

Text preprocessing

Tokenization method

Candidate retrieval depth

Tested deviation thresholds

Ground-truth definition

Recall calculation

Knee-point calculation method

Results from each independent experiment

Final selected threshold


This ensures that 2.8 is reproducible rather than appearing to be a manually chosen constant.


---

23. Final Candidate-Generation Procedure

For every S1 business:

Step 1 — Retrieve

Run BM25 over S2/S3 business names.

Step 2 — Find the strongest result

\[
S_{\max}
\]

Step 3 — Calculate deviation

\[
D_i=S_{\max}-S_i
\]

Step 4 — Apply the cutoff

\[
\boxed{D_i\leq2.8}
\]

or: