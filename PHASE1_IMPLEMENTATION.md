# Phase 1 Implementation: Real LLM Code Translation

This document provides **concrete implementation steps** to integrate real LLM-powered code translation into the framework.

---

## Current Problem

**File:** `generation/generate_code.py`

**Current Code (Mocked):**
```python
def generate_kmp_code(project_path, delegate_task=None):
    # ...
    for file_path in files_to_migrate:
        with open(file_path, 'r') as f:
            file_content = f.read()
        
        generator_goal = f"""
        Migrate this Android code to KMP:
        
        FILE: {file_path}
        CODE:
        {file_content}
        """
        
        # MOCK - doesn't actually call LLM
        generated_code = delegate_task(goal=generator_goal)
        
        # Save migrated code
        save_migrated_file(file_path, generated_code)
```

**Problem:** `delegate_task` is a mock function that returns placeholder text.

---

## Solution: Real LLM Integration

### Step 1: Update generate_code.py

**File:** `generation/generate_code.py`

**Changes:**
```python
import json
from llm import get_enhanced_invoker, LLMResponse

def generate_kmp_code(project_path, delegate_task=None, use_real_llm=True):
    """
    Generate KMP code from Android project.
    
    Args:
        project_path: Path to Android project
        delegate_task: Optional LLM invoker (backward compatibility)
        use_real_llm: If True, use real LLM. If False, use mock.
    """
    framework_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    skills = load_skills(framework_path)
    
    # Load SPEC.md
    spec_path = os.path.join(project_path, "SPEC.md")
    with open(spec_path, 'r') as f:
        spec_content = f.read()
    
    # Initialize LLM if needed
    invoker = None
    if use_real_llm:
        if delegate_task and hasattr(delegate_task, 'invoke'):
            invoker = delegate_task
        else:
            # Try to get default invoker
            try:
                invoker = get_enhanced_invoker('ollama', 'qwen2.5-coder:7b')
                # Test connection
                test_response = invoker.invoke("Reply OK", system_prompt="Test")
                if test_response.error:
                    print(f"⚠ LLM not available: {test_response.error}")
                    print("  Falling back to mock mode")
                    invoker = None
            except Exception as e:
                print(f"⚠ LLM initialization failed: {e}")
                print("  Falling back to mock mode")
                invoker = None
    
    # Process files in batches
    modules_to_migrate = extract_modules_from_spec(spec_content)
    
    for module in modules_to_migrate:
        module_path = os.path.join(project_path, module)
        files = collect_kotlin_files(module_path)
        
        # Group by type for batch processing
        batches = group_files_by_type(files)
        
        for batch_name, batch_files in batches.items():
            print(f"\n--- Migrating {batch_name} ({len(batch_files)} files) ---")
            
            if invoker and use_real_llm:
                # REAL LLM MODE
                results = migrate_batch_with_llm(
                    invoker=invoker,
                    files=batch_files,
                    batch_name=batch_name,
                    skills=skills,
                    project_path=project_path
                )
            else:
                # MOCK MODE (fallback)
                results = migrate_batch_mock(
                    files=batch_files,
                    batch_name=batch_name
                )
            
            # Save results
            for result in results:
                if result.success:
                    save_migrated_file(
                        original_path=result.original_path,
                        migrated_code=result.migrated_code,
                        target_module=result.target_module,
                        project_path=project_path
                    )
                    print(f"  ✓ {os.path.basename(result.original_path)}")
                else:
                    print(f"  ✗ {os.path.basename(result.original_path)}: {result.error}")
    
    print(f"\n✓ Batch migration complete")


@dataclass
class MigrationResult:
    """Result of migrating a single file."""
    original_path: str
    migrated_code: str
    target_module: str
    success: bool
    error: Optional[str] = None
    tokens_used: int = 0
    latency_ms: int = 0


def migrate_batch_with_llm(
    invoker,
    files: List[str],
    batch_name: str,
    skills: Dict,
    project_path: str
) -> List[MigrationResult]:
    """
    Migrate a batch of files using real LLM.
    
    Args:
        invoker: LLM invoker instance
        files: List of file paths to migrate
        batch_name: Name of this batch (e.g., "ViewModel")
        skills: Available skills for this migration
        project_path: Path to project
    
    Returns:
        List of MigrationResult objects
    """
    results = []
    
    for file_path in files:
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_code = f.read()
            
            # Detect applicable skills
            applicable_skills = detect_applicable_skills(original_code, skills)
            
            # Build prompt
            prompt = build_migration_prompt(
                file_path=file_path,
                original_code=original_code,
                batch_name=batch_name,
                applicable_skills=applicable_skills
            )
            
            # Call LLM with JSON mode for structured output
            response = invoker.invoke(
                prompt=prompt,
                system_prompt="You are an expert KMP developer. Migrate Android code to Kotlin Multiplatform.",
                json_mode=True,  # Expect JSON response
                max_tokens=4096
            )
            
            if response.error:
                results.append(MigrationResult(
                    original_path=file_path,
                    migrated_code="",
                    target_module="shared/src/commonMain/kotlin",
                    success=False,
                    error=response.error
                ))
                continue
            
            # Parse LLM response
            migration_data = parse_llm_response(response.content)
            
            # Validate migrated code
            validation = validate_kotlin_code(migration_data['code'])
            
            if not validation.valid:
                results.append(MigrationResult(
                    original_path=file_path,
                    migrated_code="",
                    target_module="shared/src/commonMain/kotlin",
                    success=False,
                    error=f"Invalid Kotlin: {validation.errors}"
                ))
                continue
            
            # Success!
            results.append(MigrationResult(
                original_path=file_path,
                migrated_code=migration_data['code'],
                target_module=migration_data.get('target_module', 'shared/src/commonMain/kotlin'),
                success=True,
                tokens_used=response.tokens_used or 0,
                latency_ms=response.latency_ms or 0
            ))
            
        except Exception as e:
            results.append(MigrationResult(
                original_path=file_path,
                migrated_code="",
                target_module="shared/src/commonMain/kotlin",
                success=False,
                error=str(e)
            ))
    
    return results


def build_migration_prompt(
    file_path: str,
    original_code: str,
    batch_name: str,
    applicable_skills: List[Dict]
) -> str:
    """
    Build prompt for LLM code migration.
    
    Returns a structured prompt that guides the LLM to produce valid KMP code.
    """
    prompt = f"""You are an expert Kotlin Multiplatform developer. Migrate the following Android code to KMP.

## File Information
- **Path:** {file_path}
- **Type:** {batch_name}
- **Target:** shared/src/commonMain/kotlin (unless platform-specific)

## Original Android Code
```kotlin
{original_code}
```

## Migration Guidelines

1. **Shared Code**: Place business logic in commonMain
2. **Platform Code**: Use expect/actual for platform-specific code
3. **Dependencies**: Use KMP-compatible libraries
4. **Naming**: Keep class/function names consistent
5. **Comments**: Preserve important comments

## Applicable Skills
"""
    
    for skill in applicable_skills:
        prompt += f"""
### {skill['name']}
- **Android:** {skill.get('android_dependency', 'N/A')}
- **KMP:** {skill.get('kmp_dependency', 'N/A')}
- **Guide:** {skill.get('migration_guide', '')[:200]}
"""
    
    prompt += """

## Output Format

Respond with JSON in this exact format:
```json
{
  "code": "// Your migrated KMP code here",
  "target_module": "shared/src/commonMain/kotlin",
  "changes_made": ["List of major changes"],
  "platform_specific": false,
  "notes": "Any important notes"
}
```

**IMPORTANT:** Return ONLY the JSON, no other text.
"""
    
    return prompt


def parse_llm_response(content: str) -> Dict:
    """
    Parse LLM response to extract migrated code.
    
    Handles various response formats and extracts the code.
    """
    try:
        # Try to parse as JSON
        data = json.loads(content)
        
        if 'code' in data:
            return {
                'code': data['code'],
                'target_module': data.get('target_module', 'shared/src/commonMain/kotlin'),
                'changes': data.get('changes_made', []),
                'notes': data.get('notes', '')
            }
        
        # Fallback: treat entire content as code
        return {
            'code': content,
            'target_module': 'shared/src/commonMain/kotlin',
            'changes': [],
            'notes': ''
        }
        
    except json.JSONDecodeError:
        # Not JSON, extract code from markdown blocks
        code_blocks = re.findall(r'```kotlin\s*([\s\S]*?)```', content)
        
        if code_blocks:
            return {
                'code': code_blocks[0].strip(),
                'target_module': 'shared/src/commonMain/kotlin',
                'changes': [],
                'notes': ''
            }
        
        # Last resort: return entire content
        return {
            'code': content.strip(),
            'target_module': 'shared/src/commonMain/kotlin',
            'changes': [],
            'notes': ''
        }


@dataclass
class KotlinValidation:
    """Result of Kotlin code validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def validate_kotlin_code(code: str) -> KotlinValidation:
    """
    Validate migrated Kotlin code.
    
    Checks for:
    - Syntax errors (basic)
    - Missing imports
    - Common KMP patterns
    """
    errors = []
    warnings = []
    
    # Basic syntax checks
    if not code.strip():
        errors.append("Empty code")
    
    # Check for common issues
    if 'TODO' in code or 'FIXME' in code:
        warnings.append("Contains TODO/FIXME comments")
    
    # Check for Android-specific imports that should be migrated
    android_imports = [
        'androidx.appcompat',
        'androidx.lifecycle.ViewModel',
        'android.arch.lifecycle',
    ]
    
    for imp in android_imports:
        if imp in code:
            warnings.append(f"Contains Android-specific import: {imp}")
    
    # Check for basic Kotlin syntax
    if 'public class' in code and 'class' not in code.split('public class')[1].split('\n')[0]:
        # This is a very basic check, real validation would use a Kotlin parser
        pass
    
    return KotlinValidation(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def migrate_batch_mock(files: List[str], batch_name: str) -> List[MigrationResult]:
    """
    Mock migration for testing/fallback.
    
    Returns placeholder code instead of real migration.
    """
    results = []
    
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_code = f.read()
        
        # Generate mock migrated code
        mock_code = f"""// MOCK MIGRATION - Configure LLM for real migration
// Original file: {file_path}
// Batch: {batch_name}

package com.example.migrated

// TODO: Implement real migration with LLM
class {os.path.basename(file_path).replace('.kt', '')} {
    // Original code:
    // {original_code[:200]}...
}
"""
        
        results.append(MigrationResult(
            original_path=file_path,
            migrated_code=mock_code,
            target_module="shared/src/commonMain/kotlin",
            success=True,  # Mock is "successful" but code is placeholder
            tokens_used=0,
            latency_ms=0
        ))
    
    return results


def save_migrated_file(
    original_path: str,
    migrated_code: str,
    target_module: str,
    project_path: str
):
    """
    Save migrated code to the correct location.
    
    Creates directory structure as needed.
    """
    # Determine target path
    migrated_project = os.path.join(project_path, 'migrated_kmp_project')
    target_path = os.path.join(migrated_project, target_module, os.path.basename(original_path))
    
    # Create directories
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    # Write file
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(migrated_code)
    
    logger.info(f"Saved migrated file: {target_path}")


def detect_applicable_skills(code: str, skills: Dict) -> List[Dict]:
    """
    Detect which skills apply to this code.
    
    Matches code against skill patterns (dependencies, imports, etc.)
    """
    applicable = []
    
    for skill_id, skill in skills.items():
        # Check if skill's Android dependency is in the code
        if skill.android_dependency and skill.android_dependency in code:
            applicable.append(skill.to_dict())
        # Check for common patterns
        elif skill_id == 'viewmodel-to-shared' and 'ViewModel' in code:
            applicable.append(skill.to_dict())
        elif skill_id == 'room-to-sqldelight' and ('@Entity' in code or 'Room' in code):
            applicable.append(skill.to_dict())
    
    return applicable
```

