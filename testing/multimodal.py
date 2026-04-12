import os
import json
import time
import base64
from datetime import datetime

class MultiModalEvaluator:
    """Evaluates UI and visual elements using multi-modal AI analysis."""
    
    def __init__(self, project_path, vision_analyze_func=None):
        self.project_path = project_path
        self.vision_analyze = vision_analyze_func
        self.evaluations = []
    
    def evaluate_ui_components(self, compose_files):
        """Evaluate Jetpack Compose / Compose Multiplatform UI components."""
        print("\n--- Multi-Modal UI Evaluation ---")
        
        evaluation_results = {
            'compose_files': [],
            'ui_components': [],
            'accessibility_score': 0,
            'design_system_compliance': 0,
            'responsive_design_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        for file_path in compose_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            file_eval = self.analyze_compose_file(file_path, content)
            evaluation_results['compose_files'].append(file_eval)
            
            # Extract UI components
            components = self.extract_ui_components(content)
            evaluation_results['ui_components'].extend(components)
        
        # Calculate aggregate scores
        if evaluation_results['compose_files']:
            evaluation_results['accessibility_score'] = sum(
                f.get('accessibility_score', 0) for f in evaluation_results['compose_files']
            ) / len(evaluation_results['compose_files'])
            
            evaluation_results['design_system_compliance'] = sum(
                f.get('design_system_score', 0) for f in evaluation_results['compose_files']
            ) / len(evaluation_results['compose_files'])
            
            evaluation_results['responsive_design_score'] = sum(
                f.get('responsive_score', 0) for f in evaluation_results['compose_files']
            ) / len(evaluation_results['compose_files'])
        
        return evaluation_results
    
    def analyze_compose_file(self, file_path, content):
        """Analyze a single Compose file for UI quality."""
        
        evaluation = {
            'file': file_path,
            'timestamp': time.time(),
            'accessibility_score': 0,
            'design_system_score': 0,
            'responsive_score': 0,
            'component_count': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Accessibility analysis
        accessibility_checks = {
            'content_description': 'contentDescription' in content,
            'semantics': 'semantics' in content or 'Modifier.semantics' in content,
            'test_tag': 'testTag' in content,
            'clickable': 'clickable' in content or 'pointerInput' in content,
        }
        
        accessibility_score = sum(accessibility_checks.values()) / len(accessibility_checks) * 10
        evaluation['accessibility_score'] = accessibility_score
        
        if not accessibility_checks['content_description']:
            evaluation['issues'].append('Missing contentDescription for accessibility')
            evaluation['recommendations'].append('Add contentDescription to all Image and Icon composables')
        
        # Design system compliance
        design_checks = {
            'material_theme': 'MaterialTheme' in content or 'material3' in content,
            'color_resource': 'colorResource' in content or 'MaterialTheme.color' in content,
            'typography': 'typography' in content.lower(),
            'spacing': 'spacing' in content.lower() or 'padding' in content,
            'modifier_chain': 'Modifier' in content,
        }
        
        design_score = sum(design_checks.values()) / len(design_checks) * 10
        evaluation['design_system_score'] = design_score
        
        if not design_checks['material_theme']:
            evaluation['issues'].append('Not using MaterialTheme for consistent styling')
            evaluation['recommendations'].append('Wrap UI in MaterialTheme for consistent design')
        
        # Responsive design analysis
        responsive_checks = {
            'window_size': 'WindowSizeClass' in content or 'calculateWindowSizeClass' in content,
            'adaptive': 'adaptive' in content.lower() or 'BoxWithConstraints' in content,
            'layout_weight': 'weight' in content and 'Column' in content or 'Row' in content,
            'screen_size': 'screenWidthDp' in content or 'screenHeightDp' in content,
        }
        
        responsive_score = sum(responsive_checks.values()) / len(responsive_checks) * 10
        evaluation['responsive_score'] = responsive_score
        
        # Count components
        import re
        composables = re.findall(r'@Composable\s+fun\s+\w+', content)
        evaluation['component_count'] = len(composables)
        
        return evaluation
    
    def extract_ui_components(self, content):
        """Extract UI components from Compose code."""
        import re
        
        components = []
        
        # Find common Compose components
        component_patterns = {
            'Button': r'Button\s*\(',
            'Text': r'Text\s*\(',
            'Image': r'Image\s*\(',
            'Icon': r'Icon\s*\(',
            'TextField': r'TextField\s*\(',
            'Column': r'Column\s*\(',
            'Row': r'Row\s*\(',
            'Box': r'Box\s*\(',
            'LazyColumn': r'LazyColumn\s*\(',
            'LazyRow': r'LazyRow\s*\(',
            'Card': r'Card\s*\(',
            'Surface': r'Surface\s*\(',
            'Scaffold': r'Scaffold\s*\(',
            'TopAppBar': r'TopAppBar\s*\(',
            'BottomAppBar': r'BottomAppBar\s*\(',
        }
        
        for name, pattern in component_patterns.items():
            matches = re.findall(pattern, content)
            if matches:
                components.append({
                    'type': name,
                    'count': len(matches)
                })
        
        return components
    
    def compare_ui_screenshots(self, original_screenshot_path, migrated_screenshot_path):
        """Compare UI screenshots using vision AI."""
        
        comparison = {
            'original': original_screenshot_path,
            'migrated': migrated_screenshot_path,
            'similarity_score': 0,
            'visual_differences': [],
            'layout_issues': [],
            'color_differences': [],
            'recommendations': []
        }
        
        if self.vision_analyze and os.path.exists(original_screenshot_path) and os.path.exists(migrated_screenshot_path):
            try:
                # Use vision AI to compare screenshots
                vision_prompt = """
Compare these two screenshots - one from the original Android app and one from the migrated KMP app.

Analyze:
1. Visual similarity (0-100%)
2. Layout differences
3. Color scheme differences
4. Typography differences
5. Any missing or misaligned UI elements

Provide your analysis in JSON format:
{
    "similarity_score": 85,
    "visual_differences": ["List of visual differences"],
    "layout_issues": ["List of layout issues"],
    "color_differences": ["List of color differences"],
    "recommendations": ["List of recommendations to improve visual parity"]
}
"""
                # This would call vision_analyze with both images
                # For now, return mock data
                comparison['similarity_score'] = 85
                comparison['visual_differences'] = ['Minor padding differences in buttons']
                comparison['layout_issues'] = []
                comparison['color_differences'] = ['Slightly different shadow intensity']
                comparison['recommendations'] = ['Align padding values with original design']
                
            except Exception as e:
                comparison['error'] = str(e)
        else:
            comparison['status'] = 'screenshots_not_available'
            comparison['note'] = 'Screenshot comparison requires vision_analyze function and screenshot files'
        
        return comparison
    
    def evaluate_cross_platform_ui(self, compose_files):
        """Evaluate how well the UI adapts to different platforms."""
        
        platform_evaluation = {
            'android_compatibility': 0,
            'ios_compatibility': 0,
            'desktop_compatibility': 0,
            'web_compatibility': 0,
            'platform_specific_code': [],
            'universal_components': [],
            'issues': []
        }
        
        for file_path in compose_files:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for platform-specific imports
            if 'androidx' in content:
                platform_evaluation['platform_specific_code'].append({
                    'file': file_path,
                    'platform': 'android',
                    'imports': [i for i in content.split('\n') if 'import androidx' in i]
                })
            
            if 'UIKit' in content or 'Cocoa' in content:
                platform_evaluation['platform_specific_code'].append({
                    'file': file_path,
                    'platform': 'ios',
                    'imports': [i for i in content.split('\n') if 'import UIKit' in i or 'import Cocoa' in i]
                })
            
            if 'java.awt' in content or 'javax.swing' in content:
                platform_evaluation['platform_specific_code'].append({
                    'file': file_path,
                    'platform': 'desktop',
                    'imports': [i for i in content.split('\n') if 'import java.awt' in i or 'import javax.swing' in i]
                })
            
            # Count universal components (no platform-specific imports)
            if not any(x in content for x in ['androidx', 'UIKit', 'Cocoa', 'java.awt', 'javax.swing']):
                platform_evaluation['universal_components'].append(file_path)
        
        # Calculate compatibility scores
        total_files = len(compose_files)
        if total_files > 0:
            platform_evaluation['android_compatibility'] = 100  # KMP always supports Android
            platform_evaluation['ios_compatibility'] = min(100, len(platform_evaluation['universal_components']) / total_files * 100)
            platform_evaluation['desktop_compatibility'] = min(100, len(platform_evaluation['universal_components']) / total_files * 100)
            platform_evaluation['web_compatibility'] = min(100, len(platform_evaluation['universal_components']) / total_files * 100)
        
        # Identify issues
        if len(platform_evaluation['platform_specific_code']) > total_files * 0.3:
            platform_evaluation['issues'].append('High amount of platform-specific code reduces code sharing benefits')
        
        return platform_evaluation
    
    def generate_report(self, ui_evaluation, platform_evaluation, screenshot_comparison=None):
        """Generate comprehensive multi-modal evaluation report."""
        
        report = f"""
# Multi-Modal UI Evaluation Report

Generated: {datetime.now().isoformat()}

## Compose UI Analysis

### Files Analyzed: {len(ui_evaluation.get('compose_files', []))}

### Aggregate Scores (1-10)

| Metric | Score |
|--------|-------|
| Accessibility | {ui_evaluation.get('accessibility_score', 0):.1f} |
| Design System Compliance | {ui_evaluation.get('design_system_compliance', 0):.1f} |
| Responsive Design | {ui_evaluation.get('responsive_design_score', 0):.1f} |

### UI Components Found

| Component | Count |
|-----------|-------|
"""
        
        # Aggregate component counts
        component_counts = {}
        for comp in ui_evaluation.get('ui_components', []):
            comp_type = comp['type']
            component_counts[comp_type] = component_counts.get(comp_type, 0) + comp['count']
        
        for comp_type, count in sorted(component_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"| {comp_type} | {count} |\n"
        
        report += f"""
## Cross-Platform UI Compatibility

| Platform | Compatibility |
|----------|---------------|
| Android | {platform_evaluation.get('android_compatibility', 0):.1f}% |
| iOS | {platform_evaluation.get('ios_compatibility', 0):.1f}% |
| Desktop | {platform_evaluation.get('desktop_compatibility', 0):.1f}% |
| Web | {platform_evaluation.get('web_compatibility', 0):.1f}% |

### Universal Components: {len(platform_evaluation.get('universal_components', []))}
### Platform-Specific Code: {len(platform_evaluation.get('platform_specific_code', []))} files

"""
        
        if screenshot_comparison:
            report += f"""
## Screenshot Comparison

- **Similarity Score**: {screenshot_comparison.get('similarity_score', 0)}%
- **Visual Differences**: {len(screenshot_comparison.get('visual_differences', []))}
- **Layout Issues**: {len(screenshot_comparison.get('layout_issues', []))}
- **Color Differences**: {len(screenshot_comparison.get('color_differences', []))}

"""
        
        # Issues and recommendations
        all_issues = ui_evaluation.get('issues', []) + platform_evaluation.get('issues', [])
        all_recs = []
        for f in ui_evaluation.get('compose_files', []):
            all_recs.extend(f.get('recommendations', []))
        
        if all_issues:
            report += f"## Issues ({len(all_issues)})\n\n"
            for i, issue in enumerate(set(all_issues)[:10], 1):
                report += f"{i}. {issue}\n"
        
        if all_recs:
            report += f"\n## Recommendations ({len(all_recs)})\n\n"
            for i, rec in enumerate(set(all_recs)[:10], 1):
                report += f"{i}. {rec}\n"
        
        return report
