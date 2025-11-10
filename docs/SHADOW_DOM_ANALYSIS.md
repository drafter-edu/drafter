# Shadow DOM Implementation Analysis for Drafter

## Executive Summary

This document explores the feasibility of using Shadow DOM to cleanly separate student CSS from Drafter's framework CSS, while ensuring JavaScript functionality remains intact.

## Current Architecture

### DOM Structure
```html
<body>
  <div id="drafter-root--">
    <div id="drafter-site--" class="drafter-site">
      <form id="drafter-form--" class="drafter-form">
        <div id="drafter-frame--" class="drafter-frame">
          <div id="drafter-header--" class="drafter-header"></div>
          <div id="drafter-body--" class="drafter-body">
            <!-- Student content here -->
          </div>
          <div id="drafter-footer--" class="drafter-footer"></div>
        </div>
        <div id="drafter-debug--" class="drafter-debug"></div>
      </form>
    </div>
  </div>
</body>
```

### CSS Specificity Solution
- Current approach: Changed from ID selectors (`#drafter-body--`) to class selectors (`.drafter-body`)
- Specificity: 400 → 10 points
- Students can now override with simple tag selectors

### JavaScript Dependencies
Key JavaScript functionality from `js/src/bridge/client.ts`:
1. `document.getElementById(BODY_ELEMENT_ID)` - Updates page content
2. `document.getElementById(FORM_ELEMENT_ID)` - Form submissions
3. Event listeners on root element - Navigation handling
4. `replaceHTML()` - Dynamic content updates

## Shadow DOM Approach

### Concept
Shadow DOM creates an encapsulated DOM subtree with style isolation:
- **Closed boundary**: Styles don't leak in or out
- **Style scoping**: Student CSS won't affect framework, framework CSS won't affect student content
- **DOM encapsulation**: JavaScript from outside can't easily access shadow DOM contents

### Proposed Architecture

#### Option 1: Shadow DOM for Student Content Only
```html
<body>
  <div id="drafter-root--">
    <div id="drafter-site--" class="drafter-site">
      <form id="drafter-form--" class="drafter-form">
        <div id="drafter-frame--" class="drafter-frame">
          <div id="drafter-header--" class="drafter-header"></div>
          <div id="drafter-body--" class="drafter-body">
            <!-- Shadow Root attached here -->
            #shadow-root (open)
              <style>/* Student CSS injected here */</style>
              <style>/* Theme CSS copied here */</style>
              <!-- Student content -->
          </div>
          <div id="drafter-footer--" class="drafter-footer"></div>
        </div>
      </form>
    </div>
  </div>
</body>
```

**Pros:**
- Framework structure remains accessible to JavaScript
- Student content completely isolated
- Student CSS can't accidentally break framework
- Theme CSS applied only to student content

**Cons:**
- Need to duplicate theme CSS into shadow root
- Event delegation from form might not work across shadow boundary
- More complex content updates

#### Option 2: Shadow DOM for Entire Site
```html
<body>
  <div id="drafter-root--">
    #shadow-root (open)
      <style>/* Framework CSS */</style>
      <style>/* Theme CSS */</style>
      <style>/* Student CSS */</style>
      <div id="drafter-site--" class="drafter-site">
        <!-- Entire site structure -->
      </div>
  </div>
</body>
```

**Pros:**
- Complete isolation from any external CSS
- Single style injection point
- Clean separation

**Cons:**
- Need to rewrite JavaScript to work within shadow root
- More invasive change to architecture
- Potential compatibility issues with Skulpt

## Implementation Considerations

### 1. JavaScript Compatibility

**Challenge:** `document.getElementById()` won't find elements inside shadow root

**Solution:** 
```typescript
// Store shadow root reference
const shadowRoot = document.getElementById('drafter-body--').shadowRoot;

// Update all DOM queries
const element = shadowRoot.getElementById(BODY_ELEMENT_ID);
```

