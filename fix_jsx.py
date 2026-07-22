with open('src/App.tsx', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '{bimModel ? (' in line:
        lines[i] = '              bimModel ? (\n'
    if '<div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline\'ı tamamlayın.</div>' in line:
        lines[i] = '                <div className="flex h-full items-center justify-center text-zinc-500">BIM Core Data Not Found. Lütfen Pipeline\'ı tamamlayın.</div>\n              )\n'
    # we need to remove the extra ')}' that was after the ternary if it was added incorrectly by regex
    
with open('src/App.tsx', 'w') as f:
    f.writelines(lines)
