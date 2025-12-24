#!/usr/bin/env python3

import sys
import argparse
from core import Phenom

def main():
    parser = argparse.ArgumentParser(description='Phenom - Advanced Personal AI Assistant')
    parser.add_argument('--mode', choices=['voice', 'text', 'hybrid'], 
                       default='hybrid',
                       help='Interaction mode (default: hybrid)')
    parser.add_argument('--ai-mode', choices=['local', 'cloud', 'hybrid'],
                       help='AI mode: local (Ollama), cloud (OpenRouter/OpenAI), or hybrid (local with cloud fallback)')
    parser.add_argument('--config', default='config/config.yaml',
                       help='Path to configuration file')
    
    args = parser.parse_args()
    
    try:
        phenom = Phenom(config_path=args.config)
        
        # Override AI mode if specified
        if args.ai_mode:
            print(f"🤖 Setting AI mode to: {args.ai_mode.upper()}")
            phenom.ai.mode = args.ai_mode
            if args.ai_mode == 'local':
                print("   Using: Local LLM (Ollama)")
            elif args.ai_mode == 'cloud':
                print("   Using: Cloud LLM (OpenRouter/OpenAI)")
            else:
                print("   Using: Hybrid (Local → Cloud fallback)")
        else:
            print(f"🤖 AI mode: {phenom.ai.mode.upper()}")
        
        print(f"💬 Interaction mode: {args.mode.upper()}")
        print()
        
        if args.mode == 'voice':
            phenom.run_voice_mode()
        elif args.mode == 'text':
            phenom.run_text_mode()
        else:
            phenom.run_hybrid_mode()
            
    except KeyboardInterrupt:
        print("\n\nShutting down Phenom...")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
