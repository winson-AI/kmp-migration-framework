"""
Skills Hub - Centralized Skill Management

A comprehensive skill registry that agents can search and select from based on:
- Migration stage (planning, generation, testing, etc.)
- Agent type (planner, generator, evaluator, etc.)
- Project characteristics (architecture, dependencies, etc.)

Skills are organized by:
- Category (networking, database, architecture, etc.)
- Complexity (basic, intermediate, advanced)
- KMP Compatibility (full, partial, android-only)
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SkillCategory(Enum):
    """Skill categories."""
    NETWORKING = "networking"
    DATABASE = "database"
    ARCHITECTURE = "architecture"
    DEPENDENCY_INJECTION = "dependency_injection"
    SERIALIZATION = "serialization"
    UI = "ui"
    TESTING = "testing"
    UTILITIES = "utilities"
    PLATFORM = "platform"


class SkillComplexity(Enum):
    """Skill complexity levels."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class KMPCompatibility(Enum):
    """KMP compatibility levels."""
    FULL = "full"  # Works on all platforms
    PARTIAL = "partial"  # Needs expect/actual
    ANDROID_ONLY = "android_only"  # Keep in android module


class MigrationStage(Enum):
    """Migration stages."""
    EXPLORATION = "exploration"
    PLANNING = "planning"
    GENERATION = "generation"
    TESTING = "testing"
    EVALUATION = "evaluation"
    REFINEMENT = "refinement"


class AgentType(Enum):
    """Agent types."""
    EXPLORER = "explorer"
    PLANNER = "planner"
    GENERATOR = "generator"
    EVALUATOR = "evaluator"
    REFINER = "refiner"


@dataclass
class Skill:
    """A migration skill."""
    id: str
    name: str
    description: str
    category: SkillCategory
    complexity: SkillComplexity
    kmp_compatibility: KMPCompatibility
    
    # Android dependency
    android_dependency: str
    android_version: Optional[str] = None
    
    # KMP alternative
    kmp_dependency: Optional[str] = None
    kmp_version: Optional[str] = None
    
    # Migration guidance
    migration_guide: str = ""
    code_examples: Dict[str, str] = field(default_factory=dict)  # stage -> example
    common_issues: List[str] = field(default_factory=list)
    solutions: List[str] = field(default_factory=list)
    
    # Applicability
    applicable_stages: List[MigrationStage] = field(default_factory=list)
    applicable_agents: List[AgentType] = field(default_factory=list)
    applicable_architectures: List[str] = field(default_factory=list)
    
    # Metadata
    version: str = "1.0.0"
    author: str = "KMP Team"
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    usage_count: int = 0
    success_rate: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'complexity': self.complexity.value,
            'kmp_compatibility': self.kmp_compatibility.value,
            'android_dependency': self.android_dependency,
            'android_version': self.android_version,
            'kmp_dependency': self.kmp_dependency,
            'kmp_version': self.kmp_version,
            'migration_guide': self.migration_guide,
            'code_examples': self.code_examples,
            'common_issues': self.common_issues,
            'solutions': self.solutions,
            'applicable_stages': [s.value for s in self.applicable_stages],
            'applicable_agents': [a.value for a in self.applicable_agents],
            'applicable_architectures': self.applicable_architectures,
            'version': self.version,
            'author': self.author,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Skill':
        # Handle missing fields with defaults
        data['category'] = SkillCategory(data.get('category', 'utilities'))
        data['complexity'] = SkillComplexity(data.get('complexity', 'basic'))
        data['kmp_compatibility'] = KMPCompatibility(data.get('kmp_compatibility', 'partial'))
        data['applicable_stages'] = [MigrationStage(s) for s in data.get('applicable_stages', [])]
        data['applicable_agents'] = [AgentType(a) for a in data.get('applicable_agents', [])]
        data['kmp_dependency'] = data.get('kmp_dependency')
        data['android_version'] = data.get('android_version')
        data['kmp_version'] = data.get('kmp_version')
        return cls(**data)
    
    def matches_context(self, 
                       stage: Optional[MigrationStage] = None,
                       agent: Optional[AgentType] = None,
                       architecture: Optional[str] = None,
                       dependency: Optional[str] = None) -> bool:
        """Check if skill matches the given context."""
        if stage and stage not in self.applicable_stages:
            return False
        
        if agent and agent not in self.applicable_agents:
            return False
        
        if architecture and architecture not in self.applicable_architectures:
            return False
        
        if dependency and self.android_dependency not in dependency:
            return False
        
        return True


