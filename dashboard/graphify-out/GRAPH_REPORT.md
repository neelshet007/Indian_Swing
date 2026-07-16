# Graph Report - C:\Indian_Swing\dashboard  (2026-07-16)

## Corpus Check
- 9 files · ~10,304 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 33 nodes · 30 edges · 10 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]

## God Nodes (most connected - your core abstractions)
1. `TradeDetail()` - 6 edges
2. `getConvictionClass()` - 2 edges
3. `RecCard()` - 2 edges
4. `fmt()` - 2 edges
5. `fmtPct()` - 2 edges
6. `fmtNum()` - 2 edges
7. `fmtCr()` - 2 edges
8. `fmtK()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `TradeDetail()` --calls--> `fmtCr()`  [EXTRACTED]
  C:\Indian_Swing\dashboard\src\pages\TradeDetail.jsx → C:\Indian_Swing\dashboard\src\pages\TradeDetail.jsx  _Bridges community 0 → community 2_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.33
Nodes (1): fmtCr()

### Community 1 - "Community 1"
Cohesion: 0.4
Nodes (0): 

### Community 2 - "Community 2"
Cohesion: 0.4
Nodes (5): fmt(), fmtK(), fmtNum(), fmtPct(), TradeDetail()

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (2): getConvictionClass(), RecCard()

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (0): 

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (0): 

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (0): 

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (0): 

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (0): 

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **Thin community `Community 7`** (2 nodes): `Stocks.jsx`, `Stocks()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (1 nodes): `vite.config.js`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (1 nodes): `main.jsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TradeDetail()` connect `Community 2` to `Community 0`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._