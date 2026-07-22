with open("backend/ifc_exporter.py", "r") as f:
    c = f.read()

c = c.replace("product=wall_ent", "products=[wall_ent]")
c = c.replace("product=col_ent", "products=[col_ent]")
c = c.replace("product=win_ent", "products=[win_ent]")
c = c.replace("product=door_ent", "products=[door_ent]")
c = c.replace("product=space_ent", "products=[space_ent]")

c = c.replace('ifc_class="IfcWall", name=f"Wall_{w.get(\'wall_id\', \'X\')}")', 'ifc_class="IfcWall", name=f"Wall_{w.get(\'wall_id\', \'X\')}")\\n                wall_ent.GlobalId = self._format_uuid(w.get("uuid"))')
c = c.replace('ifc_class="IfcColumn", name="Column")', 'ifc_class="IfcColumn", name="Column")\\n                col_ent.GlobalId = self._format_uuid(col.get("uuid"))')
c = c.replace('ifc_class="IfcWindow", name="Window")', 'ifc_class="IfcWindow", name="Window")\\n                win_ent.GlobalId = self._format_uuid(w.get("uuid"))')
c = c.replace('ifc_class="IfcDoor", name="Door")', 'ifc_class="IfcDoor", name="Door")\\n                door_ent.GlobalId = self._format_uuid(d.get("uuid"))')
c = c.replace('ifc_class="IfcSpace", name=f"Space_{s.get(\'id\', \'\')}")', 'ifc_class="IfcSpace", name=f"Space_{s.get(\'id\', \'\')}")\\n                space_ent.GlobalId = self._format_uuid(s.get("uuid"))')

with open("backend/ifc_exporter.py", "w") as f:
    f.write(c)
