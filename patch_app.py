import re

with open('src/App.tsx', 'r') as f:
    content = f.read()

# Instead of passing `floor` to BIMViewer3D, we pass `bimModel`.
# We need to add state for bimModel
state_add = """
  const [selectedBlock, setSelectedBlock] = useState<"all" | "block_a" | "block_b" | "block_c">("all");
  const [bimModel, setBimModel] = useState<any>(null);
"""
content = content.replace(
    '  const [selectedBlock, setSelectedBlock] = useState<"all" | "block_a" | "block_b" | "block_c">("all");',
    state_add
)

# Set bimModel in loadRealProjectData
set_bim_logic = """
      if (data.bim && data.bim.spaces) {
        setBimModel(data.bim);
      }
"""
content = content.replace(
    '      if (isCleaned && data.bim && data.bim.length > 0) {',
    set_bim_logic + '      if (isCleaned && data.bim && data.bim.walls && data.bim.walls.length > 0) {'
)

# Now what if data.bim is NOT the array? Wait, I previously changed server to return bim_model.json to `response.bim`.
# So `data.bim` is { metadata, spaces, walls, ... }
# Then `data.bim.walls.map` should be used instead of `data.bim.map` for CADVisualizer!
# Let's fix `mappedEntities = data.bim.map` to `mappedEntities = data.bim.walls ? [...data.bim.walls, ...data.bim.windows, ...data.bim.columns, ...data.bim.doors].map`

map_logic = """
        const allBimEntities = data.bim.walls ? [...data.bim.walls, ...data.bim.windows, ...data.bim.columns, ...data.bim.doors] : data.bim;
        mappedEntities = allBimEntities.map((e: any, idx: number) => {
"""
content = content.replace(
    '        mappedEntities = data.bim.map((e: any, idx: number) => {',
    map_logic
)

# And in the viewer render:
old_viewer = """                  <BIMViewer3D 
                    floor={{ ...currentFloor, entities: isCleaned ? currentFloor.entities : mockFloors[0].entities }}
                    renderMode={renderMode}
                    wallHeight={wallHeight}
                    selectedBlock={selectedBlock}
                  />"""

new_viewer = """                  {bimModel ? (
                    <BIMViewer3D 
                      bimModel={bimModel}
                      renderMode={renderMode}
                      wallHeight={wallHeight}
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline'ı tamamlayın.</div>
                  )}"""

content = content.replace(old_viewer, new_viewer)

with open('src/App.tsx', 'w') as f:
    f.write(content)
