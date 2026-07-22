import re

with open('src/types.ts', 'r') as f:
    content = f.read()

# Let's just append the new types for our BIM Core
new_types = """

// ==========================================
// NEW BIM CORE MODEL TYPES (bim_model.json)
// ==========================================
export interface CoreSpace {
  id: string;
  uuid: string;
  area_raw: number;
  polygon: number[][]; // [x, y][]
  related_walls: string[];
  related_windows: string[];
  related_columns: string[];
  related_doors: string[];
  neighbors: string[];
}

export interface CoreWall {
  category: "WALL";
  wall_id: number;
  uuid: string;
  type: string; // "External Wall" | "Partition Wall"
  points: number[][]; // [[x,y], [x,y]]
  thickness: number; // in mm
  angle: number;
  related_spaces: string[];
}

export interface CoreWindow {
  category: "WINDOW";
  uuid: string;
  layer: string;
  points: number[][];
  width: number;
  parent_wall?: string;
}

export interface CoreColumn {
  category: "COLUMN";
  uuid: string;
  layer: string;
  points: number[][];
  closed: boolean;
  parent_spaces?: string[];
}

export interface CoreDoor {
  category: "DOOR";
  uuid: string;
  layer: string;
  points: number[][];
  width: number;
  parent_wall?: string;
}

export interface CoreBIMModel {
  metadata: any;
  spaces: CoreSpace[];
  walls: CoreWall[];
  windows: CoreWindow[];
  columns: CoreColumn[];
  doors: CoreDoor[];
}
"""

with open('src/types.ts', 'a') as f:
    f.write(new_types)
