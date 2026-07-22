"""
Semantic Floor Classifier

Advanced floor identification using comprehensive semantic understanding:
- TEXT and MTEXT entity analysis
- Drawing title detection
- Turkish and English architectural keywords
- Sheet layout analysis
- Relative position heuristics
- Scale information
- Layer name analysis

Goal: Eliminate "Unknown Floor" by providing robust classification with
validation reports explaining the reasoning behind each classification.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict, Counter
import math


class SemanticFloorClassifier:
    """
    Advanced semantic classifier for floor plan identification.
    Uses multiple signals to determine floor level with high confidence.
    """
    
    # Comprehensive Turkish keywords for floor identification
    TURKISH_KEYWORDS = {
        'ground_floor': [
            'zemin', 'zemin kat', 'zemin kati', 'giriş', 'giris', 'giriş kat',
            'bodrum üstü', 'bodrum ustu', 'kat 0', 'kat0', '0. kat', '0.kat'
        ],
        'first_floor': [
            '1. kat', '1.kat', 'birinci kat', 'birinci', 'bir kat', 'kat 1', 'kat1',
            '1 kat', '1kat', 'asma kat', 'normal kat'
        ],
        'second_floor': [
            '2. kat', '2.kat', 'ikinci kat', 'ikinci', 'iki kat', 'kat 2', 'kat2',
            '2 kat', '2kat'
        ],
        'third_floor': [
            '3. kat', '3.kat', 'üçüncü kat', 'ucuncu kat', 'üçüncü', 'ucuncu',
            'üç kat', 'uc kat', 'kat 3', 'kat3', '3 kat', '3kat'
        ],
        'fourth_floor': [
            '4. kat', '4.kat', 'dördüncü kat', 'dorduncu kat', 'dördüncü', 'dorduncu',
            'dört kat', 'dort kat', 'kat 4', 'kat4', '4 kat', '4kat'
        ],
        'basement': [
            'bodrum', 'bodrum kat', 'bodrum kati', 'zemin altı', 'zemin alti',
            'alt kat', 'kat -1', 'kat-1', '-1 kat', '-1. kat'
        ],
        'roof': [
            'çatı', 'cati', 'çatı planı', 'cati plani', 'çatı kat', 'cati kat',
            'teras', 'teras kat', 'üst örtü', 'ust ortu'
        ],
        'site_plan': [
            'vaziyet', 'vaziyet planı', 'vaziyet plani', 'yerleşim', 'yerlesim',
            'yerleşim planı', 'yerlesim plani', 'aplikasyon', 'uygulama'
        ]
    }
    
    # Comprehensive English keywords
    ENGLISH_KEYWORDS = {
        'ground_floor': [
            'ground', 'ground floor', 'g.f', 'gf', 'ground level', 'entry level',
            'level 0', 'level0', 'floor 0', 'floor0', 'main floor'
        ],
        'first_floor': [
            'first', 'first floor', '1st', '1st floor', 'level 1', 'level1',
            'floor 1', 'floor1', 'f1', 'mezzanine'
        ],
        'second_floor': [
            'second', 'second floor', '2nd', '2nd floor', 'level 2', 'level2',
            'floor 2', 'floor2', 'f2'
        ],
        'third_floor': [
            'third', 'third floor', '3rd', '3rd floor', 'level 3', 'level3',
            'floor 3', 'floor3', 'f3'
        ],
        'fourth_floor': [
            'fourth', 'fourth floor', '4th', '4th floor', 'level 4', 'level4',
            'floor 4', 'floor4', 'f4'
        ],
        'basement': [
            'basement', 'cellar', 'lower level', 'level -1', 'level-1',
            'floor -1', 'floor-1', 'underground'
        ],
        'roof': [
            'roof', 'roof plan', 'roof level', 'terrace', 'top floor',
            'penthouse', 'attic'
        ],
        'site_plan': [
            'site', 'site plan', 'plot', 'plot plan', 'location', 'location plan',
            'layout', 'master plan', 'context'
        ]
    }
    
    # Drawing type keywords (non-floor plans)
    ELEVATION_KEYWORDS = [
        'görünüş', 'gorunus', 'görünü', 'gorunu', 'elevation', 'facade',
        'cephe', 'view', 'ön', 'on', 'arka', 'yan', 'front', 'rear', 'side'
    ]
    
    SECTION_KEYWORDS = [
        'kesit', 'section', 'cut', 'a-a', 'b-b', 'c-c', 'd-d', 'e-e'
    ]
    
    DETAIL_KEYWORDS = [
        'detay', 'detail', 'node', 'junction', 'connection', 'ayrıntı', 'ayrinti'
    ]
    
    def __init__(self):
        """Initialize the semantic classifier"""
        self.classification_reasons = []  # Store reasoning for validation report
        
    def classify_floor(self, 
                      text_entities: List[Dict[str, Any]],
                      bounds: Dict[str, float],
                      layer_names: List[str],
                      entity_count: int,
                      relative_position: Optional[Dict[str, Any]] = None) -> Tuple[str, float, List[str]]:
        """
        Classify a floor drawing using comprehensive semantic analysis.
        
        Args:
            text_entities: List of TEXT/MTEXT entities with position and content
            bounds: Bounding box of the drawing region
            layer_names: List of layer names used in this region
            entity_count: Number of entities in the region
            relative_position: Optional position info relative to other drawings
            
        Returns:
            Tuple of (classification, confidence_score, reasoning_list)
        """
        self.classification_reasons = []
        scores = defaultdict(float)
        
        # 1. Analyze text entities (highest priority)
        text_score = self._analyze_text_entities(text_entities, bounds, scores)
        
        # 2. Analyze layer names
        layer_score = self._analyze_layer_names(layer_names, scores)
        
        # 3. Analyze drawing titles (large text near top)
        title_score = self._analyze_drawing_titles(text_entities, bounds, scores)
        
        # 4. Check for non-floor-plan types (elevation, section, detail)
        type_score = self._check_drawing_type(text_entities, layer_names, scores)
        
        # 5. Analyze relative position (if available)
        if relative_position:
            position_score = self._analyze_relative_position(relative_position, scores)
        
        # 6. Analyze scale information
        scale_score = self._analyze_scale_info(text_entities, scores)
        
        # 7. Apply geometric heuristics as fallback
        geometry_score = self._analyze_geometry(bounds, entity_count, scores)
        
        # Determine best classification
        if not scores:
            # Last resort: use position-based heuristics
            return self._fallback_classification(bounds, relative_position)
        
        # Get top classification
        best_classification = max(scores.items(), key=lambda x: x[1])
        classification = best_classification[0]
        confidence = min(best_classification[1] / 100.0, 1.0)  # Normalize to 0-1
        
        return classification, confidence, self.classification_reasons
    
    def _analyze_text_entities(self, text_entities: List[Dict[str, Any]], 
                               bounds: Dict[str, float], 
                               scores: Dict[str, float]) -> float:
        """
        Analyze TEXT and MTEXT entities for floor identification keywords.
        Uses proximity weighting - text closer to the drawing center scores higher.
        """
        if not text_entities:
            return 0.0
        
        center_x = (bounds['min_x'] + bounds['max_x']) / 2
        center_y = (bounds['min_y'] + bounds['max_y']) / 2
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        max_distance = math.sqrt(width**2 + height**2) / 2
        
        # Expand search area slightly
        margin = 500.0
        search_bounds = {
            'min_x': bounds['min_x'] - margin,
            'max_x': bounds['max_x'] + margin,
            'min_y': bounds['min_y'] - margin,
            'max_y': bounds['max_y'] + margin
        }
        
        total_score = 0.0
        matches_found = []
        
        for text_entity in text_entities:
            pos = text_entity['position']
            
            # Check if text is within search bounds
            if not (search_bounds['min_x'] <= pos['x'] <= search_bounds['max_x'] and
                   search_bounds['min_y'] <= pos['y'] <= search_bounds['max_y']):
                continue
            
            text = text_entity['text'].lower().strip()
            if not text:
                continue
            
            # Calculate proximity weight (closer = higher weight)
            dx = pos['x'] - center_x
            dy = pos['y'] - center_y
            distance = math.sqrt(dx**2 + dy**2)
            proximity_weight = 1.0 - min(distance / max_distance, 1.0)
            proximity_weight = max(proximity_weight, 0.3)  # Minimum weight
            
            # Size weight (larger text = more important)
            text_height = text_entity.get('height', 0)
            size_weight = min(text_height / 100.0, 2.0) if text_height > 0 else 1.0
            
            # Combined weight
            weight = proximity_weight * size_weight
            
            # Check Turkish keywords
            for floor_type, keywords in self.TURKISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        score = 50.0 * weight
                        scores[floor_type] += score
                        total_score += score
                        matches_found.append(f"Turkish keyword '{keyword}' in text '{text}' (weight: {weight:.2f})")
            
            # Check English keywords
            for floor_type, keywords in self.ENGLISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        score = 50.0 * weight
                        scores[floor_type] += score
                        total_score += score
                        matches_found.append(f"English keyword '{keyword}' in text '{text}' (weight: {weight:.2f})")
        
        if matches_found:
            self.classification_reasons.append(f"Text analysis: {len(matches_found)} keyword matches")
            for match in matches_found[:5]:  # Limit to top 5 for brevity
                self.classification_reasons.append(f"  - {match}")
        
        return total_score
    
    def _analyze_layer_names(self, layer_names: List[str], scores: Dict[str, float]) -> float:
        """Analyze layer names for floor identification clues"""
        if not layer_names:
            return 0.0
        
        total_score = 0.0
        matches_found = []
        
        for layer in layer_names:
            layer_lower = layer.lower()
            
            # Check Turkish keywords in layers
            for floor_type, keywords in self.TURKISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in layer_lower:
                        score = 20.0
                        scores[floor_type] += score
                        total_score += score
                        matches_found.append(f"Layer '{layer}' contains '{keyword}'")
            
            # Check English keywords in layers
            for floor_type, keywords in self.ENGLISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in layer_lower:
                        score = 20.0
                        scores[floor_type] += score
                        total_score += score
                        matches_found.append(f"Layer '{layer}' contains '{keyword}'")
        
        if matches_found:
            self.classification_reasons.append(f"Layer analysis: {len(matches_found)} matches")
            for match in matches_found[:3]:
                self.classification_reasons.append(f"  - {match}")
        
        return total_score
    
    def _analyze_drawing_titles(self, text_entities: List[Dict[str, Any]], 
                                bounds: Dict[str, float], 
                                scores: Dict[str, float]) -> float:
        """
        Detect and analyze drawing titles (typically large text at top or bottom of drawing).
        Titles have higher confidence than regular text.
        """
        if not text_entities:
            return 0.0
        
        # Find large text entities (potential titles)
        title_candidates = []
        for text_entity in text_entities:
            height = text_entity.get('height', 0)
            if height > 50:  # Large text
                pos = text_entity['position']
                # Check if near top or bottom of drawing
                y_pos = pos['y']
                if (y_pos > bounds['max_y'] - 1000 or  # Near top
                    y_pos < bounds['min_y'] + 1000):    # Near bottom
                    title_candidates.append(text_entity)
        
        total_score = 0.0
        titles_found = []
        
        for title in title_candidates:
            text = title['text'].lower().strip()
            
            # Check for floor keywords in titles (higher weight)
            for floor_type, keywords in self.TURKISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        score = 80.0  # High confidence for titles
                        scores[floor_type] += score
                        total_score += score
                        titles_found.append(f"Title '{text}' contains '{keyword}'")
            
            for floor_type, keywords in self.ENGLISH_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        score = 80.0
                        scores[floor_type] += score
                        total_score += score
                        titles_found.append(f"Title '{text}' contains '{keyword}'")
        
        if titles_found:
            self.classification_reasons.append(f"Drawing title analysis: {len(titles_found)} matches")
            for title in titles_found:
                self.classification_reasons.append(f"  - {title}")
        
        return total_score
    
    def _check_drawing_type(self, text_entities: List[Dict[str, Any]], 
                           layer_names: List[str], 
                           scores: Dict[str, float]) -> float:
        """
        Check if this is a non-floor-plan drawing type (elevation, section, detail).
        These should be classified differently.
        """
        all_text = ' '.join([t['text'].lower() for t in text_entities])
        all_layers = ' '.join(layer_names).lower()
        combined = all_text + ' ' + all_layers
        
        total_score = 0.0
        
        # Check for elevation
        elevation_matches = sum(1 for kw in self.ELEVATION_KEYWORDS if kw in combined)
        if elevation_matches > 0:
            score = 60.0 * elevation_matches
            scores['elevation'] += score
            total_score += score
            self.classification_reasons.append(f"Elevation indicators: {elevation_matches} matches")
        
        # Check for section
        section_matches = sum(1 for kw in self.SECTION_KEYWORDS if kw in combined)
        if section_matches > 0:
            score = 60.0 * section_matches
            scores['section'] += score
            total_score += score
            self.classification_reasons.append(f"Section indicators: {section_matches} matches")
        
        # Check for detail
        detail_matches = sum(1 for kw in self.DETAIL_KEYWORDS if kw in combined)
        if detail_matches > 0:
            score = 60.0 * detail_matches
            scores['detail'] += score
            total_score += score
            self.classification_reasons.append(f"Detail indicators: {detail_matches} matches")
        
        return total_score
    
    def _analyze_relative_position(self, relative_position: Dict[str, Any], 
                                   scores: Dict[str, float]) -> float:
        """
        Analyze relative position of drawing among other drawings.
        Floor plans are typically arranged vertically (bottom to top) or horizontally (left to right).
        """
        if not relative_position:
            return 0.0
        
        total_drawings = relative_position.get('total_drawings', 1)
        position_index = relative_position.get('position_index', 0)
        layout = relative_position.get('layout', 'unknown')  # 'vertical' or 'horizontal'
        
        if total_drawings <= 1:
            return 0.0
        
        # Heuristic: In vertical layout, bottom = ground, top = roof
        # In horizontal layout, left = ground, right = roof
        position_ratio = position_index / (total_drawings - 1) if total_drawings > 1 else 0.5
        
        score = 15.0  # Moderate confidence
        
        if position_ratio < 0.2:  # First drawing
            scores['ground_floor'] += score
            self.classification_reasons.append(f"Position: First drawing in {layout} layout")
        elif position_ratio > 0.8:  # Last drawing
            scores['roof'] += score
            self.classification_reasons.append(f"Position: Last drawing in {layout} layout")
        elif position_ratio < 0.4:
            scores['first_floor'] += score
            self.classification_reasons.append(f"Position: Early in {layout} layout")
        elif position_ratio < 0.6:
            scores['second_floor'] += score
            self.classification_reasons.append(f"Position: Middle in {layout} layout")
        
        return score
    
    def _analyze_scale_info(self, text_entities: List[Dict[str, Any]], 
                           scores: Dict[str, float]) -> float:
        """
        Analyze scale information in text.
        Floor plans typically have scales like 1:50, 1:100, 1:200.
        Site plans have smaller scales like 1:500, 1:1000.
        Details have larger scales like 1:10, 1:20.
        """
        scale_pattern = re.compile(r'1\s*[:/-]\s*(\d+)')
        
        for text_entity in text_entities:
            text = text_entity['text']
            match = scale_pattern.search(text)
            
            if match:
                scale_value = int(match.group(1))
                
                if scale_value >= 500:  # Site plan scale
                    scores['site_plan'] += 30.0
                    self.classification_reasons.append(f"Scale 1:{scale_value} indicates site plan")
                    return 30.0
                elif scale_value <= 20:  # Detail scale
                    scores['detail'] += 30.0
                    self.classification_reasons.append(f"Scale 1:{scale_value} indicates detail")
                    return 30.0
                else:  # Floor plan scale (1:50 to 1:200)
                    # Don't add score, but note it
                    self.classification_reasons.append(f"Scale 1:{scale_value} consistent with floor plan")
        
        return 0.0
    
    def _analyze_geometry(self, bounds: Dict[str, float], 
                         entity_count: int, 
                         scores: Dict[str, float]) -> float:
        """
        Analyze geometric properties as fallback heuristics.
        """
        width = bounds['max_x'] - bounds['min_x']
        height = bounds['max_y'] - bounds['min_y']
        area = width * height
        aspect_ratio = width / height if height > 0 else 1.0
        
        score = 5.0  # Low confidence
        
        # Very small drawings are likely details
        if area < 500000:
            scores['detail'] += score
            self.classification_reasons.append(f"Small area ({area:.0f}) suggests detail")
            return score
        
        # Very wide drawings might be elevations
        if aspect_ratio > 4.0:
            scores['elevation'] += score
            self.classification_reasons.append(f"Wide aspect ratio ({aspect_ratio:.2f}) suggests elevation")
            return score
        
        # Tall narrow drawings might be sections
        if aspect_ratio < 0.5:
            scores['section'] += score
            self.classification_reasons.append(f"Tall aspect ratio ({aspect_ratio:.2f}) suggests section")
            return score
        
        return 0.0
    
    def _fallback_classification(self, bounds: Dict[str, float], 
                                relative_position: Optional[Dict[str, Any]]) -> Tuple[str, float, List[str]]:
        """
        Last resort classification when no clear signals are found.
        Uses position-based heuristics.
        """
        reasons = ["No clear text or layer indicators found"]
        
        # Use relative position if available
        if relative_position:
            total_drawings = relative_position.get('total_drawings', 1)
            position_index = relative_position.get('position_index', 0)
            
            if total_drawings > 1:
                position_ratio = position_index / (total_drawings - 1)
                
                if position_ratio < 0.3:
                    reasons.append("Fallback: First position suggests ground floor")
                    return 'ground_floor', 0.3, reasons
                elif position_ratio < 0.5:
                    reasons.append("Fallback: Early position suggests first floor")
                    return 'first_floor', 0.3, reasons
                elif position_ratio < 0.7:
                    reasons.append("Fallback: Middle position suggests second floor")
                    return 'second_floor', 0.3, reasons
                else:
                    reasons.append("Fallback: Late position suggests upper floor or roof")
                    return 'roof', 0.3, reasons
        
        # Absolute fallback: assume ground floor (most common)
        reasons.append("Absolute fallback: Defaulting to ground floor (most common)")
        return 'ground_floor', 0.2, reasons
    
    def normalize_classification(self, classification: str) -> str:
        """
        Convert internal classification codes to human-readable labels.
        """
        mapping = {
            'ground_floor': 'Ground Floor',
            'first_floor': 'First Floor',
            'second_floor': 'Second Floor',
            'third_floor': 'Third Floor',
            'fourth_floor': 'Fourth Floor',
            'basement': 'Basement',
            'roof': 'Roof Plan',
            'site_plan': 'Site Plan',
            'elevation': 'Elevation',
            'section': 'Section',
            'detail': 'Detail'
        }
        return mapping.get(classification, classification.replace('_', ' ').title())


def generate_validation_report(classifications: List[Dict[str, Any]], 
                               output_path: str) -> None:
    """
    Generate a detailed validation report showing why each classification was chosen.
    
    Args:
        classifications: List of classification results with reasoning
        output_path: Path to save the report
    """
    import json
    
    report = {
        'total_drawings': len(classifications),
        'classification_summary': {},
        'detailed_results': []
    }
    
    # Count classifications
    classification_counts = Counter()
    for result in classifications:
        classification_counts[result['classification']] += 1
    
    report['classification_summary'] = dict(classification_counts)
    
    # Add detailed results
    for i, result in enumerate(classifications, 1):
        detailed = {
            'drawing_index': i,
            'classification': result['classification'],
            'confidence': result['confidence'],
            'bounds': result.get('bounds', {}),
            'reasoning': result.get('reasoning', []),
            'text_samples': result.get('text_samples', [])[:10],  # First 10 text samples
            'layer_samples': result.get('layer_samples', [])[:10]  # First 10 layers
        }
        report['detailed_results'].append(detailed)
    
    # Save report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nValidation report saved to {output_path}")
    print(f"\nClassification Summary:")
    for classification, count in classification_counts.most_common():
        print(f"  {classification}: {count} drawing(s)")
