#!/usr/bin/env python3
"""
Test script for native_config_parser.py

Tests all 8 configurations to ensure correct parameter derivation.
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from carla_native_enhancement.native_config_parser import parse_native_enhance, build_config


def test_configuration(enhance_str, expected_desc):
    """Test a single configuration."""
    print(f"\n{'='*70}")
    print(f"Testing: {enhance_str}")
    print(f"Expected: {expected_desc}")
    print('='*70)
    
    try:
        tokens = parse_native_enhance(enhance_str)
        config = build_config(tokens)
        
        print(f"✓ Tokens: {config.tokens}")
        print(f"  - high_fps: {config.high_fps}")
        print(f"  - high_res: {config.high_res}")
        print(f"  - no_noise: {config.no_noise}")
        print(f"  - frame_rate: {config.frame_rate}Hz")
        print(f"  - fixed_delta_seconds: {config.fixed_delta_seconds}s")
        print(f"  - resolution: {config.camera_width}x{config.camera_height}")
        print(f"  - sensor_tick: {config.sensor_tick}s")
        print(f"  - motion_blur_intensity: {config.motion_blur_intensity}")
        print(f"  - lens_flare_intensity: {config.lens_flare_intensity}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("="*70)
    print("CARLA Native Enhancement Configuration Parser Test")
    print("="*70)
    
    test_cases = [
        ("none", "Baseline (20Hz, 800x600, default noise)"),
        ("", "Empty string (should default to 'none')"),
        ("high_fps", "High FPS only (40Hz, 800x600, default noise)"),
        ("high_res", "High resolution only (20Hz, 1600x1200, default noise)"),
        ("no_noise", "No noise only (20Hz, 800x600, no noise)"),
        ("gauss8", "Standalone gaussian noise (sigma=8)"),
        ("gauss16", "Standalone gaussian noise (sigma=16)"),
        ("high_fps,high_res", "High FPS + High resolution (40Hz, 1600x1200, default noise)"),
        ("high_fps,no_noise", "High FPS + No noise (40Hz, 800x600, no noise)"),
        ("high_res,no_noise", "High resolution + No noise (20Hz, 1600x1200, no noise)"),
        ("high_fps,high_res,no_noise", "All enhancements (40Hz, 1600x1200, no noise)"),
    ]
    
    passed = 0
    failed = 0
    
    for enhance_str, desc in test_cases:
        if test_configuration(enhance_str, desc):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"Test Results: {passed} passed, {failed} failed")
    print('='*70)
    
    # Test error cases
    print(f"\n{'='*70}")
    print("Testing Error Cases")
    print('='*70)
    
    error_cases = [
        ("invalid_token", "Should reject unknown token"),
        ("none,high_fps", "Should reject 'none' with other tokens"),
        ("high_fps,invalid", "Should reject unknown token in combination"),
        ("gauss8,high_fps", "Should reject gaussian noise token combined with other tokens"),
        ("gauss8,gauss16", "Should reject multiple gaussian noise tokens"),
    ]
    
    for enhance_str, desc in error_cases:
        print(f"\nTesting: {enhance_str}")
        print(f"Expected: {desc}")
        try:
            tokens = parse_native_enhance(enhance_str)
            config = build_config(tokens)
            print(f"✗ Should have raised ValueError but got: {config.tokens}")
        except ValueError as e:
            print(f"✓ Correctly raised ValueError: {e}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    print(f"\n{'='*70}")
    print("All tests completed!")
    print('='*70)


if __name__ == '__main__':
    main()
