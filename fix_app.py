import re

with open('src/App.tsx', 'r') as f:
    content = f.read()

# Replace the BIMViewer3D usage
pattern = r'<BIMViewer3D\s+floor=\{currentFloor\}\s+renderMode=\{renderMode\}\s+wallHeight=\{wallHeight\}\s+selectedBlock=\{selectedBlock\}\s+/>'

replacement = """{bimModel ? (
                <BIMViewer3D 
                  bimModel={bimModel}
                  renderMode={renderMode}
                  wallHeight={wallHeight}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline'ı tamamlayın.</div>
              )}"""

content = re.sub(pattern, replacement, content)

with open('src/App.tsx', 'w') as f:
    f.write(content)