**Required Changes:**
- Update `replaceHTML()` to work with shadow DOM
- Modify event listeners to use shadow root
- Update all `getElementById()` and `querySelector()` calls
- Ensure form submissions work across boundary

### 2. CSS Injection

**Current:** CSS added to `<head>` via `add_website_css()`

**With Shadow DOM:**
```python
# Python side - collect CSS
student_css = get_additional_css()

# JavaScript side - inject into shadow root
const style = document.createElement('style');
style.textContent = studentCSS;
shadowRoot.appendChild(style);
```

**Required Changes:**
- Modify CSS injection mechanism
- Ensure proper ordering: framework → theme → student
- Handle dynamic CSS updates

### 3. Event Handling

**Challenge:** Events from shadow DOM can bubble out, but need special handling

**Solution:**
```typescript
// Event delegation still works if listener is on host or ancestor
root.addEventListener('click', (e) => {
  // e.target will be the shadow host, not the actual element
  // Use e.composedPath() to get actual target
  const path = e.composedPath();
  const actualTarget = path[0];
});
```

### 4. Form Submissions

**Challenge:** Form inside shadow DOM

**Options:**
1. Keep form outside shadow root (current structure works)
2. Use custom form submission handling
3. Use `slot` elements to project content

**Recommended:** Keep form structure outside shadow root, only put page content inside

## Recommended Implementation Path

### Phase 1: Minimal Shadow DOM for Student Content

```typescript
// In client.ts - when updating body
const bodyElement = document.getElementById(BODY_ELEMENT_ID);

// Create shadow root if it doesn't exist
if (!bodyElement.shadowRoot) {
  bodyElement.attachShadow({ mode: 'open' });
}

const shadowRoot = bodyElement.shadowRoot;

// Inject CSS
const themeStyle = document.createElement('style');
themeStyle.textContent = getThemeCSS();
shadowRoot.appendChild(themeStyle);

const studentStyle = document.createElement('style');
studentStyle.textContent = getStudentCSS();
shadowRoot.appendChild(studentStyle);

// Update content
const contentContainer = document.createElement('div');
contentContainer.innerHTML = body;
shadowRoot.appendChild(contentContainer);
```

### Phase 2: Update Event Handling

```typescript
// Modify mountNavigation to work with shadow root
const mountNavigation = (hostElement: HTMLElement, callback: Function) => {
  const shadowRoot = hostElement.shadowRoot;
  
  const clickHandler = (e: MouseEvent) => {
    const path = e.composedPath();
    const target = path[0] as HTMLElement;
    
    // Handle navigation with composed path
    // ...
  };
  
  // Listen on shadow root
  shadowRoot.addEventListener('click', clickHandler);
};
```

### Phase 3: Update Python API

```python
# No changes needed - add_website_css() continues to work
# But CSS is injected into shadow root instead of <head>
```

## Benefits of Shadow DOM Approach

1. **Perfect CSS Isolation**
   - Student CSS cannot affect framework
   - Framework CSS cannot affect student content
   - Themes apply only to student content

2. **Cleaner Architecture**
   - Clear boundary between framework and content
   - Easier to reason about styling
   - No specificity wars

3. **Better Encapsulation**
   - Framework implementation hidden
   - Students work in isolated environment
   - More robust to external interference

## Challenges and Risks

1. **JavaScript Complexity**
   - Need to update many DOM queries
   - Event handling requires careful consideration
   - Potential bugs in transition

2. **Form Handling**
   - Forms don't work well across shadow boundaries
   - May need custom form submission
   - Could affect file uploads

3. **Browser Compatibility**
   - Shadow DOM well-supported in modern browsers
   - But may have edge cases
   - Need thorough testing

4. **Skulpt Integration**
   - Unclear how Skulpt will interact with shadow DOM
   - May need special handling
   - Requires extensive testing

5. **Development Complexity**
   - More complex debugging
   - DevTools support varies
   - Harder to inspect and modify

