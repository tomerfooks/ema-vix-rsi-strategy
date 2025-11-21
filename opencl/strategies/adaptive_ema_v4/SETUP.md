# Setup Instructions for V4

The v4 strategy is ready but needs optimize.c to be fully adapted. Here's the quick way to get it working:

## Option 1: Quick Test (Simplified)
For now, you can test the v4 logic by temporarily modifying v2's parameters in the kernel call.

## Option 2: Full Implementation
The optimize.c file needs these changes from v2:

1. **Config struct** (line ~30): Already updated with 8 parameters
2. **load_config()** (line ~50-120): Needs all 3 intervals updated (1h/4h/1d)  
3. **Parameter iteration** (line ~580): Change from 6 to 8 parameters
4. **JSON export** (line ~200): Update parameter names
5. **Printf statements**: Update parameter display names

## Current Status

The KERNEL is complete and working. The optimize.c compilation infrastructure is 90% done but needs the parameter loop logic updated.

## Next Step

Due to the file's complexity (800 lines), I recommend:
1. Test if basic compilation works
2. Fix any remaining parameter mismatches
3. Or simplify to use base parameters without optimization first

The core v4 strategy logic (KAMA + ADX + RSI) is solid and should perform much better than v3.
