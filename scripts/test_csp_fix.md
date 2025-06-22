# 🔒 CSP Fix Validation Test

## Quick Test Script for Content Security Policy Fix

This script validates that the CSP fix is working correctly in generated analysis reports.

```bash
# Generate a test report
python scripts/bitaxe_analysis_generator.py --hours 48

# Check that CSP header is present
echo "Checking for CSP header in generated HTML..."
grep -n "Content-Security-Policy" generated_charts/*.html

# Verify specific CSP directives
echo "Validating CSP directives..."
grep -o "unsafe-eval" generated_charts/*.html  # Should find unsafe-eval
grep -o "cdnjs.cloudflare.com" generated_charts/*.html  # Should find CDN
```

## Browser Testing Checklist

When opening the generated HTML report in a browser:

- [ ] **No CSP errors** in browser developer console
- [ ] **3D surface plots** load and are interactive
- [ ] **Scatter plots** display correctly
- [ ] **Plotly.js controls** (zoom, rotate, pan) work
- [ ] **Responsive design** works on different screen sizes

## Expected CSP Header

The generated HTML should contain this meta tag:

```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self' https://cdnjs.cloudflare.com;">
```

## Troubleshooting

If CSP issues persist:

1. **Clear browser cache** and reload the page
2. **Check browser console** for any remaining CSP violations
3. **Verify CSP header** is present in HTML source
4. **Try different browser** to isolate browser-specific issues

## Security Note

The `unsafe-eval` directive is safe for local analysis reports because:
- Files are generated locally, not served from web
- No user input is eval'd
- Only trusted Plotly.js library uses eval()
- Limited to specific domain (cdnjs.cloudflare.com)
