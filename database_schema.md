## **Database Schema**

### 1. **User Database**

- **Key**: `user:<pseudonym>`

  - `false_positives`: int
    - **Set**: `update_user_performance(pseudonym, Field.FALSE_POSITIVES, value)`
    - **Get**: `get_user_performance_value(pseudonym, Field.FALSE_POSITIVES)`

  - `false_negatives`: int
    - **Set**: `update_user_performance(pseudonym, Field.FALSE_NEGATIVES, value)`
    - **Get**: `get_user_performance_value(pseudonym, Field.FALSE_NEGATIVES)`

  - `true_positives`: int
    - **Set**: `update_user_performance(pseudonym, Field.TRUE_POSITIVES, value)`
    - **Get**: `get_user_performance_value(pseudonym, Field.TRUE_POSITIVES)`

  - `true_negatives`: int
    - **Set**: `update_user_performance(pseudonym, Field.TRUE_NEGATIVES, value)`
    - **Get**: `get_user_performance_value(pseudonym, Field.TRUE_NEGATIVES)`

  - `from_snippet_id`: int
    - (Interacted with via the snippet-handling functions)
  
  - `to_snippet_id`: int
    - (Interacted with via the snippet-handling functions)
  
  - `seed`: int
    - (Interacted with via the snippet-handling functions)

### 2. **Snippet Database**

1. **Snippet Entries**:
   - **Key**: `snippet:<snippet_id>`
   - **Values**:
     - `text`: The actual snippet of text.
     - `source`: The source of the snippet (e.g., a URL or a reference).
     - `is_bot`: A boolean indicating if the text was AI-generated.
   - **Function Interaction**: `set_snippet()`, `get_snippet()`

2. **Snippet Hashes** (to prevent duplicates):
   - **Key**: `snippet_hashes`
   - **Value**: SHA256 hash of the text snippet.
   - **Function Interaction**: `set_snippet()`

3. **Snippet ID Counter**:
   - **Key**: `snippet_id_counter`
   - **Value**: A counter incremented for each new snippet.
   - **Function Interaction**: `set_snippet()`

### 3. **Marker Database**

- **Key**: `marker:<marker_name>`

  - `true_positive_count`: int
    - **Set**: `update_marker(marker_name, Field.TRUE_POSITIVES, value)`
    - **Get**: `get_marker_value(marker_name, Field.TRUE_POSITIVES)`

  - `false_positive_count`: int
    - **Set**: `update_marker(marker_name, Field.FALSE_POSITIVES, value)`
    - **Get**: `get_marker_value(marker_name, Field.FALSE_POSITIVES)`

  - `true_negative_count`: int
    - **Set**: `update_marker(marker_name, Field.TRUE_NEGATIVES, value)`
    - **Get**: `get_marker_value(marker_name, Field.TRUE_NEGATIVES)`

  - `false_negative_count`: int
    - **Set**: `update_marker(marker_name, Field.FALSE_NEGATIVES, value)`
    - **Get**: `get_marker_value(marker_name, Field.FALSE_NEGATIVES)`


## **Functions and their Associated Database Entries**

1. **`update_user_performance(pseudonym, Field, value)`**:
   - `user:<pseudonym>.false_positives`
   - `user:<pseudonym>.false_negatives`
   - `user:<pseudonym>.true_positives`
   - `user:<pseudonym>.true_negatives`

2. **`get_user_performance_value(pseudonym, Field)`**:
   - `user:<pseudonym>.false_positives`
   - `user:<pseudonym>.false_negatives`
   - `user:<pseudonym>.true_positives`
   - `user:<pseudonym>.true_negatives`

3. **`set_snippet(snippet_id, text, source, is_bot)`**:
   - `snippet:<snippet_id>.text`
   - `snippet:<snippet_id>.source`
   - `snippet:<snippet_id>.is_bot`
   - `snippet_hashes`
   - `snippet_id_counter`

4. **`get_snippet(snippet_id)`**:
   - `snippet:<snippet_id>.text`
   - `snippet:<snippet_id>.source`
   - `snippet:<snippet_id>.is_bot`

5. **`update_marker(marker_name, Field, value)`**:
   - `marker:<marker_name>.true_positive_count`
   - `marker:<marker_name>.false_positive_count`
   - `marker:<marker_name>.true_negative_count`
   - `marker:<marker_name>.false_negative_count`

6. **`get_marker_value(marker_name, Field)`**:
   - `marker:<marker_name>.true_positive_count`
   - `marker:<marker_name>.false_positive_count`
   - `marker:<marker_name>.true_negative_count`
   - `marker:<marker_name>.false_negative_count`