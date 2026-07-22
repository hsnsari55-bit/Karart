import { Floor, CanonicalBIMFloor, BIMWall, BIMColumn, BIMDoor, BIMWindow, BIMRoom } from "../types";

/**
 * Converts a raw CAD Floor Plan into a structured Canonical BIM Model.
 * This completely decouples raw DXF layer checks and geometric math from the 3D Viewer.
 */
export function convertToCanonicalBIM(floor: Floor, wallHeight: number): CanonicalBIMFloor {
  const walls: BIMWall[] = [];
  const columns: BIMColumn[] = [];
  const doors: BIMDoor[] = [];
  const windows: BIMWindow[] = [];

  floor.entities.forEach((entity) => {
    const startX = entity.start.x;
    const startZ = entity.start.y;
    const endX = entity.end.x;
    const endZ = entity.end.y;

    // 1. WALL EXTRUSION
    if (entity.type === "LINE" && entity.layer === "duvar") {
      const dx = endX - startX;
      const dz = endZ - startZ;
      const length = Math.sqrt(dx * dx + dz * dz);
      const angle = Math.atan2(dz, dx);
      const thickness = entity.thickness || 15;
      const type = thickness > 20 ? "exterior" : "interior";

      walls.push({
        id: entity.id,
        type,
        axis: {
          start: { x: startX, y: startZ },
          end: { x: endX, y: endZ },
        },
        profile: {
          thickness,
          height: wallHeight,
        },
        extrusion: {
          length,
          angle,
        },
        mesh: {
          position: {
            x: startX + dx / 2,
            y: wallHeight / 2,
            z: startZ + dz / 2,
          },
          rotation: { x: 0, y: -angle, z: 0 },
          size: {
            width: length,
            height: wallHeight,
            depth: thickness,
          },
        },
      });
    }

    // 2. COLUMN GENERATION
    if (entity.type === "COLUMN" && entity.layer === "kolon") {
      const size = entity.thickness || 30;
      const height = wallHeight + 5;

      columns.push({
        id: entity.id,
        position: { x: startX, y: startZ },
        height,
        size,
        mesh: {
          position: {
            x: startX,
            y: height / 2,
            z: startZ,
          },
          size: {
            width: size,
            height,
            depth: size,
          },
        },
      });
    }

    // 3. WINDOW PLACEMENT
    if (entity.type === "WINDOW" && entity.layer === "k pencere") {
      const dx = endX - startX;
      const dz = endZ - startZ;
      const length = Math.sqrt(dx * dx + dz * dz);
      const angle = Math.atan2(dz, dx);
      const sillHeight = wallHeight * 0.3;
      const height = wallHeight * 0.4;

      windows.push({
        id: entity.id,
        width: length,
        height,
        sillHeight,
        mesh: {
          position: {
            x: startX + dx / 2,
            y: wallHeight * 0.5,
            z: startZ + dz / 2,
          },
          rotation: { x: 0, y: -angle, z: 0 },
        },
      });
    }

    // 4. DOOR PLACEMENT (Parameterizing Opening direction & Hinge placement)
    if (entity.type === "DOOR" && entity.layer === "kapı") {
      const dx = endX - startX;
      const dz = endZ - startZ;
      const length = entity.width || 80;
      const angle = Math.atan2(dz, dx);

      // Deterministic hinge side and direction parameters based on entity geometry properties
      const isLeft = (Math.round(startX + startZ) % 2) === 0;
      const hinge = isLeft ? "left" : "right";
      const openingDirection = (startX > 300) ? "inward" : "outward";
      const swingAngle = 45; // Default standard opening angle

      doors.push({
        id: entity.id,
        hinge,
        openingDirection,
        swingAngle,
        width: length,
        height: wallHeight,
        mesh: {
          position: { x: startX, y: startZ, z: 0 },
          rotation: { x: 0, y: -angle, z: 0 },
        },
      });
    }
  });

  const rooms: BIMRoom[] = floor.rooms.map((r) => ({
    id: r.id,
    name: r.name,
    type: r.type,
    area: r.area,
    color: r.color,
    points: r.points,
  }));

  return {
    id: floor.id,
    name: floor.name,
    elevation: floor.elevation,
    area: floor.area,
    walls,
    columns,
    doors,
    windows,
    rooms,
  };
}
