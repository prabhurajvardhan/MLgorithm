
# Amazon ML Challenge 2026
# Business Entity Resolution

## 1. Problem Understanding

The task is to identify which records from Source 2 and Source 3 belong to the same real-world business as each record in Source 1.

The three sources do not share a common business ID. The records can also contain noisy information such as different business name formats, abbreviations, spelling mistakes, address variations and missing information.

One Source 1 business can have zero, one or multiple matching records in Source 2 and Source 3.

Our main objective is therefore not just finding similar strings. The objective is to decide whether two complete business records represent the same entity.

The final evaluation uses F0.5, which gives more importance to precision than recall. Because of this, making an incorrect merge between two different businesses is an important error for our system.


## 2. Overall Approach

We divided the solution into separate stages so that each stage has one clear responsibility.

Raw Data
    |
    v
P1 - Data Profiling and Normalization
    |
    v
P2 - Candidate Generation / Blocking
    |
    v
Candidate Pairs
    |
    v
P3 - Pair Feature Extraction
    |
    v
XGBoost Matching Model
    |
    v
Match Probability
    |
    v
Threshold Decision
    |
    v
Final Matching Results


### P1 - Data Profiling and Normalization

P1 studies the structure and quality of the three sources and prepares reusable text normalization.

The purpose is not to decide whether two businesses match. It prepares the data so that later stages can compare records more reliably.

Typical checks include missing values, duplicate IDs, text patterns, country values and common variations in names and addresses.


### P2 - Candidate Generation

Comparing every Source 1 record with every Source 2 and Source 3 record would create a very large number of comparisons.

P2 therefore reduces the search space and creates a candidate set.

The important point is that blocking is only used to decide which records are worth comparing. It does not make the final match decision.

We plan to use multiple candidate-generation signals and combine their results. This gives the candidate stage more opportunities to retrieve a true match.


### P3 - Matching Model

P3 receives the final candidate pairs from P2.

For every candidate pair, we compare the corresponding fields:

    Source 1 business_name <-> Source 2/3 business_name
    Source 1 business_address <-> Source 2/3 business_address
    Source 1 country <-> Source 2/3 country

These comparisons are converted into numerical features.

The features are then given to an XGBoost classifier, which predicts the probability that the two records represent the same business.

Finally, a probability threshold is applied to produce the final matches.


## 3. Candidate Generation / Blocking

Candidate generation is important because the matching model can only select a true match if that record is present in the candidate set.

For this reason, we treat candidate generation as a recall-sensitive stage.

The planned strategy is to use more than one blocking signal and take the union of the candidates.

For example:

    Name based candidates
             +
    Address based candidates
             +
    Other useful blocking signals
             |
             v
       Candidate Union
             |
             v
       Final Candidate Set


This is preferable to depending on only one blocking rule. A true match may fail one blocking rule because of a typo or address variation but may still be retrieved by another rule.

The candidate_pairs.tsv submitted with the final solution will contain the final candidate set actually passed to the matching model.


## 4. Feature Engineering

For every candidate pair we currently generate several simple similarity features.

### Business Name Features

1. Jaccard similarity
2. Levenshtein similarity
3. Token-sort similarity
4. Exact match


### Business Address Features

1. Jaccard similarity
2. Levenshtein similarity
3. Token-sort similarity
4. Exact match


### Country Feature

1. Country exact match


The current baseline therefore produces 9 numerical features for every candidate pair.


## 5. Why Multiple Similarity Measures?

We did not want to depend on a single similarity calculation.

Different similarity methods see different types of similarity.

For example:

    "ABC Technologies Pvt Ltd"
    "ABC Technology Private Limited"

A character-based method can capture the overall spelling similarity, while token-based methods can capture the common words.

Similarly, word order can change between records. A token-sort comparison can reduce the effect of word ordering.

Jaccard is useful for measuring overlap between sets of words.

Levenshtein-based similarity is useful for character-level changes such as spelling differences and small edits.

Exact matching is also retained because an exact match is a strong signal when it occurs.

The idea is not that one feature should solve the matching problem.

Instead, each feature gives the model another piece of information.


## 6. Why Jaccard and Levenshtein?

We selected these as simple baseline similarity measures because they capture two different types of similarity.

Jaccard works at the token level.

Levenshtein works at the character level.

This difference is useful because business names and addresses can change in different ways.

For example, abbreviations and word changes may affect token overlap, while spelling mistakes may still produce a high character-level similarity.

We also use token-sort similarity because two records can contain similar words in a different order.


## 7. Why Not Use Only One Similarity Score?

A single similarity score can hide important information.

Consider:

    Record A:
    Ocean View Restaurant
    Beach Road Chennai

    Record B:
    Ocean View Restaurant
    Beach Road Kochi

The business names are identical, but the addresses are different.

Another case can be the opposite:

    Same address
    Different business name

Therefore, the model receives separate name and address features instead of one combined similarity score.

This allows the model to learn how different signals work together.


## 8. TF-IDF and Other Similarity Methods

TF-IDF cosine similarity is one of the methods suggested in the challenge description and is a useful candidate for experimentation.

We have intentionally kept the first baseline small instead of adding every possible similarity method immediately.

The reason is simple: we first want to establish a working baseline and understand the contribution of each feature.

The next validation experiments can compare the current features with TF-IDF cosine similarity and other useful features.

A feature will be retained only if it provides useful validation results without adding unnecessary complexity.

This also keeps the final pipeline easier to reproduce and explain.


## 9. Why XGBoost?

We are treating entity matching as a binary classification problem.

For every candidate pair:

    1 = same business
    0 = different business


