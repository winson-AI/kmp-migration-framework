"""
Prompt Management System

Features:
- Prompt templates with variable substitution
- Prompt versioning and A/B testing
- Prompt optimization utilities
- Built-in templates for KMP migration tasks

Usage:
    from llm.prompts import PromptManager
    
    pm = PromptManager()
    prompt = pm.render('code_migration', {
        'source_code': code,
        'target_platform': 'KMP'
    })
"""

import os
import json
import re
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """Prompt template with metadata."""
    id: str
    name: str
    description: str
    template: str
    version: str = "1.0.0"
    variables: List[str] = None
    tags: List[str] = None
    created_at: str = None
    updated_at: str = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = self._extract_variables()
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def _extract_variables(self) -> List[str]:
        """Extract variable names from template."""
        return re.findall(r'\{\{(\w+)\}\}', self.template)
    
    def render(self, **kwargs) -> str:
        """Render template with provided variables."""
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f'{{{{{key}}}}}', str(value))
        return result
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PromptTemplate':
        return cls(**data)


@dataclass
class PromptResult:
    """Result of prompt rendering and optimization."""
    template_id: str
    rendered_prompt: str
    variables_used: Dict[str, Any]
    token_estimate: int
    optimization_notes: List[str] = None
    
    def __post_init__(self):
        if self.optimization_notes is None:
            self.optimization_notes = []