---

## Step 2: Update Orchestrator

**File:** `orchestrator.py`

**Change:**
```python
# OLD
from generation.batch_migration import BatchMigrator
migration_plan = migrator.analyze_project()
migration_results = migrator.migrate_all()

# NEW
from generation.generate_code import generate_kmp_code
generate_kmp_code(
    project_path=self.project_path,
    delegate_task=self.delegate_task,
    use_real_llm=True  # Enable real LLM
)
```

---

## Step 3: Add Configuration

**File:** `core/config.py`

**Add:**
```python
@dataclass
class LLMConfig:
    """LLM configuration for code generation."""
    provider: str = "ollama"
    model: str = "qwen2.5-coder:7b"
    base_url: str = "http://localhost:11434"
    api_key: Optional[str] = None
    timeout: int = 120
    max_tokens: int = 4096
    temperature: float = 0.3  # Lower for code generation
    
    # Cost tracking
    track_tokens: bool = True
    cost_limit_usd: float = 10.0  # Prevent runaway costs


@dataclass  
class MigrationConfig:
    """Complete migration configuration."""
    # ... existing fields ...
    
    # LLM settings
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Code generation
    use_real_llm: bool = True
    batch_size: int = 5  # Files per batch
    retry_failed: bool = True
    max_retries: int = 3
```

