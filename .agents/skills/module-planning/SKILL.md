---
name: module-planning
description: Creates phased development plans and roadmaps for StudyCore modules. Covers prioritization (Risk × Value × Dependencies), milestone planning, architecture stories (GitHub issues), progress tracking, and report generation. Use when planning a new module, prioritizing work, creating a roadmap, or tracking progress through implementation phases. Do NOT use for initial codebase analysis (use modular-decomposition) or domain modeling (use domain-modeling).
---

# Module Planning

Structured planning and roadmaps for implementing StudyCore modules.

## Core Concepts

### Phased Approach

**Phase 1: Analysis & Preparation**
- Component inventory and sizing
- Common component detection
- Dependency analysis

**Phase 2: Domain Organization**
- Domain identification
- Component grouping
- Namespace/module alignment

**Phase 3: Module Implementation**
- Module creation
- API boundary definition
- Integration testing

### Prioritization Factors

| Factor | Low = Easy | High = Hard |
|--------|-----------|-------------|
| **Risk** | Standalone, few deps | Core logic, high coupling |
| **Value** | Nice to have | Business-critical |
| **Dependencies** | Independent | Blocks other work |
| **Complexity** | Few components | Many components, unclear boundaries |

### Priority Score

```
Priority = (Value × 3) - (Risk × 2) - (Dependencies × 1)
Higher score = Higher priority
```

## Step-by-Step Process

### Step 1: Assess Current State

Check what's already done:
- [ ] Components identified and sized
- [ ] Common components analyzed
- [ ] Dependencies mapped
- [ ] Domains identified
- [ ] Any modules already extracted

**Output:** Current state assessment with what's done and remaining.

### Step 2: Prioritize Work

1. **Assess Risk:** Low/Medium/High for each work item
2. **Assess Value:** High/Medium/Low for each work item
3. **Assess Dependencies:** Independent/Dependent/Blocking
4. **Calculate Priority Score**

**Output:** Prioritized list of work items.

### Step 3: Create Phased Roadmap

Define phases with milestones:

```markdown
## Phased Roadmap

### Phase 1: Analysis & Preparation (Weeks 1-2)
**Goal:** Complete component analysis
**Milestones:**
- Week 1: Component inventory complete
- Week 2: Dependency analysis complete

### Phase 2: Domain Organization (Weeks 3-4)
**Goal:** Organize into domains
**Milestones:**
- Week 3: Domains identified
- Week 4: Namespace alignment complete

### Phase 3: Module Implementation (Weeks 5-8)
**Goal:** Extract and implement modules
**Milestones:**
- Week 6: First module complete
- Week 8: All modules implemented
```

### Step 4: Generate Architecture Stories

Create GitHub issues for tracking:

```markdown
## Issue: [Module Name] — [Phase]

**As a** developer, I need to [action]
**to support** [business need]
**so that** [benefit]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests pass

**Estimate:** [story points or time]
**Priority:** [High/Medium/Low]
**Dependencies:** [list]
```

### Step 5: Track Progress

Monitor through phases:
- Stories completed / in progress / not started
- Metrics: components identified, modules created, tests passing
- Blockers and risks

## Output Formats

### Progress Dashboard

```markdown
## Progress Dashboard

### Phase Completion
| Phase | Status | Progress | Blocker |
|-------|--------|----------|---------|
| Analysis | ✅ Complete | 100% | None |
| Domain Org | ⚠️ In Progress | 60% | None |
| Implementation | ❌ Not Started | 0% | Waiting on Domain Org |

### Story Completion
**Completed:** 5 (25%)
**In Progress:** 3 (15%)
**Not Started:** 12 (60%)

### Key Metrics
- Components Identified: 25
- Modules Created: 1
- Tests Passing: 16/16
```

### Prioritized Work Plan

```markdown
## Prioritized Work Plan

### High Priority (Do First)
1. **Complete Auth Module** (Priority: 9/10)
   - Risk: Low | Value: High | Dependencies: None

### Medium Priority (Do Next)
2. **Deadline Sync Service** (Priority: 7/10)
   - Risk: Medium | Value: High | Dependencies: Auth Module

### Low Priority (Do Later)
3. **Materials Processing Pipeline** (Priority: 5/10)
   - Risk: High | Value: High | Dependencies: Deadline Module
```

## Best Practices

### Do's ✅
- Start with analysis
- Prioritize low-risk, high-value work
- Create architecture stories for tracking
- Set clear milestones
- Track progress regularly

### Don'ts ❌
- Skip analysis
- Start implementation too early
- Ignore dependencies
- Create unrealistic timelines
- Skip progress tracking
