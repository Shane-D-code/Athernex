# Property-Based Tests

This directory contains property-based tests using the [Hypothesis](https://hypothesis.readthedocs.io/) framework. Property-based tests validate universal correctness properties that should hold for all valid inputs, rather than testing specific examples.

## Test Files

### test_confidence_bounds.py

**Property 1: Confidence Score Bounds**

Validates Requirements:
- **1.5**: STT confidence scores between 0.0 and 1.0
- **2.7**: LLM clarity scores between 0.0 and 1.0  
- **3.5**: Combined confidence scores between 0.0 and 1.0

#### Test Cases

1. **test_confidence_scores_within_bounds** (Property 1a)
   - Validates all confidence scores remain in [0.0, 1.0]
   - Tests 100 random combinations of STT/LLM scores, penalties, and intents

2. **test_combined_score_never_exceeds_bounds_after_penalties** (Property 1b)
   - Validates combined scores stay in bounds after applying penalties
   - Ensures penalties properly clamp scores to 0.0 minimum

3. **test_analyzer_handles_invalid_input_gracefully** (Property 1c)
   - Tests robustness with out-of-bounds inputs (-2.0 to 2.0)
   - Validates defensive programming and input clamping

4. **test_maximum_penalty_scenario** (Property 1d)
   - Tests extreme case with 10 low-confidence words + 4 missing fields
   - Ensures score remains valid even with maximum penalties

5. **test_perfect_confidence_no_penalties** (Property 1e)
   - Validates perfect confidence (1.0) stays at 1.0 with no penalties
   - Tests all intent types

6. **test_zero_confidence_stays_at_zero** (Property 1f)
   - Validates zero confidence (0.0) stays at 0.0 with no penalties
   - Ensures clarification is always triggered

7. **test_confidence_analyzer_weights_sum_to_one** (Property 1g)
   - Validates STT and LLM weights sum to 1.0
   - Ensures normalized weighted combination

8. **test_combined_score_calculation_examples** (Property 1h)
   - Validates specific examples of weighted combination formula
   - Tests edge cases: (1.0, 1.0), (0.5, 0.5), (0.0, 1.0), (1.0, 0.0)

### test_semantic_equivalence.py

**Property 5: Semantic Equivalence**

Validates Requirements:
- **12.5**: Semantic equivalence across different phrasings
- **2.3**: Structured data extraction consistency

#### Test Cases

1. **test_identity_is_semantically_equivalent** (Property 5a)
   - Validates reflexive property: an order is equivalent to itself
   - Tests 100 random order configurations

2. **test_semantic_equivalence_is_symmetric** (Property 5b)
   - Validates symmetric property: if A ≡ B, then B ≡ A
   - Tests with random order pairs

3. **test_reordered_items_are_semantically_equivalent** (Property 5c)
   - Validates item order invariance
   - "pizza and burger" ≡ "burger and pizza"

4. **test_confidence_variation_preserves_semantic_equivalence** (Property 5d)
   - Validates confidence invariance
   - Same order with different confidence scores are equivalent

5. **test_case_insensitive_item_names** (Property 5e)
   - Validates case insensitivity
   - "Pizza" ≡ "pizza" ≡ "PIZZA"

6. **test_paraphrased_utterances_produce_equivalent_orders** (Property 5f - Integration)
   - Validates paraphrase equivalence with actual LLM
   - Requires running Ollama instance
   - Tests English, Hindi, and code-mixed variations

7. **test_multiple_variations_produce_equivalent_orders** (Property 5g - Integration)
   - Validates multiple variations all produce equivalent results
   - Requires running Ollama instance

## Running the Tests

```bash
# Run all property tests
pytest tests/property/ -v

# Run with statistics
pytest tests/property/ -v --hypothesis-show-statistics

# Run with more examples (default is 100)
pytest tests/property/ -v --hypothesis-max-examples=1000

# Run specific test file
pytest tests/property/test_confidence_bounds.py -v
```

## Understanding Property-Based Testing

Property-based tests differ from traditional example-based tests:

**Example-Based Test:**
```python
def test_add():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
```

**Property-Based Test:**
```python
@given(st.integers(), st.integers())
def test_add_commutative(a, b):
    assert add(a, b) == add(b, a)  # Property: addition is commutative
```

Property-based tests:
- Generate hundreds of random test cases automatically
- Find edge cases you might not think of
- Validate universal properties that should always hold
- Provide better coverage with less code

## Adding New Property Tests

When adding new property tests:

1. Identify a universal property that should always hold
2. Use `@given` decorator with appropriate strategies
3. Write clear assertions that validate the property
4. Document which requirements the property validates
5. Add the test to this README

### Example Template

```python
from hypothesis import given, strategies as st

@given(
    param1=st.floats(min_value=0.0, max_value=1.0),
    param2=st.integers(min_value=0, max_value=100)
)
def test_my_property(param1: float, param2: int):
    """
    Property X: Description of the property.
    
    Validates:
    - Requirement X.Y: Description
    """
    # Arrange
    system_under_test = MyClass()
    
    # Act
    result = system_under_test.method(param1, param2)
    
    # Assert
    assert result >= 0.0, "Result must be non-negative"
```

## Hypothesis Strategies

Common strategies used in these tests:

- `st.floats(min_value=0.0, max_value=1.0)` - Confidence scores
- `st.integers(min_value=0, max_value=10)` - Counts
- `st.lists(st.text())` - Lists of strings
- `st.sampled_from([...])` - Enum values
- `st.just(value)` - Fixed value

See [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/data.html) for more strategies.