---

## Step 4: Add Cost Tracking

**File:** `llm/enhanced_invoker.py`

**Add to LLMStatistics:**
```python
@dataclass
class LLMStatistics:
    # ... existing fields ...
    
    # Cost tracking
    total_cost_usd: float = 0.0
    cost_limit_exceeded: bool = False
    
    def add_token_usage(self, prompt_tokens: int, completion_tokens: int, model: str):
        """Track token usage and calculate cost."""
        pricing = MODEL_PRICING.get(model, {'prompt': 0.001, 'completion': 0.003})
        cost = (prompt_tokens * pricing['prompt'] + completion_tokens * pricing['completion']) / 1000
        
        self.total_cost_usd += cost
        
        # Check limit
        if self.total_cost_usd > self.cost_limit:
            self.cost_limit_exceeded = True
            logger.warning(f"Cost limit exceeded: ${self.total_cost_usd:.2f}")
```

---

## Step 5: Testing

**File:** NEW `tests/test_real_llm_migration.py`

```python
import pytest
from generation.generate_code import generate_kmp_code, migrate_batch_with_llm
from llm import get_enhanced_invoker

@pytest.fixture
def invoker():
    return get_enhanced_invoker('ollama', 'qwen2.5-coder:7b')

@pytest.fixture
def sample_android_file():
    return """
package com.example.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.LiveData

class UserViewModel : ViewModel() {
    private val _user = MutableLiveData<User>()
    val user: LiveData<User> = _user
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            _user.value = repository.getUser(id)
        }
    }
}
"""

def test_real_migration(invoker, sample_android_file):
    """Test real LLM migration."""
    files = ['/tmp/TestViewModel.kt']
    
    # Save test file
    with open(files[0], 'w') as f:
        f.write(sample_android_file)
    
    # Migrate
    results = migrate_batch_with_llm(
        invoker=invoker,
        files=files,
        batch_name="ViewModel",
        skills={},
        project_path="/tmp"
    )
    
    # Verify
    assert len(results) == 1
    assert results[0].success
    assert 'StateFlow' in results[0].migrated_code or 'Flow' in results[0].migrated_code
    assert 'LiveData' not in results[0].migrated_code  # Should be migrated
```

---

## Step 6: Rollout Plan

### Week 1: Core Integration
- [ ] Update generate_code.py with real LLM calls
- [ ] Add prompt building and response parsing
- [ ] Add code validation
- [ ] Test with small files

### Week 2: Reliability
- [ ] Add retry logic
- [ ] Add cost tracking
- [ ] Add error handling
- [ ] Test with medium projects

### Week 3: Optimization
- [ ] Optimize prompts for better quality
- [ ] Add batch processing
- [ ] Add caching for repeated patterns
- [ ] Test with large projects

### Week 4: Production
- [ ] Add monitoring/logging
- [ ] Add user feedback collection
- [ ] Document known limitations
- [ ] Release to beta users

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Code compiles without fixes | 80%+ | 0% (mock) |
| Business logic preserved | 90%+ | N/A |
| KMP best practices followed | 85%+ | N/A |
| Migration time per file | <30s | <1s (mock) |
| Cost per file | <$0.01 | $0 (mock) |
| User satisfaction | 4/5 | N/A |

---

*Phase 1 Implementation Plan - Real LLM Integration*
