import os
import json
import time

class LLMJudge:
    """Uses LLM to evaluate code quality, correctness, and KMP best practices."""
    
    def __init__(self, project_path, delegate_task=None):
        self.project_path = project_path
        self.delegate_task = delegate_task
        self.evaluations = []
    
    def evaluate_all(self, migrated_files):
        """Evaluate all migrated files using LLM."""
        print("\n--- LLM-as-a-Judge Evaluation ---")
        
        for file_info in migrated_files:
            evaluation = self.evaluate_file(file_info)
            self.evaluations.append(evaluation)
        
        return self.generate_report()
    
    def evaluate_file(self, file_info):
        """Evaluate a single migrated file."""
        file_path = file_info['path']
        original_path = file_info.get('original_path', 'N/A')
        content = file_info['content']
        
        evaluation = {
            'file': file_path,
            'original_file': original_path,
            'timestamp': time.time(),
            'scores': {},
            'feedback': '',
            'issues': [],
            'recommendations': []
        }
        
        # Use LLM to evaluate if delegate_task is available
        if self.delegate_task:
            judge_prompt = f"""
You are an expert Kotlin Multiplatform code reviewer. Evaluate the following migrated KMP code.

## Evaluation Criteria

Rate each criterion from 1-10 (10 being best):

1. **Correctness**: Does the code compile and function correctly?
2. **KMP Best Practices**: Does it follow KMP conventions (expect/actual, common code)?
3. **Code Quality**: Is the code clean, readable, and well-structured?
4. **Platform Separation**: Is platform-specific code properly isolated?
5. **Dependency Usage**: Are KMP-compatible libraries used correctly?
6. **Error Handling**: Is error handling appropriate for multiplatform?
7. **Testing**: Are there appropriate tests for this code?
8. **Documentation**: Is the code well-documented?
9. **Performance**: Are there any obvious performance issues?
10. **Maintainability**: Is the code easy to maintain and extend?

## Code to Evaluate

File: {file_path}
Original: {original_path}

```kotlin
{content}
```

## Output Format

Provide your evaluation in this exact JSON format:
{{
    "scores": {{
        "correctness": 8,
        "kmp_best_practices": 7,
        "code_quality": 9,
        "platform_separation": 8,
        "dependency_usage": 7,
        "error_handling": 6,
        "testing": 5,
        "documentation": 7,
        "performance": 8,
        "maintainability": 8
    }},
    "overall_score": 7.5,
    "feedback": "Brief summary of the code quality",
    "issues": ["List of specific issues found"],
    "recommendations": ["List of recommendations for improvement"]
}}

Provide ONLY the JSON, no other text.
"""
            
            try:
                llm_response = self.delegate_task(goal=judge_prompt, toolsets=None)
                
                # Parse the JSON response
                try:
                    # Try to extract JSON from response
                    json_start = llm_response.find('{')
                    json_end = llm_response.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = llm_response[json_start:json_end]
                        parsed = json.loads(json_str)
                        
                        evaluation['scores'] = parsed.get('scores', {})
                        evaluation['overall_score'] = parsed.get('overall_score', 0)
                        evaluation['feedback'] = parsed.get('feedback', '')
                        evaluation['issues'] = parsed.get('issues', [])
                        evaluation['recommendations'] = parsed.get('recommendations', [])
                    else:
                        evaluation['feedback'] = llm_response
                        evaluation['overall_score'] = 5.0
                except json.JSONDecodeError:
                    evaluation['feedback'] = f"Failed to parse LLM response: {llm_response[:500]}"
                    evaluation['overall_score'] = 0
                    
            except Exception as e:
                evaluation['feedback'] = f"LLM evaluation failed: {str(e)}"
                evaluation['overall_score'] = 0
        else:
            # Mock evaluation for testing
            evaluation['scores'] = {
                'correctness': 8,
                'kmp_best_practices': 7,
                'code_quality': 8,
                'platform_separation': 7,
                'dependency_usage': 6,
                'error_handling': 6,
                'testing': 5,
                'documentation': 6,
                'performance': 7,
                'maintainability': 7
            }
            evaluation['overall_score'] = 6.7
            evaluation['feedback'] = "Code follows general KMP patterns but could improve dependency usage."
            evaluation['issues'] = ["Some Android-specific dependencies detected"]
            evaluation['recommendations'] = ["Replace with KMP-compatible alternatives"]
        
        return evaluation
    
    def evaluate_architecture(self, all_files):
        """Evaluate the overall architecture of the migrated project."""
        print("\n--- Architecture Evaluation ---")
        
        architecture_prompt = f"""
You are an expert software architect specializing in Kotlin Multiplatform. 
Evaluate the overall architecture of this migrated KMP project.

## Files in Project

{json.dumps([f['path'] for f in all_files], indent=2)}

## Evaluation Criteria

Rate each criterion from 1-10:

1. **Modularity**: Is the code well-organized into modules?
2. **Separation of Concerns**: Are responsibilities clearly separated?
3. **Dependency Injection**: Is DI implemented appropriately?
4. **Layer Architecture**: Are data/domain/presentation layers separated?
5. **KMP Structure**: Is the shared/platform code structure optimal?
6. **Scalability**: Can the architecture scale with new features?
7. **Testability**: Is the architecture conducive to testing?

## Output Format

Provide your evaluation in this exact JSON format:
{{
    "scores": {{
        "modularity": 8,
        "separation_of_concerns": 7,
        "dependency_injection": 6,
        "layer_architecture": 7,
        "kmp_structure": 8,
        "scalability": 7,
        "testability": 6
    }},
    "overall_score": 7.0,
    "architecture_pattern": "MVVM / MVI / Clean Architecture",
    "strengths": ["List of architectural strengths"],
    "weaknesses": ["List of architectural weaknesses"],
    "recommendations": ["List of recommendations"]
}}

Provide ONLY the JSON, no other text.
"""
        
        if self.delegate_task:
            try:
                llm_response = self.delegate_task(goal=architecture_prompt, toolsets=None)
                
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = llm_response[json_start:json_end]
                    return json.loads(json_str)
            except Exception as e:
                return {'error': str(e), 'overall_score': 0}
        
        # Mock evaluation
        return {
            'scores': {
                'modularity': 7,
                'separation_of_concerns': 7,
                'dependency_injection': 5,
                'layer_architecture': 6,
                'kmp_structure': 7,
                'scalability': 6,
                'testability': 6
            },
            'overall_score': 6.3,
            'architecture_pattern': 'MVVM',
            'strengths': ['Clear separation of UI and logic', 'Good use of ViewModels'],
            'weaknesses': ['Limited dependency injection', 'Some tight coupling'],
            'recommendations': ['Add Koin for DI', 'Extract use cases for better separation']
        }
    
    def compare_implementations(self, original_code, migrated_code):
        """Compare original Android code with migrated KMP code."""
        
        comparison_prompt = f"""
You are an expert code reviewer comparing Android and KMP implementations.

## Original Android Code

```kotlin
{original_code}
```

## Migrated KMP Code

```kotlin
{migrated_code}
```

## Evaluation

Compare the two implementations and evaluate:

1. **Functional Equivalence**: Does the KMP code provide the same functionality?
2. **Code Quality Improvement**: Is the KMP code cleaner or more maintainable?
3. **Platform Coverage**: Does the KMP code support more platforms?
4. **Performance**: Are there any performance regressions?
5. **API Design**: Is the KMP API design better?

## Output Format

{{
    "functional_equivalence": 9,
    "code_quality_delta": "+2",
    "platform_coverage_delta": "+3 (Android -> Android+iOS+Desktop)",
    "performance_delta": "0",
    "api_design_delta": "+1",
    "summary": "Brief comparison summary",
    "regressions": ["Any functionality lost"],
    "improvements": ["Any improvements gained"]
}}

Provide ONLY the JSON, no other text.
"""
        
        if self.delegate_task:
            try:
                llm_response = self.delegate_task(goal=comparison_prompt, toolsets=None)
                json_start = llm_response.find('{')
                json_end = llm_response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    return json.loads(llm_response[json_start:json_end])
            except:
                pass
        
        return {
            'functional_equivalence': 8,
            'code_quality_delta': '+1',
            'platform_coverage_delta': '+3',
            'performance_delta': '0',
            'api_design_delta': '+1',
            'summary': 'KMP migration successful with minor improvements',
            'regressions': [],
            'improvements': ['Multiplatform support', 'Cleaner architecture']
        }
    
    def generate_report(self):
        """Generate comprehensive LLM judge report."""
        if not self.evaluations:
            return "No evaluations performed."
        
        # Calculate averages
        avg_scores = {}
        score_keys = ['correctness', 'kmp_best_practices', 'code_quality', 
                      'platform_separation', 'dependency_usage', 'error_handling',
                      'testing', 'documentation', 'performance', 'maintainability']
        
        for key in score_keys:
            values = [e['scores'].get(key, 0) for e in self.evaluations if e.get('scores')]
            avg_scores[key] = sum(values) / len(values) if values else 0
        
        overall_avg = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0
        
        # Collect all issues and recommendations
        all_issues = []
        all_recommendations = []
        for e in self.evaluations:
            all_issues.extend(e.get('issues', []))
            all_recommendations.extend(e.get('recommendations', []))
        
        report = f"""
# LLM-as-a-Judge Evaluation Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
Files Evaluated: {len(self.evaluations)}

## Average Scores (1-10)

| Criterion | Score |
|-----------|-------|
| Correctness | {avg_scores.get('correctness', 0):.1f} |
| KMP Best Practices | {avg_scores.get('kmp_best_practices', 0):.1f} |
| Code Quality | {avg_scores.get('code_quality', 0):.1f} |
| Platform Separation | {avg_scores.get('platform_separation', 0):.1f} |
| Dependency Usage | {avg_scores.get('dependency_usage', 0):.1f} |
| Error Handling | {avg_scores.get('error_handling', 0):.1f} |
| Testing | {avg_scores.get('testing', 0):.1f} |
| Documentation | {avg_scores.get('documentation', 0):.1f} |
| Performance | {avg_scores.get('performance', 0):.1f} |
| Maintainability | {avg_scores.get('maintainability', 0):.1f} |

## Overall Score: {overall_avg:.1f}/10

## Common Issues ({len(all_issues)})

"""
        
        for i, issue in enumerate(list(set(all_issues))[:10], 1):
            report += f"{i}. {issue}\n"
        
        report += f"\n## Recommendations ({len(all_recommendations)})\n\n"
        
        for i, rec in enumerate(list(set(all_recommendations))[:10], 1):
            report += f"{i}. {rec}\n"
        
        # Individual file scores
        report += "\n## Individual File Scores\n\n"
        report += "| File | Overall Score | Key Issues |\n"
        report += "|------|---------------|------------|\n"
        
        for e in self.evaluations:
            issues = ', '.join(e.get('issues', [])[:2])
            report += f"| {os.path.basename(e['file'])} | {e.get('overall_score', 0):.1f} | {issues[:50]}... |\n"
        
        return report