## Alternative: CSS Layers (Cascade Layers)

Modern alternative to Shadow DOM for style isolation:

```css
/* Framework styles */
@layer framework {
  .drafter-body {
    background: white;
  }
}

/* Theme styles */
@layer theme {
  body {
    color: #333;
  }
}

/* Student styles - highest priority, no @layer needed */
body {
  background: lightblue; /* This wins! */
}
```

**Pros:**
- No JavaScript changes needed
- Simpler implementation
- Better browser support
- Works with existing architecture

**Cons:**
- Not true isolation (just ordering)
- Student can still accidentally override framework
- Requires modern browsers (2022+)

## Recommendation

**Short Term:** Current class-based approach is good enough
- Specificity reduced from 400 → 10
- Students can override easily
- No architectural changes needed

**Medium Term:** Consider CSS Cascade Layers
- Add `@layer` to framework and theme CSS
- Keep student CSS outside layers
- Minimal changes, good isolation

**Long Term:** Shadow DOM if truly needed
- Only if CSS layers prove insufficient
- Requires significant refactoring
- But provides perfect isolation

## Proof of Concept Code

### Minimal Shadow DOM Implementation

```typescript
// In bridge/client.ts

class ShadowDOMManager {
  private shadowRoot: ShadowRoot | null = null;
  
  initialize(hostElement: HTMLElement) {
    if (!hostElement.shadowRoot) {
      this.shadowRoot = hostElement.attachShadow({ mode: 'open' });
      this.injectStyles();
    }
    return this.shadowRoot;
  }
  
  injectStyles() {
    // Framework CSS (minimal)
    const frameworkStyle = document.createElement('style');
    frameworkStyle.textContent = `
      :host {
        display: block;
      }
    `;
    this.shadowRoot.appendChild(frameworkStyle);
    
    // Theme CSS
    const themeStyle = document.createElement('style');
    themeStyle.textContent = this.getThemeCSS();
    this.shadowRoot.appendChild(themeStyle);
    
    // Student CSS
    const studentStyle = document.createElement('style');
    studentStyle.id = 'student-css';
    studentStyle.textContent = this.getStudentCSS();
    this.shadowRoot.appendChild(studentStyle);
  }
  
  updateContent(html: string) {
    if (!this.shadowRoot) return;
    
    // Preserve style elements
    const styles = Array.from(this.shadowRoot.querySelectorAll('style'));
    
    // Update content
    this.shadowRoot.innerHTML = '';
    styles.forEach(style => this.shadowRoot.appendChild(style));
    
    const container = document.createElement('div');
    container.innerHTML = html;
    this.shadowRoot.appendChild(container);
  }
  
  private getThemeCSS(): string {
    // Fetch from theme system
    return '';
  }
  
  private getStudentCSS(): string {
    // Fetch from student CSS
    return '';
  }
}

// Usage
const shadowManager = new ShadowDOMManager();
const bodyElement = document.getElementById(BODY_ELEMENT_ID);
shadowManager.initialize(bodyElement);
shadowManager.updateContent(pageHTML);
```

## Testing Requirements

If implementing Shadow DOM:

1. **Unit Tests**
   - CSS injection
   - Content updates
   - Event handling

2. **Integration Tests**
   - Form submissions
   - Navigation
   - File uploads

3. **Browser Tests**
   - Chrome, Firefox, Safari
   - Mobile browsers
   - Edge cases

4. **Skulpt Compatibility**
   - Ensure Python code works
   - Test with examples
   - Verify no regressions

## Conclusion

Shadow DOM is technically feasible but requires significant refactoring. The current class-based approach with reduced specificity is a pragmatic solution that achieves the main goal: allowing students to easily override styles.

**Next Steps:**
1. Evaluate if current solution is sufficient
2. If more isolation needed, try CSS Cascade Layers first
3. Only implement Shadow DOM if both previous approaches fail

The choice between these approaches should be driven by actual user needs and pain points rather than technical elegance.
