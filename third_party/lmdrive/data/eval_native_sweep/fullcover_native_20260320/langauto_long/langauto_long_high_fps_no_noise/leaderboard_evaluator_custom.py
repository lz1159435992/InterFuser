#!/usr/bin/env python
import os

native_enhance = os.environ.get('NATIVE_ENHANCE', 'none')
frame_rate = 40.0 if 'high_fps' in native_enhance else 20.0
print(f"[LMDrive Native Enhancement] Setting frame rate to {frame_rate}Hz")

import leaderboard.leaderboard_evaluator as le
le.LeaderboardEvaluator.frame_rate = frame_rate

if __name__ == '__main__':
    le.main()
