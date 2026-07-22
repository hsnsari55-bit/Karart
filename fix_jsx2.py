with open('src/App.tsx', 'r') as f:
    content = f.read()

content = content.replace(
"""            {activeTab === "bim" && (
              bimModel ? (
                <BIMViewer3D 
                  bimModel={bimModel}
                  renderMode={renderMode}
                  wallHeight={wallHeight}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline'ı tamamlayın.</div>
              )
              )}
            )}""",
"""            {activeTab === "bim" && (
              bimModel ? (
                <BIMViewer3D 
                  bimModel={bimModel}
                  renderMode={renderMode}
                  wallHeight={wallHeight}
                />
              ) : (
                <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline'ı tamamlayın.</div>
              )
            )}"""
)

with open('src/App.tsx', 'w') as f:
    f.write(content)
