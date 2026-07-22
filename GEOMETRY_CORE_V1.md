# Geometry Core v1 Specification

## Goals
- Provide a robust and extensible core for geometric data management.
- Ensure compatibility with various formats such as DXF, PDF, IFC, DWG, and Revit.
- Support long-term architectural goals including 7D geometry and BIM integration.

## Scope
This module will define the internal representation of geometrical entities in KaRar. It will serve as a foundation for higher-level modules like wall detection, room detection, semantic classification, topology analysis, and BIM generation.

## Responsibilities
- Represent geometric entities with sufficient metadata.
- Support transformations (translation, rotation, scaling).
- Maintain consistency across different file formats and geometric types.

## Supported Geometry Types
1. Line
2. Polyline
3. Arc
4. Circle

## Required Metadata
- **ID**: Unique identifier for each geometry object.
- **Source Format**: The format from which the geometry was extracted (e.g., DXF, PDF).
- **Layer**: Layer information in source file.
- **3D Coordinates** (x, y, z): Support 3D coordinates for accurate representation.
- **Bounding Box**: Define a bounding box that encapsulates the extent of the geometry.
- **GeometryType Enum**: Use an enumeration to define different types of geometries.
- **Source ID**: Unique identifier within the source format (e.g., DXF handle, IFC GUID).
- **Style Metadata**:
  - Layer
  - Color
  - Linetype
  - Lineweight

## Forbidden Responsibilities
- Include semantic or topological information directly in geometry objects.

## Module Dependencies
- **Parser**: Reads raw data and converts it into GeometryObjects.
- **Wall Detection, Room Detection**: Analyze geometric entities for structural insights.
- **Semantic Engine**: Classifies geometrical entities based on attributes.
- **Topology Analysis**: Evaluates spatial relationships among geometries.
- **BIM Core**: Generates a Building Information Model from the geometry data.

## Design Principles
- Maintain encapsulation and abstraction to ensure modularity.
- Support flexibility for future extensions (e.g., additional geometric types).
- Ensure performance and efficiency in data handling and processing.