class SkillsHub:
    """
    Centralized skill registry and search system.
    
    Features:
    - Search skills by category, stage, agent, etc.
    - Recommend skills for migration context
    - Track skill usage and success rates
    - Load/save skills from JSON files
    """
    
    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = skills_dir or os.path.expanduser('~/.hermes/kmp-migration/skills')
        os.makedirs(self.skills_dir, exist_ok=True)
        
        self.skills: Dict[str, Skill] = {}
        
        # Load built-in skills
        self._load_builtin_skills()
        
        # Load custom skills
        self._load_custom_skills()
    
    def _load_builtin_skills(self):
        """Load built-in skills."""
        builtin_skills = self._get_builtin_skills()
        
        for skill_data in builtin_skills:
            skill = Skill.from_dict(skill_data)
            self.skills[skill.id] = skill
        
        logger.info(f"Loaded {len(self.skills)} built-in skills")
    
    def _get_builtin_skills(self) -> List[Dict]:
        """Get built-in skill definitions."""
        return [
            # Networking
            {
                'id': 'retrofit-to-ktor',
                'name': 'Retrofit to Ktor',
                'description': 'Migrate Retrofit networking to Ktor Multiplatform',
                'category': 'networking',
                'complexity': 'intermediate',
                'kmp_compatibility': 'full',
                'android_dependency': 'com.squareup.retrofit2:retrofit',
                'kmp_dependency': 'io.ktor:ktor-client-core',
                'migration_guide': '''
1. Add Ktor dependencies to shared module
2. Create HttpClient in commonMain
3. Migrate API interfaces to Ktor DSL
4. Handle platform-specific HTTP engines
''',
                'code_examples': {
                    'generation': '''
// Before (Retrofit)
interface ApiService {
    @GET("users/{id}")
    suspend fun getUser(@Path("id") id: String): User
}

// After (Ktor)
class ApiService(private val client: HttpClient) {
    suspend fun getUser(id: String): User {
        return client.get("$BASE_URL/users/$id").body()
    }
}
'''
                },
                'common_issues': [
                    'Different error handling',
                    'JSON serialization differences',
                    'Platform engine configuration'
                ],
                'solutions': [
                    'Use Kotlinx Serialization',
                    'Configure platform engines (OkHttp/Darwin)',
                    'Wrap Ktor exceptions in sealed class'
                ],
                'applicable_stages': ['planning', 'generation', 'testing'],
                'applicable_agents': ['planner', 'generator', 'evaluator'],
                'applicable_architectures': ['MVVM', 'MVI', 'Clean Architecture']
            },
            
            # Database
            {
                'id': 'room-to-sqldelight',
                'name': 'Room to SQLDelight',
                'description': 'Migrate Room database to SQLDelight',
                'category': 'database',
                'complexity': 'advanced',
                'kmp_compatibility': 'full',
                'android_dependency': 'androidx.room:room-runtime',
                'kmp_dependency': 'app.cash.sqldelight:runtime',
                'migration_guide': '''
1. Add SQLDelight plugin and dependencies
2. Convert @Entity to .sq files
3. Convert DAO to SQLDelight queries
4. Create platform-specific database drivers
''',
                'code_examples': {
                    'generation': '''
// Before (Room Entity)
@Entity
data class User(
    @PrimaryKey val id: String,
    val name: String
)

// After (SQLDelight)
// user.sq
CREATE TABLE User (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

// Before (Room DAO)
@Dao
interface UserDao {
    @Query("SELECT * FROM User WHERE id = :id")
    fun getUser(id: String): User?
}

// After (SQLDelight)
// user.sq
getUser:
SELECT * FROM User WHERE id = ?;
'''
                },
                'common_issues': [
                    'Schema migration complexity',
                    'Different query syntax',
                    'Coroutine support setup'
                ],
                'solutions': [
                    'Export Room schema first',
                    'Test queries incrementally',
                    'Use SQLDelight coroutines extension'
                ],
                'applicable_stages': ['planning', 'generation', 'testing'],
                'applicable_agents': ['planner', 'generator', 'evaluator'],
                'applicable_architectures': ['MVVM', 'Clean Architecture']
            },
            
            # Architecture
            {
                'id': 'viewmodel-to-shared',
                'name': 'ViewModel to Shared ViewModel',
                'description': 'Migrate Android ViewModel to shared KMP ViewModel',
                'category': 'architecture',
                'complexity': 'intermediate',
                'android_dependency': 'androidx.lifecycle:lifecycle-viewmodel-ktx',
                'kmp_dependency': 'org.jetbrains.kotlinx:kotlinx-coroutines-core',
                'migration_guide': '''
1. Replace ViewModel with class using StateFlow
2. Replace LiveData with StateFlow/SharedFlow
3. Remove Android lifecycle dependencies
4. Create platform-specific ViewModel factories if needed
''',
                'code_examples': {
                    'generation': '''
// Before (Android ViewModel)
class UserViewModel : ViewModel() {
    private val _user = MutableLiveData<User>()
    val user: LiveData<User> = _user
    
    fun loadUser(id: String) {
        viewModelScope.launch {
            _user.value = repository.getUser(id)
        }
    }
}

// After (Shared ViewModel)
class UserViewModel(private val repository: UserRepository) {
    private val _user = MutableStateFlow<User?>(null)
    val user: StateFlow<User?> = _user.asStateFlow()
    
    fun loadUser(id: String) {
        CoroutineScope(Dispatchers.Default).launch {
            _user.value = repository.getUser(id)
        }
    }
}
'''
                },
                'common_issues': [
                    'Lifecycle awareness lost',
                    'Different scope management',
                    'Platform-specific UI updates'
                ],
                'solutions': [
                    'Use lifecycle-aware coroutines on each platform',
                    'Create expect/actual for CoroutineScope',
                    'Collect flows in UI layer appropriately'
                ],
                'applicable_stages': ['planning', 'generation', 'testing'],
                'applicable_agents': ['planner', 'generator', 'evaluator'],
                'applicable_architectures': ['MVVM', 'MVI']
            },
            
            # Dependency Injection
            {
                'id': 'koin-kmp',
                'name': 'Koin for KMP',
                'description': 'Use Koin for dependency injection in KMP',
                'category': 'dependency_injection',
                'complexity': 'basic',
                'android_dependency': 'org.koin:koin-android',
                'kmp_dependency': 'org.koin:koin-core',
                'migration_guide': '''
1. Replace koin-android with koin-core
2. Update module definitions for KMP
3. Create platform-specific Koin initialization
4. Use Koin in common code
''',
                'code_examples': {
                    'generation': '''
// Before (Android Koin)
val appModule = module {
    viewModel { UserViewModel(get()) }
    single { UserRepository() }
}

// After (KMP Koin)
val appModule = module {
    factory { UserViewModel(get()) }
    single { UserRepository() }
}

// Platform initialization
// Android
startKoin { androidContext(context) }
// iOS
KoinApplication.init()
'''
                },
                'common_issues': [
                    'Different scope types',
                    'Platform initialization',
                    'Android-specific injections'
                ],
                'solutions': [
                    'Use factory instead of viewModel',
                    'Create expect/actual for Koin setup',
                    'Move Android-specific to android module'
                ],
                'applicable_stages': ['planning', 'generation'],
                'applicable_agents': ['planner', 'generator'],
                'applicable_architectures': ['MVVM', 'MVI', 'Clean Architecture']
            },
            
            # Serialization
            {
                'id': 'gson-to-kotlinx-serialization',
                'name': 'Gson to Kotlinx Serialization',
                'description': 'Migrate Gson JSON serialization to Kotlinx Serialization',
                'category': 'serialization',
                'complexity': 'basic',
                'android_dependency': 'com.google.code.gson:gson',
                'kmp_dependency': 'org.jetbrains.kotlinx:kotlinx-serialization-json',
                'migration_guide': '''
1. Add Kotlinx Serialization plugin
2. Add @Serializable to data classes
3. Replace Gson with Json
4. Handle custom serializers if needed
''',
                'code_examples': {
                    'generation': '''
// Before (Gson)
data class User(val id: String, val name: String)

val gson = Gson()
val json = gson.toJson(user)
val user = gson.fromJson(json, User::class.java)

// After (Kotlinx Serialization)
@Serializable
data class User(val id: String, val name: String)

val json = Json { ignoreUnknownKeys = true }
val jsonString = json.encodeToString(user)
val user = json.decodeFromString<User>(jsonString)
'''
                },
                'common_issues': [
                    'Different null handling',
                    'Custom type adapters',
                    'Date/time serialization'
                ],
                'solutions': [
                    'Configure Json builder appropriately',
                    'Create custom KSerializer',
                    'Use kotlinx-datetime for dates'
                ],
                'applicable_stages': ['planning', 'generation'],
                'applicable_agents': ['planner', 'generator'],
                'applicable_architectures': ['MVVM', 'MVI', 'Clean Architecture']
            },
            
            # Testing
            {
                'id': 'junit-to-kotlin-test',
                'name': 'JUnit to Kotlin Test',
                'description': 'Migrate JUnit tests to Kotlin Test for common code',
                'category': 'testing',
                'complexity': 'basic',
                'android_dependency': 'junit:junit',
                'kmp_dependency': 'org.jetbrains.kotlin:kotlin-test',
                'migration_guide': '''
1. Add kotlin-test dependency to commonTest
2. Replace JUnit assertions with Kotlin assertions
3. Move common tests to commonTest
4. Keep Android-specific tests in androidTest
''',
                'code_examples': {
                    'generation': '''
// Before (JUnit)
@Test
fun testUserCreation() {
    val user = User("1", "John")
    assertEquals("1", user.id)
    assertEquals("John", user.name)
}

// After (Kotlin Test)
@Test
fun testUserCreation() {
    val user = User("1", "John")
    assertEquals("1", user.id)
    assertEquals("John", user.name)
}
// Same syntax, different import!
'''
                },
                'common_issues': [
                    'Different assertion styles',
                    'Test runner configuration',
                    'Platform-specific test setup'
                ],
                'solutions': [
                    'Use kotlin.test assertions',
                    'Configure test tasks in Gradle',
                    'Use expect/actual for test helpers'
                ],
                'applicable_stages': ['testing', 'evaluation'],
                'applicable_agents': ['evaluator', 'refiner'],
                'applicable_architectures': ['MVVM', 'MVI', 'Clean Architecture']
            },
            
            # Platform
            {
                'id': 'expect-actual-fs',
                'name': 'Expect/Actual for File System',
                'description': 'Implement expect/actual for file system operations',
                'category': 'platform',
                'complexity': 'intermediate',
                'android_dependency': 'java.io.File',
                'kmp_dependency': None,
                'migration_guide': '''
1. Define expect interface in commonMain
2. Implement actual in androidMain
3. Implement actual in iosMain
4. Use interface in common code
''',
                'code_examples': {
                    'generation': '''
// commonMain
expect class FileSystem {
    fun read(path: String): String
    fun write(path: String, content: String)
}

// androidMain
actual class FileSystem {
    actual fun read(path: String): String {
        return File(path).readText()
    }
    actual fun write(path: String, content: String) {
        File(path).writeText(content)
    }
}

// iosMain
actual class FileSystem {
    actual fun read(path: String): String {
        return NSString.fileWithString(path)
    }
    actual fun write(path: String, content: String) {
        content.writeToFile(path, atomically: true, encoding: UTF8)
    }
}
'''
                },
                'common_issues': [
                    'Different file APIs',
                    'Path handling differences',
                    'Encoding issues'
                ],
                'solutions': [
                    'Abstract file operations',
                    'Use common path utilities',
                    'Specify encoding explicitly'
                ],
                'applicable_stages': ['generation', 'testing'],
                'applicable_agents': ['generator', 'evaluator'],
                'applicable_architectures': ['MVVM', 'MVI', 'Clean Architecture']
            }
        ]
    
    def _load_custom_skills(self):
        """Load custom skills from disk."""
        skills_file = os.path.join(self.skills_dir, 'skills.json')
        
        if os.path.exists(skills_file):
            try:
                with open(skills_file, 'r') as f:
                    data = json.load(f)
                
                for skill_data in data:
                    skill = Skill.from_dict(skill_data)
                    self.skills[skill.id] = skill
                
                logger.info(f"Loaded {len(self.skills) - len(self._get_builtin_skills())} custom skills")
            except Exception as e:
                logger.warning(f"Failed to load custom skills: {e}")
    
    def search(self, 
               query: Optional[str] = None,
               category: Optional[SkillCategory] = None,
               stage: Optional[MigrationStage] = None,
               agent: Optional[AgentType] = None,
               complexity: Optional[SkillComplexity] = None,
               dependency: Optional[str] = None) -> List[Skill]:
        """
        Search skills by various criteria.
        
        Args:
            query: Text search query
            category: Filter by category
            stage: Filter by applicable stage
            agent: Filter by applicable agent
            complexity: Filter by complexity
            dependency: Match against Android dependency
        
        Returns:
            List of matching skills, sorted by relevance
        """
        results = []
        
        for skill in self.skills.values():
            match = True
            
            # Text search
            if query:
                query_lower = query.lower()
                if not (query_lower in skill.name.lower() or 
                        query_lower in skill.description.lower() or
                        query_lower in skill.android_dependency.lower()):
                    match = False
            
            # Category filter
            if category and skill.category != category:
                match = False
            
            # Stage filter
            if stage and not skill.matches_context(stage=stage):
                match = False
            
            # Agent filter
            if agent and not skill.matches_context(agent=agent):
                match = False
            
            # Complexity filter
            if complexity and skill.complexity != complexity:
                match = False
            
            # Dependency filter
            if dependency and not skill.matches_context(dependency=dependency):
                match = False
            
            if match:
                results.append(skill)
        
        # Sort by success rate and usage count
        results.sort(key=lambda s: (s.success_rate, s.usage_count), reverse=True)
        
        return results
    
    def recommend(self, 
                  stage: MigrationStage,
                  agent: AgentType,
                  project_context: Dict) -> List[Skill]:
        """
        Recommend skills for a specific migration context.
        
        Args:
            stage: Current migration stage
            agent: Agent requesting recommendation
            project_context: Project characteristics
        
        Returns:
            List of recommended skills
        """
        recommendations = []
        
        architecture = project_context.get('architecture', '')
        dependencies = project_context.get('dependencies', [])
        
        # Find skills applicable to this stage and agent
        applicable_skills = self.search(stage=stage, agent=agent)
        
        # Boost skills matching project dependencies
        for skill in applicable_skills:
            score = skill.success_rate
            
            # Check if skill matches any project dependency
            for dep in dependencies:
                if skill.android_dependency in dep:
                    score += 0.5
                    break
            
            # Check if skill matches architecture
            if architecture in skill.applicable_architectures:
                score += 0.3
            
            recommendations.append((skill, score))
        
        # Sort by score
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        return [skill for skill, score in recommendations]
    
    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """Get skill by ID."""
        return self.skills.get(skill_id)
    
    def add_skill(self, skill: Skill):
        """Add a new skill."""
        self.skills[skill.id] = skill
        self._save_custom_skills()
        logger.info(f"Added skill: {skill.id}")
    
    def update_skill_usage(self, skill_id: str, success: bool):
        """Update skill usage statistics."""
        skill = self.skills.get(skill_id)
        if skill:
            skill.usage_count += 1
            
            # Update success rate (exponential moving average)
            alpha = 0.3
            skill.success_rate = alpha * (1.0 if success else 0.0) + (1 - alpha) * skill.success_rate
            
            self._save_custom_skills()
    
    def _save_custom_skills(self):
        """Save custom skills to disk."""
        builtin_ids = {s['id'] for s in self._get_builtin_skills()}
        custom_skills = [s.to_dict() for s in self.skills.values() if s.id not in builtin_ids]
        
        skills_file = os.path.join(self.skills_dir, 'skills.json')
        with open(skills_file, 'w') as f:
            json.dump(custom_skills, f, indent=2)
    
    def get_stats(self) -> Dict:
        """Get skills hub statistics."""
        return {
            'total_skills': len(self.skills),
            'by_category': {
                cat.value: sum(1 for s in self.skills.values() if s.category == cat)
                for cat in SkillCategory
            },
            'by_complexity': {
                comp.value: sum(1 for s in self.skills.values() if s.complexity == comp)
                for comp in SkillComplexity
            },
            'by_compatibility': {
                compat.value: sum(1 for s in self.skills.values() if s.kmp_compatibility == compat)
                for compat in KMPCompatibility
            }
        }
    
    def export_for_agent(self, stage: MigrationStage, agent: AgentType) -> str:
        """Export skills relevant to a specific agent and stage as a prompt."""
        skills = self.search(stage=stage, agent=agent)
        
        prompt = "# Available Skills\n\n"
        prompt += f"**Stage:** {stage.value}\n"
        prompt += f"**Agent:** {agent.value}\n"
        prompt += f"**Skills Available:** {len(skills)}\n\n"
        
        for skill in skills[:10]:  # Top 10 skills
            prompt += f"## {skill.name}\n"
            prompt += f"**ID:** `{skill.id}`\n"
            prompt += f"**Description:** {skill.description}\n"
            prompt += f"**Android:** `{skill.android_dependency}`\n"
            if skill.kmp_dependency:
                prompt += f"**KMP:** `{skill.kmp_dependency}`\n"
            prompt += f"**Complexity:** {skill.complexity.value}\n"
            prompt += f"**Compatibility:** {skill.kmp_compatibility.value}\n"
            
            if skill.migration_guide:
                prompt += f"\n**Migration Guide:**\n{skill.migration_guide}\n"
            
            if skill.common_issues:
                prompt += f"\n**Common Issues:**\n"
                for issue in skill.common_issues[:3]:
                    prompt += f"- {issue}\n"
            
            prompt += "\n---\n\n"
        
        return prompt


# Global skills hub instance
_hub: Optional[SkillsHub] = None

def get_skills_hub() -> SkillsHub:
    """Get global skills hub instance."""
    global _hub
    if not _hub:
        _hub = SkillsHub()
    return _hub
