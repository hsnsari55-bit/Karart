export interface Point {
  x: number;
  y: number;
  z?: number;
}

export interface Point3D {
  x: number;
  y: number;
  z: number;
}

export interface CADEntity {
  id: string;
  type: "LINE" | "ARC" | "COLUMN" | "DOOR" | "WINDOW";
  layer: "duvar" | "kolon" | "kapı" | "k pencere" | "aks";
  start: Point;
  end: Point;
  thickness?: number; // for walls/columns
  radius?: number;    // for arcs
  angle?: number;
  width?: number;     // for doors/windows
  doorType?: "Single" | "Double" | "Sliding";
  status?: "original" | "snapped" | "merged";
}

export interface Room {
  id: string;
  name: string;
  type: string;
  area: number; // m²
  color: string;
  points: Point[]; // Polygon boundaries
}

export interface Floor {
  id: string;
  name: string;
  elevation: string;
  entityCount: number;
  area: number;
  rooms: Room[];
  entities: CADEntity[];
}

export type PipelineStepId = "parsing" | "geometry" | "semantic" | "topology";

export interface PipelineStep {
  id: PipelineStepId;
  title: string;
  subtitle: string;
  description: string;
  icon: string;
  status: "idle" | "running" | "completed";
  duration: number; // ms
  insights: string[];
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
  isError?: boolean;
  stepId?: string;
  statusCode?: number;
}

// ==========================================
// CANONICAL BIM MODEL (Target KaRar Architecture)
// ==========================================

export interface BIMWall {
  id: string;
  type: "exterior" | "interior";
  axis: {
    start: Point;
    end: Point;
  };
  profile: {
    thickness: number;
    height: number;
  };
  extrusion: {
    length: number;
    angle: number;
  };
  mesh: {
    position: Point3D;
    rotation: Point3D; // Pitch, Yaw, Roll
    size: {
      width: number;
      height: number;
      depth: number;
    };
  };
}

export interface BIMColumn {
  id: string;
  position: Point;
  height: number;
  size: number;
  mesh: {
    position: Point3D;
    size: {
      width: number;
      height: number;
      depth: number;
    };
  };
}

export interface BIMDoor {
  id: string;
  hinge: "left" | "right";
  openingDirection: "inward" | "outward";
  swingAngle: number; // Swing opening angle in degrees
  width: number;
  height: number;
  mesh: {
    position: Point3D;
    rotation: Point3D;
  };
}

export interface BIMWindow {
  id: string;
  width: number;
  height: number;
  sillHeight: number; // Elevation from floor
  mesh: {
    position: Point3D;
    rotation: Point3D;
  };
}

export interface BIMRoom {
  id: string;
  name: string;
  type: string;
  area: number;
  color: string;
  points: Point[];
}

export interface CanonicalBIMFloor {
  id: string;
  name: string;
  elevation: string;
  area: number;
  walls: BIMWall[];
  columns: BIMColumn[];
  doors: BIMDoor[];
  windows: BIMWindow[];
  rooms: BIMRoom[];
}



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