After feature extraction, the problem becomes a small tabular classification problem.

XGBoost was selected as the first model because it can work directly with numerical feature values and can learn non-linear relationships between them.

For example, the model can learn that:

    high name similarity
    +
    high address similarity

is stronger evidence than either signal alone.

It can also learn that a high address similarity by itself should not automatically mean that two businesses are the same.

We considered the matching problem more suitable for a compact tabular model than using a large language model or a large neural network for the first baseline.

This keeps training and inference simpler and makes the effect of the engineered features easier to study.

We are not assuming XGBoost is automatically the final model. Other models can be tested on the validation set and compared using F0.5.


## 10. Training Labels

The training ground truth contains the true matching IDs for every Source 1 entity.

For each candidate pair generated by P2:

    If candidate_entity_id exists in the ground-truth
    matches for that Source 1 entity:

        label = 1

    Otherwise:

        label = 0


This gives the matching model positive examples and negative examples.

Importantly, the negative examples come from the candidate generation stage rather than random records from the entire database.

These are more useful because they are records that already looked somewhat plausible during candidate generation.


## 11. Why Candidate-Based Negative Examples?

A random record from another business is usually very easy to reject.

For example:

    "ABC Technologies"
    vs
    "Green Valley Hospital"

A model does not learn much from such an obvious negative.

A candidate such as:

    Same business name
    Different address

or:

    Same address
    Different business name

is much harder.

These hard negatives are more useful for teaching the matching model where the boundary between match and non-match exists.


## 12. Decision Threshold

The XGBoost model produces a probability for each candidate pair.

For example:

    S1-001 -> S2-001 -> 0.91
    S1-001 -> S2-002 -> 0.32

The probability itself is not the final submission.

A threshold is applied:

    probability >= threshold
            |
            v
          match

    probability < threshold
            |
            v
        no match


The value 0.5 is currently used only for testing the mock pipeline.

For the real solution, the threshold will be selected using a validation split and the F0.5 metric.


## 13. Evaluation Strategy

The test set does not contain ground-truth labels.

Therefore, we cannot directly calculate F0.5 on the test data.

Instead, we will create a validation split from the training data.

The validation process will be:

    Training data
         |
         +---- Training split
         |
         +---- Validation split

The model is trained only on the training split.

Predictions are then generated for the validation split.

Different thresholds can be tested and F0.5 can be calculated for each threshold.

The threshold producing the strongest validation result will then be considered for test inference.


## 14. F0.5

The challenge uses:

    F0.5 = (1.25 × Precision × Recall)
           / (0.25 × Precision + Recall)


The score is calculated separately for every Source 1 entity and then macro-averaged.

This is important because the number of matches can be different for different Source 1 entities.

Entities with no true matches are also included in the evaluation.

Therefore, our model must not assume that every Source 1 record has at least one match.


## 15. Current Mock Experiment

Before using the complete dataset, we built a small mock dataset to verify the complete P3 pipeline.

The mock experiment contained:

    5 Source 1 records
    7 Source 2 records
    6 Source 3 records
    16 candidate pairs

The pipeline successfully performed:

    Candidate pair
        ->
    Feature extraction
        ->
    Ground-truth label creation
        ->
    XGBoost training
        ->
    Match probability
        ->
    Threshold decision
        ->
    matching_results.tsv


Using a temporary threshold of 0.5, the mock dataset produced:

    Macro F0.5 = 1.0


This result is only a pipeline verification result. It should not be treated as an estimate of performance on the real dataset because the mock dataset is very small.


## 16. Error Cases Considered

We specifically included difficult examples in the mock data.

For example:

    Same address + different business name

and:

    Same business name + different address


These cases are important because a single attribute can be misleading.

The matching model therefore receives name and address evidence separately instead of treating one field as sufficient proof of identity.


## 17. Reasoning Behind the Overall Design

The main design decision was to separate candidate generation from matching.

If we tried to compare every record with every other record, the number of comparisons would become extremely large.

Blocking solves the search-space problem.

However, blocking alone cannot make the final identity decision.

Therefore:

    P2 asks:
    "Which records are worth comparing?"

    P3 asks:
    "After comparing them, which ones are actually the same business?"


We also separated feature extraction from the ML model.

This allows us to add or remove similarity features without changing the whole pipeline.

The model is therefore not responsible for understanding raw strings directly. It receives structured evidence from the name, address and country fields.


## 18. Planned Experiments

The first baseline is intentionally simple.

The next experiments will investigate:

1. Different probability thresholds.
2. TF-IDF cosine similarity.
3. Additional name and address features.
4. Different XGBoost parameter settings.
5. Different blocking strategies.
6. Hard-negative selection.
7. Handling of missing fields.
8. Country-specific address patterns.
9. Singleton/no-match behaviour.

Each experiment will be recorded with its configuration and validation F0.5 so that the final model is based on measured results rather than assumptions.


## 19. Reproducibility

The solution is being developed as separate modules.

The code contains separate components for:

    Data preparation
    Feature extraction
    Training
    Prediction
    Decision making
    Evaluation


Large datasets and generated artifacts are kept outside the source-code files, while the processing logic remains reproducible from code.

The final submission will contain the required output files, source code, dependencies and methodology document.


## 20. Conclusion

The current work establishes a complete baseline entity-resolution pipeline.

The important part of the approach is not relying on one similarity score.

Instead, the system combines several simple signals and lets a supervised model learn how those signals relate to true and false matches.

The next stage is to run the same pipeline on a proper validation split from the provided training data, measure F0.5, test thresholds and feature variations, and then move to inference on the test data.

All experiments and final decisions will be recorded so that the final submission can be reproduced and explained.
