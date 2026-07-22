# DXF Investigation Report for Door Detection

## 1. LAYERS IN DXF
Total layers: 77

Key layers found:
- Layer 'KAPI VE PENCERELER': 69 entities (all LINE type)
- Layer 'kap�': 156 entities (128 LINE, 12 ARC) - appears to be 'kapı' with encoding issues
- Layer 'k pencere': 313 entities (289 LINE, 21 LWPOLYLINE, 3 ARC)
- Layer 'pencere': 371 entities (116 LINE, 227 LWPOLYLINE, 28 ARC)
- Layer 'Duvar': 489 entities (244 LINE, 223 LWPOLYLINE)
- Many other layers containing LINE, LWPOLYLINE, and ARC entities

## 2. GEOMETRY TYPE COUNTS PER LAYER (Door-relevant layers)
- 'KAPI VE PENCERELER': LINE: 69
- 'kap�': LINE: 128, ARC: 12
- 'k pencere': LINE: 289, LWPOLYLINE: 21, ARC: 3
- 'pencere': LINE: 116, LWPOLYLINE: 227, ARC: 28
- '0': LINE: 397, LWPOLYLINE: 301, ARC: 42
- 'Duvar': LINE: 244, LWPOLYLINE: 223

## 3. POTENTIAL DOOR LAYERS
Multiple layers contain door-related geometry:
- 'k pencere' (313 entities, has door geometry: True)
- 'k g�r�n���n' (148 entities, has door geometry: True)
- 'k tarama' (1516 entities, has door geometry: True)
- 'pencere' (371 entities, has door geometry: True)
- 'G�r�neyen' (199 entities, has door geometry: True)
- 'korkuluk' (58 entities, has door geometry: True)
- 'CERCEVE' (713 entities, has door geometry: True)
- 'YAz�' (662 entities, has door geometry: True)
- 'Kolon' (190 entities, has door geometry: True)
- 'merdivenn' (500 entities, has door geometry: True)
- 'Duvar' (489 entities, has door geometry: True)
- 'kap�' (156 entities, has door geometry: True)
- 'mutfak tefri�' (16 entities, has door geometry: True)
- 'tefri�' (86 entities, has door geometry: True)
- 'k aks' (143 entities, has door geometry: True)
- 'k merd izd�' (2 entities, has door geometry: True)
- 'k ic olcu' (266 entities, has door geometry: True)
- 'KAKS' (30 entities, has door geometry: True)
- 'GORUNUS_6_TWA' (66 entities, has door geometry: True)
- 'YAZI' (139 entities, has door geometry: True)
- 'A-AREA-IDEN' (207 entities, has door geometry: True)
- 'Merdiven' (54 entities, has door geometry: True)
- 'tarama' (1301 entities, has door geometry: True)
- 'GOR1' (117 entities, has door geometry: True)
- '0' (896 entities, has door geometry: True)
- 'KAPI VE PENCERELER' (69 entities, has door geometry: True)
- 'YAZILAR' (46 entities, has door geometry: True)
- 'tefr�s' (1474 entities, has door geometry: True)
- And many others...

## 4. ANALYSIS OF CURRENT DETECTOR ISSUES

Current DOOR_LAYERS in detector:
- 'kapı'
- 'kapi'
- 'kapi___pencere'
- 'kapi ve pencereler'
- 'kapı ve pencereler'
- 'KAPI VE PENCERELER'

**Issues found:**

1. **Encoding Issues**: The layer name 'kap�' in the DXF appears to be 'kapı' with a special Turkish character (İ/ı) that may not be matching correctly due to encoding differences.

2. **Case Sensitivity**: While 'KAPI VE PENCERELER' exactly matches one of the entries in DOOR_LAYERS, there may be encoding or whitespace issues preventing proper matching.

3. **Layer Name Variations**: The investigation shows multiple potential door-related layers:
   - 'k pencere' (window layers - may contain door frames)
   - 'pencere' (window layers)
   - 'kap�' (likely 'kapı' - door layers)
   - 'KAPI VE PENCERELER' (exact match in DOOR_LAYERS)

4. **Geometry Types**: The 'KAPI VE PENCERELER' layer contains only LINE entities (69 lines), which should be detected by the current LINE processing logic.

## 5. RECOMMENDED DETECTION STRATEGY

Based on the investigation:

### Primary Issue:
The door detection is finding 209 raw candidates but detecting 0 doors, indicating the filtering is too strict or the matching is failing.

### Recommended Fixes:

1. **Improve Layer Matching**:
   - Use case-insensitive comparison for layer names
   - Handle Turkish character encoding properly
   - Consider adding variations like 'kapi', 'kapı', 'pencere', etc.

2. **Review Geometry Processing**:
   - The LINE processing logic may be filtering out valid door lines based on length constraints
   - Need to verify MIN_DOOR_WIDTH and MAX_DOOR_WIDTH parameters are appropriate for the DXF scale

3. **Enhanced Debugging**:
   - Add logging to see which entities are being filtered out and why
   - Check if wall matching is failing (no walls found within threshold)
   - Verify room assignment is working correctly

### Immediate Actions:
1. Verify that walls.json and rooms.json are being loaded correctly
2. Check that the WALL_LAYERS detection is working (currently looking for layer="wall")
3. Add debug output to see what's happening in the processing pipeline

The most likely issue is that either:
- Wall matching is failing (no walls found with layer="wall")
- Room assignment is failing (doors not inside any room boundary)
- Geometry filtering is too strict (door dimensions outside MIN/MAX bounds)