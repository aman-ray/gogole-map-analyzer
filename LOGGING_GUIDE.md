"""
LOGGING AND TROUBLESHOOTING GUIDE
==================================

This guide explains the new logging functionality and how to resolve the "0 results" issue.

LOGGING FEATURES
================

1. **Date-wise Log Files**:
   - Files created in `logs/` directory
   - Format: `tradescout_YYYY-MM-DD.log`
   - Automatic daily rotation (keeps 30 days)

2. **Log Levels**:
   - DEBUG: Detailed operation information
   - INFO: General application flow
   - WARNING: Non-fatal issues
   - ERROR: Serious problems

3. **Dual Output**:
   - User-facing messages still appear in console
   - Technical details logged to files
   - Errors/warnings shown in both places

USAGE EXAMPLES
==============

Basic usage with logging:
```bash
tradescout --center "Dublin, Ireland" --radius-km 5 --output results
```

Debug mode with verbose logging:
```bash
tradescout --center "53.3498,-6.2603" --radius-km 5 --log-level DEBUG --log-dir logs --output debug_results
```

View real-time logs:
```bash
tail -f logs/tradescout_$(date +%Y-%m-%d).log
```

TROUBLESHOOTING THE "0 RESULTS" ISSUE
=====================================

**ROOT CAUSE**: Missing Playwright browser installation

**SYMPTOMS**:
- Always getting 0 results
- Error messages about missing browser executable
- Logs show: "BrowserType.launch: Executable doesn't exist"

**SOLUTION**:
```bash
# Install the Playwright browser
playwright install chromium

# Then run your search
tradescout --center "Dublin, Ireland" --radius-km 5 --output test_search
```

**VERIFICATION**:
Check logs for successful browser initialization:
```bash
grep -i "browser" logs/tradescout_*.log
```

COMMON ERROR SCENARIOS
=====================

1. **Missing Browser**:
   - Error: "Executable doesn't exist"
   - Fix: `playwright install chromium`

2. **Geocoding Issues**:
   - Error: "Failed to geocode address"
   - Fix: Use coordinates instead: "53.3498,-6.2603"

3. **Network Issues**:
   - Error: "Failed to connect" or timeouts
   - Fix: Check internet connection, try --headless false for debugging

4. **Permission Issues**:
   - Error: "Cannot write to output directory"
   - Fix: Check directory permissions or use different output path

LOG FILE ANALYSIS
================

Important log patterns to look for:

**Success Indicators**:
- "Tradescout logging initialized"
- "Browser initialized"
- "Found: [Business Name]"
- "Export completed successfully"

**Warning Signs**:
- "Could not find listings panel"
- "Retrying ... search"
- "Duplicate business filtered"

**Error Indicators**:
- "Failed to search ... after 3 attempts"
- "Error processing listing"
- "Error searching ... in tile"

DEBUGGING TIPS
==============

1. **Enable Debug Logging**:
   ```bash
   tradescout --log-level DEBUG --center "Dublin" --radius-km 2 --max-results 5
   ```

2. **Check Browser Installation**:
   ```bash
   playwright install --help
   ```

3. **Test with Small Area**:
   ```bash
   tradescout --center "53.3498,-6.2603" --radius-km 1 --max-results 3 --max-runtime-min 2
   ```

4. **View Live Logs**:
   ```bash
   # In one terminal
   tradescout --center "Dublin" --radius-km 5 --output test
   
   # In another terminal
   tail -f logs/tradescout_$(date +%Y-%m-%d).log
   ```

BEST PRACTICES
==============

1. **Always check logs after runs**:
   ```bash
   ls -la logs/
   tail -20 logs/tradescout_$(date +%Y-%m-%d).log
   ```

2. **Use appropriate log levels**:
   - Production: INFO (default)
   - Debugging: DEBUG
   - Monitoring: WARNING

3. **Regular log cleanup**:
   - Logs auto-rotate after 30 days
   - Manual cleanup: `rm logs/tradescout_2024-*.log`

4. **Test with known coordinates**:
   - Dublin: "53.3498,-6.2603"
   - London: "51.5074,-0.1278"
   - Manchester: "53.4808,-2.2426"

PERFORMANCE MONITORING
======================

Check logs for performance metrics:
- Search timing information
- Number of tiles generated
- Businesses found per tile
- Export timing

Example log analysis:
```bash
# Count businesses found
grep "Found:" logs/tradescout_*.log | wc -l

# Check error rate
grep "ERROR" logs/tradescout_*.log | wc -l

# View search timing
grep "completed in" logs/tradescout_*.log
```
"""