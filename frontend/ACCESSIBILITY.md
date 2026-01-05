# Accessibility Guidelines (WCAG 2.1 AA)

This document outlines the accessibility features and best practices implemented in the API Assistant application.

## Implemented Features

### 1. Keyboard Navigation
- All interactive elements are keyboard accessible
- Tab order follows logical page flow
- Focus indicators are visible on all focusable elements
- Skip links available for main content navigation

### 2. Screen Reader Support
- Semantic HTML elements used throughout
- ARIA labels and descriptions where needed
- Live regions for dynamic content updates
- Proper heading hierarchy (h1-h6)

### 3. Color and Contrast
- All text meets WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text)
- Color is not the only means of conveying information
- Focus indicators have sufficient contrast
- Error states use both color and icons

### 4. Forms and Inputs
- All form inputs have associated labels
- Error messages are descriptive and linked to inputs
- Required fields are clearly indicated
- Help text is available for complex inputs

### 5. Images and Media
- All images have alt text
- Decorative images use empty alt attributes
- Icons have accessible labels or are hidden from screen readers

## Component-Specific Accessibility

### Sessions Page
- Session status indicated by both color and text
- Filter buttons have clear labels
- Confirmation dialogs for destructive actions
- Loading states announced to screen readers

### Diagrams Page
- Diagram type selection is keyboard accessible
- Generate button has loading state indication
- Error messages are clear and actionable
- Diagram viewer has export options with keyboard access

### Navigation
- Current page is indicated in navigation
- Navigation items have descriptive labels
- Logo link returns to home page

## Testing

### Manual Testing Checklist
- [ ] Navigate entire app using only keyboard
- [ ] Test with screen reader (NVDA/JAWS/VoiceOver)
- [ ] Verify color contrast ratios
- [ ] Test with browser zoom at 200%
- [ ] Verify focus indicators are visible
- [ ] Test form validation messages
- [ ] Verify error recovery mechanisms

### Automated Testing
- Jest and React Testing Library tests include accessibility checks
- Playwright E2E tests verify keyboard navigation
- ESLint plugin for accessibility warnings

## Known Issues and Improvements

### Current Limitations
1. Some complex components may need additional ARIA attributes
2. Mobile responsiveness can be further improved
3. Some dynamic content updates could benefit from better announcements

### Planned Improvements
1. Add skip navigation links
2. Implement better focus management in modals
3. Add keyboard shortcuts documentation
4. Improve mobile touch target sizes

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## Contact

For accessibility issues or concerns, please file an issue in the repository.
