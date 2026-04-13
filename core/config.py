"""
Configuration System for KMP Migration

Centralized configuration for all user-customizable settings.

Usage:
    from core.config import MigrationConfig, load_config, save_config
    
    # Load or create config
    config = load_config()
    
    # Customize
    config.llm_provider = 'dashscope'
    config.llm_model = 'qwen-max'
    config.dry_run = False
    
    # Save
    save_config(config)
    
    # Or use in migration
    from orchestrator import run_orchestrator
    run_orchestrator('/path/to/project', config=config)
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OLLAMA = "ollama"
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"  # No LLM, mock responses


class MigrationMode(Enum):
    """Migration execution modes."""
    FULL = "full"  # All phases
    ANALYSIS_ONLY = "analysis_only"  # Just analyze, don't migrate
    MIGRATION_ONLY = "migration_only"  # Skip analysis and testing
    DRY_RUN = "dry_run"  # Simulate without writing files


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider = LLMProvider.OLLAMA
    model: str = "qwen2.5-coder:7b"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout_seconds: int = 60
    
    def to_dict(self) -> Dict:
        return {
            'provider': self.provider.value,
            'model': self.model,
            'api_key': '***' if self.api_key else None,  # Mask in output
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'timeout_seconds': self.timeout_seconds
        }


@dataclass
class MigrationConfig:
    """Main migration configuration."""
    
    # Project paths
    project_path: str = ""
    output_path: Optional[str] = None  # Default: project_path/migrated_kmp_project
    
    # LLM settings
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Migration settings
    mode: MigrationMode = MigrationMode.FULL
    dry_run: bool = True  # Don't create git commits
    check_health: bool = True  # Check LLM health before migration
    
    # Batch settings
    batch_size: int = 10  # Max files per batch
    enable_batch_migration: bool = True
    
    # Testing settings
    enable_testing: bool = True
    enable_llm_judge: bool = True
    enable_multimodal: bool = True
    
    # Learning settings
    enable_learning: bool = True
    knowledge_base_path: Optional[str] = None
    
    # Delivery settings
    enable_delivery: bool = False  # Disabled by default
    git_branch: str = "kmp-migration"
    create_pr: bool = False
    
    # Logging
    verbose: bool = False
    log_file: Optional[str] = None
    
    # Custom mappings (Android → KMP libraries)
    library_mappings: Dict[str, str] = field(default_factory=dict)
    
    # File patterns to skip
    skip_patterns: List[str] = field(default_factory=lambda: [
        'build/',
        '.gradle/',
        'gradle/',
        '*.java'  # Skip Java files by default
    ])
    
    # File patterns to include (override skip)
    include_patterns: List[str] = field(default_factory=lambda: [
        '*.kt',
        '*.kts'
    ])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary (safe for JSON)."""
        return {
            'project_path': self.project_path,
            'output_path': self.output_path,
            'llm': self.llm.to_dict(),
            'mode': self.mode.value,
            'dry_run': self.dry_run,
            'check_health': self.check_health,
            'batch_size': self.batch_size,
            'enable_batch_migration': self.enable_batch_migration,
            'enable_testing': self.enable_testing,
            'enable_llm_judge': self.enable_llm_judge,
            'enable_multimodal': self.enable_multimodal,
            'enable_learning': self.enable_learning,
            'enable_delivery': self.enable_delivery,
            'git_branch': self.git_branch,
            'create_pr': self.create_pr,
            'verbose': self.verbose,
            'log_file': self.log_file,
            'library_mappings': self.library_mappings,
            'skip_patterns': self.skip_patterns,
            'include_patterns': self.include_patterns
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MigrationConfig':
        """Create from dictionary."""
        config = cls()
        
        if 'project_path' in data:
            config.project_path = data['project_path']
        if 'output_path' in data:
            config.output_path = data['output_path']
        
        # LLM config
        if 'llm' in data:
            llm_data = data['llm']
            config.llm.provider = LLMProvider(llm_data.get('provider', 'ollama'))
            config.llm.model = llm_data.get('model', 'qwen2.5-coder:7b')
            config.llm.base_url = llm_data.get('base_url')
            config.llm.temperature = llm_data.get('temperature', 0.3)
            config.llm.max_tokens = llm_data.get('max_tokens', 4096)
            config.llm.timeout_seconds = llm_data.get('timeout_seconds', 60)
            # Don't load API key from file for security
        
        if 'mode' in data:
            config.mode = MigrationMode(data.get('mode', 'full'))
        if 'dry_run' in data:
            config.dry_run = data['dry_run']
        if 'check_health' in data:
            config.check_health = data['check_health']
        if 'batch_size' in data:
            config.batch_size = data['batch_size']
        if 'enable_batch_migration' in data:
            config.enable_batch_migration = data['enable_batch_migration']
        if 'enable_testing' in data:
            config.enable_testing = data['enable_testing']
        if 'enable_llm_judge' in data:
            config.enable_llm_judge = data['enable_llm_judge']
        if 'enable_multimodal' in data:
            config.enable_multimodal = data['enable_multimodal']
        if 'enable_learning' in data:
            config.enable_learning = data['enable_learning']
        if 'enable_delivery' in data:
            config.enable_delivery = data['enable_delivery']
        if 'git_branch' in data:
            config.git_branch = data['git_branch']
        if 'create_pr' in data:
            config.create_pr = data['create_pr']
        if 'verbose' in data:
            config.verbose = data['verbose']
        if 'log_file' in data:
            config.log_file = data['log_file']
        if 'library_mappings' in data:
            config.library_mappings = data['library_mappings']
        if 'skip_patterns' in data:
            config.skip_patterns = data['skip_patterns']
        if 'include_patterns' in data:
            config.include_patterns = data['include_patterns']
        
        return config


# Config file location
CONFIG_DIR = os.path.expanduser('~/.hermes/kmp-migration')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')


def load_config(config_path: Optional[str] = None) -> MigrationConfig:
    """
    Load configuration from file or create default.
    
    Args:
        config_path: Custom config file path (default: ~/.hermes/kmp-migration/config.json)
    
    Returns:
        MigrationConfig object
    """
    path = config_path or CONFIG_FILE
    
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                config = MigrationConfig.from_dict(data)
                logger.info(f"Loaded config from {path}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load config: {e}. Using defaults.")
    
    # Create default config
    config = MigrationConfig()
    logger.info("Using default configuration")
    return config


def save_config(config: MigrationConfig, config_path: Optional[str] = None):
    """
    Save configuration to file.
    
    Args:
        config: MigrationConfig object
        config_path: Custom config file path (default: ~/.hermes/kmp-migration/config.json)
    """
    path = config_path or CONFIG_FILE
    
    # Create directory if needed
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(config.to_dict(), f, indent=2)
    
    logger.info(f"Saved config to {path}")


def create_config_wizard() -> MigrationConfig:
    """
    Interactive configuration wizard.
    
    Returns:
        MigrationConfig object with user-provided values
    """
    print("\n" + "="*60)
    print("KMP MIGRATION CONFIGURATION WIZARD")
    print("="*60)
    print("\nThis will help you configure the migration framework.\n")
    print("Press Enter to use default values.\n")
    
    config = MigrationConfig()
    
    # Project path
    project_path = input(f"Project path [{config.project_path}]: ").strip()
    if project_path:
        config.project_path = project_path
    
    # LLM Provider
    print("\n--- LLM Configuration ---")
    print("Available providers:")
    print("  1. ollama (local, free)")
    print("  2. dashscope (Alibaba Cloud)")
    print("  3. openai (OpenAI)")
    print("  4. anthropic (Anthropic)")
    print("  5. mock (no LLM, for testing)")
    
    provider_choice = input(f"\nSelect provider [{config.llm.provider.value}]: ").strip()
    if provider_choice:
        provider_map = {
            '1': 'ollama',
            '2': 'dashscope',
            '3': 'openai',
            '4': 'anthropic',
            '5': 'mock',
            'ollama': 'ollama',
            'dashscope': 'dashscope',
            'openai': 'openai',
            'anthropic': 'anthropic',
            'mock': 'mock'
        }
        if provider_choice in provider_map:
            config.llm.provider = LLMProvider(provider_map[provider_choice])
    
    # Model
    model = input(f"Model name [{config.llm.model}]: ").strip()
    if model:
        config.llm.model = model
    
    # API Key (if not mock/ollama)
    if config.llm.provider not in [LLMProvider.OLLAMA, LLMProvider.MOCK]:
        api_key = input("API key [from environment]: ").strip()
        if api_key:
            config.llm.api_key = api_key
        else:
            # Try to load from environment
            env_vars = {
                LLMProvider.DASHSCOPE: 'DASHSCOPE_API_KEY',
                LLMProvider.OPENAI: 'OPENAI_API_KEY',
                LLMProvider.ANTHROPIC: 'ANTHROPIC_API_KEY'
            }
            env_var = env_vars.get(config.llm.provider)
            if env_var:
                config.llm.api_key = os.environ.get(env_var)
    
    # Migration mode
    print("\n--- Migration Mode ---")
    print("  1. full (all phases)")
    print("  2. analysis_only (just analyze)")
    print("  3. dry_run (simulate)")
    
    mode_choice = input(f"\nSelect mode [{config.mode.value}]: ").strip()
    if mode_choice:
        mode_map = {
            '1': 'full',
            '2': 'analysis_only',
            '3': 'dry_run'
        }
        if mode_choice in mode_map:
            config.mode = MigrationMode(mode_map[mode_choice])
    
    # Dry run
    dry_run = input(f"Dry run (no git commits) [{config.dry_run}]: ").strip()
    if dry_run:
        config.dry_run = dry_run.lower() in ['true', 'yes', 'y', '1']
    
    # Testing
    print("\n--- Testing Options ---")
    testing = input(f"Enable testing [{config.enable_testing}]: ").strip()
    if testing:
        config.enable_testing = testing.lower() in ['true', 'yes', 'y', '1']
    
    llm_judge = input(f"Enable LLM-as-a-Judge [{config.enable_llm_judge}]: ").strip()
    if llm_judge:
        config.enable_llm_judge = llm_judge.lower() in ['true', 'yes', 'y', '1']
    
    # Save config
    save_config = input(f"\nSave configuration? [yes]: ").strip().lower()
    if save_config not in ['no', 'n', 'false', '0']:
        save_config_file(config)
        print(f"\n✓ Configuration saved to {CONFIG_FILE}")
        print("  Run 'kmp-migrate' to use this configuration")
    
    return config


def save_config_file(config: MigrationConfig):
    """Save config to standard location."""
    save_config(config)


def print_config(config: MigrationConfig):
    """Print current configuration."""
    print("\n" + "="*60)
    print("CURRENT CONFIGURATION")
    print("="*60)
    
    print(f"\nProject Path: {config.project_path or 'Not set'}")
    print(f"Output Path: {config.output_path or 'Default (migrated_kmp_project/)'}")
    
    print(f"\n--- LLM ---")
    print(f"  Provider: {config.llm.provider.value}")
    print(f"  Model: {config.llm.model}")
    print(f"  API Key: {'***' if config.llm.api_key else 'Not set'}")
    print(f"  Base URL: {config.llm.base_url or 'Default'}")
    
    print(f"\n--- Migration ---")
    print(f"  Mode: {config.mode.value}")
    print(f"  Dry Run: {config.dry_run}")
    print(f"  Check Health: {config.check_health}")
    print(f"  Batch Size: {config.batch_size}")
    
    print(f"\n--- Testing ---")
    print(f"  Enable Testing: {config.enable_testing}")
    print(f"  LLM-as-a-Judge: {config.enable_llm_judge}")
    print(f"  Multi-Modal: {config.enable_multimodal}")
    
    print(f"\n--- Learning ---")
    print(f"  Enable Learning: {config.enable_learning}")
    
    print(f"\n--- Delivery ---")
    print(f"  Enable Delivery: {config.enable_delivery}")
    print(f"  Git Branch: {config.git_branch}")
    print(f"  Create PR: {config.create_pr}")
    
    if config.library_mappings:
        print(f"\n--- Library Mappings ---")
        for android_lib, kmp_lib in config.library_mappings.items():
            print(f"  {android_lib} → {kmp_lib}")
    
    if config.skip_patterns:
        print(f"\n--- Skip Patterns ---")
        for pattern in config.skip_patterns[:5]:
            print(f"  {pattern}")
        if len(config.skip_patterns) > 5:
            print(f"  ... and {len(config.skip_patterns) - 5} more")
    
    print("\n" + "="*60)


# CLI command
def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='KMP Migration Configuration')
    parser.add_argument('--wizard', action='store_true', help='Run configuration wizard')
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--reset', action='store_true', help='Reset to default configuration')
    parser.add_argument('--config', type=str, help='Custom config file path')
    
    args = parser.parse_args()
    
    if args.wizard:
        create_config_wizard()
    elif args.show:
        config = load_config(args.config)
        print_config(config)
    elif args.reset:
        if input("Reset configuration to defaults? [yes]: ").strip().lower() in ['yes', 'y']:
            config = MigrationConfig()
            save_config(config, args.config)
            print("✓ Configuration reset to defaults")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