class PromptManager:
    """Manage prompt templates and rendering."""
    
    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize prompt manager.
        
        Args:
            templates_dir: Directory to load/save templates (default: ~/.hermes/kmp-migration/prompts)
        """
        self.templates_dir = templates_dir or os.path.expanduser('~/.hermes/kmp-migration/prompts')
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_builtin_templates()
        self._load_custom_templates()
    
    def _load_builtin_templates(self):
        """Load built-in KMP migration templates."""
        builtin_templates = self._get_builtin_templates()
        for template_data in builtin_templates:
            template = PromptTemplate(**template_data)
            self.templates[template.id] = template
            logger.debug(f"Loaded built-in template: {template.id}")
    
    def _get_builtin_templates(self) -> List[Dict]:
        """Return built-in prompt templates."""
        return [
            {
                'id': 'code_migration',
                'name': 'Code Migration',
                'description': 'Migrate code from Android to KMP',
                'version': '2.0.0',
                'tags': ['migration', 'code', 'kmp'],
                'template': '''You are an expert Kotlin Multiplatform developer.

## Task
Migrate the following Android code to Kotlin Multiplatform (KMP).

## Guidelines
- Place shared code in `commonMain` source set
- Use `expect`/`actual` for platform-specific code
- Replace Android dependencies with KMP equivalents:
  - Retrofit → Ktor Client
  - Room → SQLDelight
  - ViewModel → Kotlinx Coroutines + StateFlow
  - LiveData → Kotlinx Flow
  - Gson/Moshi → Kotlinx Serialization

## Original Code
File: {{file_path}}
```kotlin
{{source_code}}
```

## Output Format
Provide the migrated KMP code with:
1. The complete migrated code
2. A brief explanation of changes made
3. Any platform-specific considerations

## Target Module
{{target_module}}
'''
            },
            {
                'id': 'code_review',
                'name': 'Code Review',
                'description': 'Review migrated KMP code for quality',
                'version': '2.0.0',
                'tags': ['review', 'quality', 'kmp'],
                'template': '''You are an expert KMP code reviewer.

## Task
Review the following migrated KMP code for quality, correctness, and best practices.

## Evaluation Criteria (rate 1-10)
1. **Correctness**: Does the code compile and function correctly?
2. **KMP Best Practices**: Proper use of expect/actual, common code?
3. **Code Quality**: Clean, readable, well-structured?
4. **Platform Separation**: Platform-specific code properly isolated?
5. **Dependency Usage**: KMP-compatible libraries used correctly?
6. **Error Handling**: Appropriate for multiplatform?
7. **Testing**: Testable code structure?
8. **Documentation**: Well-documented?
9. **Performance**: No obvious performance issues?
10. **Maintainability**: Easy to maintain and extend?

## Code to Review
File: {{file_path}}
```kotlin
{{source_code}}
```

## Output Format
Provide your review in this exact JSON format:
{
    "scores": {
        "correctness": 8,
        "kmp_best_practices": 7,
        "code_quality": 8,
        "platform_separation": 7,
        "dependency_usage": 6,
        "error_handling": 6,
        "testing": 5,
        "documentation": 6,
        "performance": 7,
        "maintainability": 7
    },
    "overall_score": 7.1,
    "feedback": "Brief summary",
    "issues": ["List of specific issues"],
    "recommendations": ["List of recommendations"]
}

Return ONLY the JSON, no other text.
'''
            },
            {
                'id': 'architecture_analysis',
                'name': 'Architecture Analysis',
                'description': 'Analyze project architecture',
                'version': '1.0.0',
                'tags': ['architecture', 'analysis'],
                'template': '''You are an expert software architect specializing in Kotlin Multiplatform.

## Task
Analyze the architecture of this KMP project and provide recommendations.

## Project Structure
{{project_structure}}

## Files
{{file_list}}

## Evaluation Criteria (rate 1-10)
1. **Modularity**: Well-organized modules?
2. **Separation of Concerns**: Clear responsibility boundaries?
3. **Dependency Injection**: Appropriate DI implementation?
4. **Layer Architecture**: Data/domain/presentation separation?
5. **KMP Structure**: Optimal shared/platform code structure?
6. **Scalability**: Can scale with new features?
7. **Testability**: Conducive to testing?

## Output Format
Provide analysis in JSON format:
{
    "scores": {
        "modularity": 8,
        "separation_of_concerns": 7,
        "dependency_injection": 6,
        "layer_architecture": 7,
        "kmp_structure": 8,
        "scalability": 7,
        "testability": 6
    },
    "overall_score": 7.0,
    "architecture_pattern": "MVVM/MVI/Clean Architecture",
    "strengths": ["List of strengths"],
    "weaknesses": ["List of weaknesses"],
    "recommendations": ["List of recommendations"]
}

Return ONLY the JSON.
'''
            },
            {
                'id': 'dependency_mapping',
                'name': 'Dependency Mapping',
                'description': 'Map Android dependencies to KMP equivalents',
                'version': '1.0.0',
                'tags': ['dependencies', 'mapping'],
                'template': '''You are an expert in Kotlin Multiplatform dependencies.

## Task
Map the following Android dependencies to their KMP equivalents.

## Dependencies to Map
{{dependencies}}

## Known Mappings
- com.squareup.retrofit2:retrofit → io.ktor:ktor-client-core
- androidx.room:room-runtime → app.cash.sqldelight:runtime
- androidx.lifecycle:lifecycle-viewmodel → org.jetbrains.kotlinx:kotlinx-coroutines-core
- com.google.code.gson:gson → org.jetbrains.kotlinx:kotlinx-serialization-json
- androidx.test:runner → kotlin.test: kotlin-test

## Output Format
Provide mapping in JSON format:
{
    "mappings": [
        {
            "android_dependency": "com.example:library:1.0.0",
            "kmp_equivalent": "com.example:kmp-library:1.0.0",
            "migration_notes": "Any special migration notes",
            "compatibility": "full/partial/none"
        }
    ],
    "unresolved": ["Dependencies with no KMP equivalent"]
}

Return ONLY the JSON.
'''
            },
            {
                'id': 'test_generation',
                'name': 'Test Generation',
                'description': 'Generate tests for KMP code',
                'version': '1.0.0',
                'tags': ['testing', 'generation'],
                'template': '''You are an expert in KMP testing.

## Task
Generate comprehensive tests for the following KMP code.

## Source Code
```kotlin
{{source_code}}
```

## Testing Guidelines
- Use `kotlin.test` for common tests
- Use platform-specific test frameworks where needed
- Cover edge cases and error conditions
- Include both unit tests and integration tests

## Output Format
Provide tests in this format:
```kotlin
// Test file content
```

Include:
1. Test file path
2. Complete test code
3. Brief explanation of test coverage
'''
            },
            {
                'id': 'skill_improvement',
                'name': 'Skill Improvement',
                'description': 'Improve migration skills based on feedback',
                'version': '1.0.0',
                'tags': ['learning', 'improvement'],
                'template': '''You are a learning system improving KMP migration skills.

## Task
Analyze failed migrations and suggest improvements to the migration skill guide.

## Failed Migration
File: {{file_path}}
Original Code:
```kotlin
{{original_code}}
```

Migrated Code:
```kotlin
{{migrated_code}}
```

## Evaluation Feedback
{{feedback}}

## Current Skill Guide
{{current_guide}}

## Output Format
Provide improvements in this format:
{
    "skill_id": "{{skill_id}}",
    "confidence": 0.85,
    "proposed_changes": [
        {
            "section": "guide.md section to update",
            "old_content": "Current content",
            "new_content": "Proposed new content",
            "reason": "Why this change is needed"
        }
    ],
    "auto_apply": true/false
}

Return ONLY the JSON.
'''
            }
        ]
    
    def _load_custom_templates(self):
        """Load custom templates from disk."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir, exist_ok=True)
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.templates_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        template = PromptTemplate.from_dict(data)
                        self.templates[template.id] = template
                        logger.debug(f"Loaded custom template: {template.id}")
                except Exception as e:
                    logger.warning(f"Failed to load template {filename}: {e}")
    
    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def render(self, template_id: str, **kwargs) -> PromptResult:
        """
        Render a template with provided variables.
        
        Args:
            template_id: Template ID
            **kwargs: Variables to substitute
        
        Returns:
            PromptResult with rendered prompt
        """
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        rendered = template.render(**kwargs)
        
        # Estimate tokens (rough approximation)
        token_estimate = len(rendered.split()) * 1.3
        
        # Optimization notes
        optimization_notes = []
        if token_estimate > 3000:
            optimization_notes.append(f"Large prompt ({token_estimate:.0f} tokens) - consider splitting")
        if len(kwargs) < len(template.variables):
            missing = set(template.variables) - set(kwargs.keys())
            optimization_notes.append(f"Missing variables: {missing}")
        
        return PromptResult(
            template_id=template_id,
            rendered_prompt=rendered,
            variables_used=kwargs,
            token_estimate=int(token_estimate),
            optimization_notes=optimization_notes
        )
    
    def invoke(self, template_id: str, llm_invoker, **kwargs) -> Any:
        """
        Render template and invoke LLM in one step.
        
        Args:
            template_id: Template ID
            llm_invoker: LLMInvoker instance
            **kwargs: Variables for template
        
        Returns:
            LLMResponse from invoker
        """
        result = self.render(template_id, **kwargs)
        
        # Log optimization notes
        for note in result.optimization_notes:
            logger.info(f"Prompt optimization: {note}")
        
        return llm_invoker.invoke(result.rendered_prompt)
    
    def save_template(self, template: PromptTemplate):
        """Save a custom template to disk."""
        template.updated_at = datetime.now().isoformat()
        filepath = os.path.join(self.templates_dir, f"{template.id}.json")
        
        with open(filepath, 'w') as f:
            json.dump(template.to_dict(), f, indent=2)
        
        self.templates[template.id] = template
        logger.info(f"Saved template: {template.id}")
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template."""
        if template_id not in self.templates:
            return False
        
        filepath = os.path.join(self.templates_dir, f"{template_id}.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        del self.templates[template_id]
        logger.info(f"Deleted template: {template_id}")
        return True
    
    def list_templates(self, tags: Optional[List[str]] = None) -> List[Dict]:
        """List all templates, optionally filtered by tags."""
        result = []
        for template in self.templates.values():
            if tags:
                if any(tag in template.tags for tag in tags):
                    result.append({
                        'id': template.id,
                        'name': template.name,
                        'description': template.description,
                        'version': template.version,
                        'tags': template.tags
                    })
            else:
                result.append({
                    'id': template.id,
                    'name': template.name,
                    'description': template.description,
                    'version': template.version,
                    'tags': template.tags
                })
        return result
    
    def optimize_prompt(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Optimize a prompt to fit within token limits.
        
        Strategies:
        - Remove redundant whitespace
        - Truncate long code blocks
        - Remove verbose instructions
        """
        optimized = prompt
        
        # Remove multiple blank lines
        optimized = re.sub(r'\n{3,}', '\n\n', optimized)
        
        # Remove leading/trailing whitespace from lines
        optimized = '\n'.join(line.strip() for line in optimized.split('\n'))
        
        # Check token count
        token_estimate = len(optimized.split()) * 1.3
        
        if token_estimate > max_tokens:
            # Truncate code blocks
            code_blocks = re.findall(r'```[\s\S]*?```', optimized)
            for block in code_blocks:
                if len(block) > 500:
                    truncated = block[:250] + '\n// ... truncated ...\n' + block[-250:]
                    optimized = optimized.replace(block, truncated)
        
        return optimized
    
    def ab_test(self, template_a: PromptTemplate, template_b: PromptTemplate,
                test_cases: List[Dict], llm_invoker) -> Dict:
        """
        A/B test two prompt templates.
        
        Args:
            template_a: First template
            template_b: Second template
            test_cases: List of test inputs
            llm_invoker: LLMInvoker instance
        
        Returns:
            Comparison results
        """
        results = {
            'template_a': {'scores': [], 'latencies': []},
            'template_b': {'scores': [], 'latencies': []}
        }
        
        for test_case in test_cases:
            # Test template A
            prompt_a = template_a.render(**test_case)
            response_a = llm_invoker.invoke(prompt_a)
            results['template_a']['scores'].append(self._score_response(response_a))
            results['template_a']['latencies'].append(response_a.latency_ms)
            
            # Test template B
            prompt_b = template_b.render(**test_case)
            response_b = llm_invoker.invoke(prompt_b)
            results['template_b']['scores'].append(self._score_response(response_b))
            results['template_b']['latencies'].append(response_b.latency_ms)
        
        # Calculate averages
        results['template_a']['avg_score'] = sum(results['template_a']['scores']) / len(results['template_a']['scores'])
        results['template_b']['avg_score'] = sum(results['template_b']['scores']) / len(results['template_b']['scores'])
        results['template_a']['avg_latency'] = sum(results['template_a']['latencies']) / len(results['template_a']['latencies'])
        results['template_b']['avg_latency'] = sum(results['template_b']['latencies']) / len(results['template_b']['latencies'])
        
        results['winner'] = 'A' if results['template_a']['avg_score'] > results['template_b']['avg_score'] else 'B'
        
        return results
    
    def _score_response(self, response) -> float:
        """Score an LLM response (0-10)."""
        # Simple scoring based on response quality indicators
        score = 5.0
        
        if response.error:
            return 0.0
        
        content = response.content
        
        # Length bonus (not too short, not too long)
        word_count = len(content.split())
        if 100 <= word_count <= 500:
            score += 2.0
        elif 50 <= word_count <= 1000:
            score += 1.0
        
        # JSON structure bonus
        if content.strip().startswith('{') and content.strip().endswith('}'):
            try:
                json.loads(content)
                score += 2.0
            except:
                pass
        
        # Code blocks bonus
        if '```' in content:
            score += 1.0
        
        return min(10.0, score)
